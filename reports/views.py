import csv
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import redirect
from django.utils import timezone

from clubs.models import Club
from participants.models import Participant
from specialties.models import Specialty, SpecialtySchedule
from registrations.models import Registration, RegistrationProcess


# ============================================================
# Helpers
# ============================================================

def _base_registration_qs(user):
    """Inscripciones con scoping por rol."""
    qs = Registration.objects.select_related(
        'participant__club', 'schedule__specialty', 'registered_by',
    )
    if not user.is_admin:
        if user.club_id:
            qs = qs.filter(participant__club_id=user.club_id)
        else:
            qs = qs.none()
    return qs


def _apply_common_filters(qs, request, include_club=True):
    specialty_id = request.GET.get('specialty')
    if specialty_id:
        qs = qs.filter(schedule__specialty_id=specialty_id)

    if include_club and request.user.is_admin:
        club_id = request.GET.get('club')
        if club_id:
            qs = qs.filter(participant__club_id=club_id)

    date_from = request.GET.get('date_from')
    if date_from:
        qs = qs.filter(date__gte=date_from)

    date_to = request.GET.get('date_to')
    if date_to:
        qs = qs.filter(date__lte=date_to)

    q = request.GET.get('q')
    if q:
        qs = qs.filter(
            Q(participant__dni__icontains=q) |
            Q(participant__first_name__icontains=q) |
            Q(participant__last_name__icontains=q)
        )

    return qs


def _csv_response(filename, headers, rows):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(headers)
    for r in rows:
        writer.writerow(r)
    return response


# ============================================================
# Dashboard
# ============================================================

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.request.user
        today = timezone.localdate()

        clubs_qs = Club.objects.all()
        participants_qs = Participant.objects.all()
        registrations_qs = Registration.objects.all()

        if not u.is_admin and u.club_id:
            clubs_qs = clubs_qs.filter(pk=u.club_id)
            participants_qs = participants_qs.filter(club_id=u.club_id)
            registrations_qs = registrations_qs.filter(participant__club_id=u.club_id)

        ctx['total_clubs'] = clubs_qs.count()
        ctx['total_participants'] = participants_qs.count()
        ctx['total_registrations'] = registrations_qs.count()
        ctx['total_specialties'] = Specialty.objects.count()
        ctx['today_registrations'] = registrations_qs.filter(date=today).count()
        ctx['today'] = today
        ctx['upcoming_schedules'] = (
            SpecialtySchedule.objects
            .select_related('specialty')
            .filter(date__gte=today)
            .order_by('date')[:5]
        )
        ctx['recent_registrations'] = (
            registrations_qs
            .select_related('participant__club', 'schedule__specialty', 'registered_by')
            .order_by('-created_at')[:8]
        )
        if u.is_admin:
            ctx['processes'] = (
                RegistrationProcess.objects
                .select_related('club', 'closed_by')
                .order_by('club__name')
            )
        elif u.club_id:
            try:
                ctx['current_process'] = RegistrationProcess.objects.get(club_id=u.club_id)
            except RegistrationProcess.DoesNotExist:
                ctx['current_process'] = None
        return ctx


# ============================================================
# Índice de reportes
# ============================================================

class ReportsIndexView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.request.user

        qs = _base_registration_qs(u)
        ctx['total_registrations'] = qs.count()
        ctx['total_specialties'] = Specialty.objects.count()

        if u.is_admin:
            ctx['total_clubs'] = Club.objects.count()
            ctx['total_participants'] = Participant.objects.count()
        else:
            ctx['total_clubs'] = 1 if u.club_id else 0
            ctx['total_participants'] = (
                Participant.objects.filter(club_id=u.club_id).count() if u.club_id else 0
            )
        return ctx


# ============================================================
# Reporte 1 — Por especialidad y club
# ============================================================

class ReportBySpecialtyAndClubView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/by_specialty_club.html'

    def get_qs(self):
        qs = _base_registration_qs(self.request.user)
        return _apply_common_filters(qs, self.request)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.get_qs()
        u = self.request.user

        rows = (
            qs.values(
                'schedule__specialty__name',
                'schedule__specialty__id',
                'participant__club__name',
                'participant__club__id',
            )
            .annotate(total=Count('id'))
            .order_by('schedule__specialty__name', 'participant__club__name')
        )

        totals_by_specialty = (
            qs.values(
                'schedule__specialty__name',
                'schedule__specialty__id',
            )
            .annotate(total=Count('id'))
            .order_by('-total', 'schedule__specialty__name')
        )

        ctx.update({
            'rows': rows,
            'totals_by_specialty': totals_by_specialty,
            'total_registrations': qs.count(),
            'total_specialties': qs.values('schedule__specialty').distinct().count(),
            'total_clubs': qs.values('participant__club').distinct().count(),
            'specialties': Specialty.objects.all(),
            'selected_specialty': self.request.GET.get('specialty', ''),
            'selected_club': self.request.GET.get('club', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
        })

        if u.is_admin:
            ctx['clubs'] = Club.objects.all()
        elif u.club_id:
            ctx['clubs'] = Club.objects.filter(pk=u.club_id)
        else:
            ctx['clubs'] = Club.objects.none()
        return ctx


# ============================================================
# Reporte 2 — Total por especialidad + listado de niños inscritos
# ============================================================

class ReportBySpecialtyView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/by_specialty.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.request.user

        # Inscripciones con scoping por rol
        regs = _base_registration_qs(u)

        # --- Resumen por especialidad ---
        rows = list(
            Specialty.objects
            .annotate(
                total_registered_global=Count('schedules__registrations', distinct=True),
                total_schedules=Count('schedules', distinct=True),
            )
            .order_by('-total_registered_global', 'name')
        )

        for row in rows:
            # Si no es admin, recalcular con el queryset scoped
            if u.is_admin:
                row.total_registered = row.total_registered_global
            else:
                row.total_registered = regs.filter(schedule__specialty=row).count()

            schedules = SpecialtySchedule.objects.filter(specialty=row)
            row.total_available = sum(s.available_slots for s in schedules)
            row.total_capacity = row.max_participants * row.total_schedules
            row.occupancy_pct = (
                round((row.total_registered / row.total_capacity) * 100)
                if row.total_capacity else 0
            )

        # --- Detalle por programación ---
        schedules = (
            SpecialtySchedule.objects
            .select_related('specialty')
            .annotate(registered=Count('registrations', distinct=True))
            .order_by('date', 'specialty__name')
        )

        # --- Listado de niños inscritos (filtrable) ---
        enrolled = regs.order_by(
            'schedule__specialty__name',
            'schedule__date',
            'participant__last_name',
            'participant__first_name',
        )
        enrolled = _apply_common_filters(enrolled, self.request, include_club=False)

        specialty_id = self.request.GET.get('specialty')

        ctx.update({
            'rows': rows,
            'schedules': schedules,
            'enrolled': enrolled,
            'enrolled_count': enrolled.count(),
            'specialties': Specialty.objects.all(),
            'selected_specialty': specialty_id or '',
            'selected_specialty_obj': (
                Specialty.objects.filter(pk=specialty_id).first()
                if specialty_id else None
            ),
            'q': self.request.GET.get('q', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
            'total_registrations': regs.count(),
            'total_schedules': SpecialtySchedule.objects.count(),
            'total_specialties': Specialty.objects.count(),
        })
        return ctx


# ============================================================
# Reporte 3 — Inscripciones por día
# ============================================================

class ReportByDayView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/by_day.html'

    def get_qs(self):
        qs = _base_registration_qs(self.request.user)
        date_from = self.request.GET.get('date_from')
        if date_from:
            qs = qs.filter(date__gte=date_from)
        date_to = self.request.GET.get('date_to')
        if date_to:
            qs = qs.filter(date__lte=date_to)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.get_qs()

        rows = list(
            qs.values('date')
            .annotate(total=Count('id'))
            .order_by('-date')
        )

        for r in rows:
            r['specialties'] = list(
                qs.filter(date=r['date'])
                .values('schedule__specialty__name')
                .annotate(count=Count('id'))
                .order_by('-count')
            )

        max_day = max((r['total'] for r in rows), default=1)
        for r in rows:
            r['pct'] = round((r['total'] / max_day) * 100) if max_day else 0

        ctx.update({
            'rows': rows,
            'total_registrations': qs.count(),
            'total_days': len(rows),
            'max_day': max_day,
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
            'today': timezone.localdate(),
        })
        return ctx


# ============================================================
# Exportaciones CSV
# ============================================================

def export_by_specialty_club_csv(request):
    if not request.user.is_authenticated:
        return redirect('accounts:login')

    qs = _base_registration_qs(request.user)
    qs = _apply_common_filters(qs, request)

    rows = qs.values_list(
        'schedule__specialty__name',
        'participant__club__name',
        'participant__dni',
        'participant__last_name',
        'participant__first_name',
        'date',
    ).order_by('schedule__specialty__name', 'participant__club__name', 'date')

    return _csv_response(
        'inscripciones_por_especialidad_club.csv',
        ['Especialidad', 'Club', 'DNI', 'Apellidos', 'Nombres', 'Fecha'],
        rows,
    )


def export_by_specialty_csv(request):
    """Resumen agregado por especialidad, con scoping por rol."""
    if not request.user.is_authenticated:
        return redirect('accounts:login')

    u = request.user
    regs = _base_registration_qs(u)

    rows = []
    for s in Specialty.objects.annotate(
        total_schedules=Count('schedules', distinct=True),
    ).order_by('name'):
        total_registered = regs.filter(schedule__specialty=s).count()
        total_capacity = s.max_participants * s.total_schedules
        rows.append([
            s.name,
            s.max_participants,
            s.total_schedules,
            total_registered,
            total_capacity,
            total_capacity - total_registered,
        ])

    return _csv_response(
        'inscripciones_por_especialidad.csv',
        ['Especialidad', 'Cupo por programación', 'Programaciones',
         'Total inscritos', 'Capacidad total', 'Cupos disponibles'],
        rows,
    )


def export_enrolled_csv(request):
    """Listado de niños inscritos, filtrable, con scoping por rol."""
    if not request.user.is_authenticated:
        return redirect('accounts:login')

    qs = _base_registration_qs(request.user)
    qs = _apply_common_filters(qs, request, include_club=False)
    qs = qs.order_by(
        'schedule__specialty__name',
        'schedule__date',
        'participant__last_name',
    )

    rows = qs.values_list(
        'schedule__specialty__name',
        'schedule__date',
        'participant__last_name',
        'participant__first_name',
        'participant__dni',
        'participant__club__name',
        'registered_by__username',
    )

    return _csv_response(
        'ninos_inscritos.csv',
        ['Especialidad', 'Fecha', 'Apellidos', 'Nombres', 'DNI', 'Club', 'Registrado por'],
        rows,
    )


def export_by_day_csv(request):
    if not request.user.is_authenticated:
        return redirect('accounts:login')

    qs = _base_registration_qs(request.user)
    date_from = request.GET.get('date_from')
    if date_from:
        qs = qs.filter(date__gte=date_from)
    date_to = request.GET.get('date_to')
    if date_to:
        qs = qs.filter(date__lte=date_to)

    rows = qs.values('date').annotate(total=Count('id')).order_by('-date')
    return _csv_response(
        'inscripciones_por_dia.csv',
        ['Fecha', 'Total inscripciones'],
        [(r['date'], r['total']) for r in rows],
    )