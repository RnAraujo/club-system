import csv
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import redirect
from django.contrib import messages
from clubs.models import Club
from specialties.models import Specialty, SpecialtySchedule
from registrations.models import Registration
from accounts.mixins import AdminRequiredMixin


# ========== Dashboard ==========
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.request.user
        regs = Registration.objects.all()
        if not u.is_admin and u.club_id:
            regs = regs.filter(participant__club_id=u.club_id)

        ctx.update({
            'total_clubs': Club.objects.count(),
            'total_participants': (
                sum(c.participants.count() for c in Club.objects.all())
                if u.is_admin else
                (u.club.participants.count() if u.club else 0)
            ),
            'total_registrations': regs.count(),
            'total_specialties': Specialty.objects.count(),
            'recent_registrations': regs.select_related(
                'participant', 'schedule__specialty'
            ).order_by('-created_at')[:5],
        })
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