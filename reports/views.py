import csv
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import redirect
from django.contrib import messages
from clubs.models import Club
from specialties.models import Specialty, SpecialtySchedule
from participants.models import Participant
from registrations.models import RegistrationProcess
from django.utils import timezone
from registrations.models import Registration
from accounts.mixins import AdminRequiredMixin


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.request.user
        today = timezone.localdate()

        # ---- Base querysets según rol ----
        clubs_qs = Club.objects.all()
        participants_qs = Participant.objects.all()
        registrations_qs = Registration.objects.all()

        if not u.is_admin and u.club_id:
            clubs_qs = clubs_qs.filter(pk=u.club_id)
            participants_qs = participants_qs.filter(club_id=u.club_id)
            registrations_qs = registrations_qs.filter(participant__club_id=u.club_id)

        # ---- Métricas principales ----
        ctx['total_clubs'] = clubs_qs.count()
        ctx['total_participants'] = participants_qs.count()
        ctx['total_registrations'] = registrations_qs.count()
        ctx['total_specialties'] = Specialty.objects.count()

        # ---- Métricas secundarias ----
        ctx['today_registrations'] = registrations_qs.filter(date=today).count()
        ctx['today'] = today
        ctx['upcoming_schedules'] = (
            SpecialtySchedule.objects
            .select_related('specialty')
            .filter(date__gte=today)
            .order_by('date')[:5]
        )

        # ---- Inscripciones recientes ----
        ctx['recent_registrations'] = (
            registrations_qs
            .select_related('participant__club', 'schedule__specialty', 'registered_by')
            .order_by('-created_at')[:8]
        )

        # ---- Estado del proceso de inscripción ----
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


# ========== Reporte 1: Inscritos por especialidad y club (registrador) ==========
class ReportBySpecialtyAndClubView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/by_specialty_club.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.request.user
        qs = Registration.objects.select_related('participant__club', 'schedule__specialty')

        if not u.is_admin and u.club_id:
            qs = qs.filter(participant__club_id=u.club_id)

        # Filtro por especialidad
        specialty_id = self.request.GET.get('specialty')
        if specialty_id:
            qs = qs.filter(schedule__specialty_id=specialty_id)

        rows = (
            qs.values(
                'participant__club__name',
                'schedule__specialty__name',
            )
            .annotate(total=Count('id'))
            .order_by('schedule__specialty__name', 'participant__club__name')
        )

        ctx.update({
            'rows': rows,
            'specialties': Specialty.objects.all(),
            'selected_specialty': specialty_id or '',
        })
        return ctx


# ========== Reporte 2: Inscritos por especialidad (admin) ==========
class ReportBySpecialtyView(AdminRequiredMixin, TemplateView):
    template_name = 'reports/by_specialty.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        rows = (
            Specialty.objects
            .annotate(
                total_registered=Count('schedules__registrations'),
                total_slots=Count('schedules__available_slots'),
            )
            .order_by('name')
        )
        # Detalle por programación
        schedules = (
            SpecialtySchedule.objects
            .select_related('specialty')
            .annotate(registered=Count('registrations'))
            .order_by('date', 'specialty__name')
        )
        ctx.update({'rows': rows, 'schedules': schedules})
        return ctx


# ========== Reporte 3: Inscripciones por día ==========
class ReportByDayView(AdminRequiredMixin, TemplateView):
    template_name = 'reports/by_day.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        rows = (
            Registration.objects
            .values('date')
            .annotate(total=Count('id'))
            .order_by('-date')
        )
        ctx['rows'] = rows
        return ctx


# ========== Exportaciones CSV ==========

def _csv_response(filename, headers, rows):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(headers)
    for r in rows:
        writer.writerow(r)
    return response


def export_by_specialty_club_csv(request):
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    u = request.user
    qs = Registration.objects.select_related('participant__club', 'schedule__specialty')
    if not u.is_admin and u.club_id:
        qs = qs.filter(participant__club_id=u.club_id)
    specialty_id = request.GET.get('specialty')
    if specialty_id:
        qs = qs.filter(schedule__specialty_id=specialty_id)

    rows = qs.values_list(
        'schedule__specialty__name',
        'participant__club__name',
        'participant__dni',
        'participant__last_name',
        'participant__first_name',
        'date',
    ).order_by('schedule__specialty__name', 'participant__club__name')

    return _csv_response(
        'inscripciones_por_especialidad_club.csv',
        ['Especialidad', 'Club', 'DNI', 'Apellidos', 'Nombres', 'Fecha'],
        rows,
    )