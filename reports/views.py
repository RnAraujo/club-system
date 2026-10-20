import csv
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import redirect
from django.utils import timezone

from accounts.mixins import AdminRequiredMixin
from clubs.models import Club
from participants.models import Participant
from specialties.models import Specialty, SpecialtySchedule
from registrations.models import Registration


# ============================================================
# Helpers
# ============================================================

def _base_registration_qs(user):
    """Queryset base de inscripciones aplicando restricción por rol."""
    qs = Registration.objects.select_related(
        'participant__club', 'schedule__specialty'
    )
    if not user.is_admin and user.club_id:
        qs = qs.filter(participant__club_id=user.club_id)
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

    return qs


def _csv_response(filename, headers, rows):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write('\ufeff')  # BOM para abrir correctamente en Excel
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
            from registrations.models import RegistrationProcess
            ctx['processes'] = (
                RegistrationProcess.objects
                .select_related('club', 'closed_by')
                .order_by('club__name')
            )
        elif u.club_id:
            from registrations.models import RegistrationProcess
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
# Reporte 1 — Por especialidad y club (registrador)
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

        # Filas (especialidad x club)
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

        # Totales por especialidad
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
# Reporte 2 — Total por especialidad (admin)
# ============================================================

class ReportBySpecialtyView(AdminRequiredMixin, TemplateView):
    template_name = 'reports/by_specialty.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        rows = list(
            Specialty.objects
            .annotate(
                total_registered=Count('schedules__registrations', distinct=True),
                total_schedules=Count('schedules', distinct=True),
            )
            .order_by('-total_registered', 'name')
        )

        # Cupos disponibles agregados + % de ocupación
        for row in rows:
            schedules = SpecialtySchedule.objects.filter(specialty=row)
            total_slots = sum(s.available_slots for s in schedules)
            total_capacity = row.max_participants * row.total_schedules
            row.total_available = total_slots
            row.total_capacity = total_capacity
            if total_capacity > 0:
                row.occupancy_pct = round((row.total_registered / total_capacity) * 100)
            else:
                row.occupancy_pct = 0

        schedules = (
            SpecialtySchedule.objects
            .select_related('specialty')
            .annotate(registered=Count('registrations', distinct=True))
            .order_by('date', 'specialty__name')
        )

        ctx.update({
            'rows': rows,
            'schedules': schedules,
            'total_registrations': Registration.objects.count(),
            'total_schedules': SpecialtySchedule.objects.count(),
            'total_specialties': Specialty.objects.count(),
        })
        return ctx


# ============================================================
# Reporte 3 — Inscripciones por día (admin)
# ============================================================

class ReportByDayView(AdminRequiredMixin, TemplateView):
    template_name = 'reports/by_day.html'

    def get_qs(self):
        qs = Registration.objects.all()
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

        # Desglose por especialidad para cada día
        for r in rows:
            r['specialties'] = list(
                qs.filter(date=r['date'])
                .values('schedule__specialty__name')
                .annotate(count=Count('id'))
                .order_by('-count')
            )

        max_day = max((r['total'] for r in rows), default=1)

        # Para la barra: % relativo respecto al día con más inscripciones
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
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    if not request.user.is_admin:
        return redirect('reports:index')

    rows = []
    for s in Specialty.objects.annotate(
        total_registered=Count('schedules__registrations', distinct=True),
        total_schedules=Count('schedules', distinct=True),
    ).order_by('name'):
        total_capacity = s.max_participants * s.total_schedules
        rows.append([
            s.name,
            s.max_participants,
            s.total_schedules,
            s.total_registered,
            total_capacity,
            total_capacity - s.total_registered,
        ])

    return _csv_response(
        'inscripciones_por_especialidad.csv',
        ['Especialidad', 'Cupo por programación', 'Programaciones',
         'Total inscritos', 'Capacidad total', 'Cupos disponibles'],
        rows,
    )


def export_by_day_csv(request):
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    if not request.user.is_admin:
        return redirect('reports:index')

    qs = Registration.objects.all()
    date_from = request.GET.get('date_from')
    if date_from:
        qs = qs.filter(date__gte=date_from)
    date_to = request.GET.get('date_to')
    if date_to:
        qs = qs.filter(date__lte=date_to)

    rows = qs.values_list('date').annotate(total=Count('id')).order_by('-date')
    return _csv_response(
        'inscripciones_por_dia.csv',
        ['Fecha', 'Total inscripciones'],
        [(r['date'], r['total']) for r in rows],
    )