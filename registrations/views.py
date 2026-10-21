from django.views.generic import ListView, FormView
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone

from accounts.mixins import RegistradorRequiredMixin, AdminRequiredMixin
from clubs.models import Club
from participants.models import Participant

from .models import Registration, RegistrationProcess
from .forms import RegistrationForm
from .services import close_process, reopen_process


# ========================== LISTADO ==========================

class RegistrationListView(LoginRequiredMixin, ListView):
    model = Registration
    template_name = 'registrations/list.html'
    context_object_name = 'registrations'
    paginate_by = 25

    def get_queryset(self):
        qs = (
            Registration.objects
            .select_related(
                'participant__club',
                'schedule__specialty',
                'registered_by',
            )
            .order_by('-date', '-created_at')
        )

        u = self.request.user
        if not u.is_admin and u.club_id:
            qs = qs.filter(participant__club_id=u.club_id)

        # Filtros
        q = self.request.GET.get('q')
        if q:
            from django.db.models import Q
            qs = qs.filter(
                Q(participant__dni__icontains=q) |
                Q(participant__first_name__icontains=q) |
                Q(participant__last_name__icontains=q)
            )

        specialty = self.request.GET.get('specialty')
        if specialty:
            qs = qs.filter(schedule__specialty_id=specialty)

        club = self.request.GET.get('club')
        if club and u.is_admin:
            qs = qs.filter(participant__club_id=club)

        date_from = self.request.GET.get('date_from')
        if date_from:
            qs = qs.filter(date__gte=date_from)

        date_to = self.request.GET.get('date_to')
        if date_to:
            qs = qs.filter(date__lte=date_to)

        return qs

    def get_context_data(self, **kwargs):
        from specialties.models import Specialty
        ctx = super().get_context_data(**kwargs)
        u = self.request.user
        today = timezone.localdate()

        # Métricas sobre el queryset filtrado
        base_qs = self.get_queryset()
        ctx['total_filtered'] = base_qs.count()
        ctx['today_count'] = base_qs.filter(date=today).count()

        # Filtros disponibles
        ctx['specialties'] = Specialty.objects.all()
        if u.is_admin:
            ctx['clubs'] = Club.objects.all()
        elif u.club_id:
            ctx['clubs'] = Club.objects.filter(pk=u.club_id)
        else:
            ctx['clubs'] = Club.objects.none()

        ctx['q'] = self.request.GET.get('q', '')
        ctx['selected_specialty'] = self.request.GET.get('specialty', '')
        ctx['selected_club'] = self.request.GET.get('club', '')
        ctx['date_from'] = self.request.GET.get('date_from', '')
        ctx['date_to'] = self.request.GET.get('date_to', '')
        ctx['today'] = today
        return ctx


# ========================== CREAR INSCRIPCIÓN ==========================

class RegistrationCreateView(RegistradorRequiredMixin, FormView):
    template_name = 'registrations/form.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('registrations:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        participant_id = self.request.GET.get('participant')
        if participant_id:
            initial['participant'] = participant_id
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.request.user

        # Participante pre-seleccionado desde query string
        participant_id = self.request.GET.get('participant')
        if participant_id:
            try:
                ctx['preselected_participant'] = (
                    Participant.objects
                    .select_related('club')
                    .get(pk=participant_id)
                )
            except Participant.DoesNotExist:
                pass

        # Estado del proceso del club del usuario (aviso previo)
        if u.club_id:
            try:
                ctx['process'] = RegistrationProcess.objects.get(club_id=u.club_id)
            except RegistrationProcess.DoesNotExist:
                ctx['process'] = None
        return ctx

    def form_valid(self, form):
        try:
            form.save()
            messages.success(self.request, 'Inscripción registrada correctamente.')
            return super().form_valid(form)
        except ValidationError as e:
            errors = getattr(e, 'messages', [str(e)])
            for msg in errors:
                form.add_error(None, msg)
            return self.form_invalid(form)


# ========================== PROCESOS ==========================

class ProcessListView(RegistradorRequiredMixin, ListView):
    model = RegistrationProcess
    template_name = 'registrations/process.html'
    context_object_name = 'processes'

    def get_queryset(self):
        u = self.request.user

        # Asegurar que exista un proceso por cada club visible
        clubs = Club.objects.all()
        if not u.is_admin and u.club_id:
            clubs = clubs.filter(pk=u.club_id)
        for club in clubs:
            RegistrationProcess.objects.get_or_create(club=club)

        qs = (
            RegistrationProcess.objects
            .select_related('club', 'closed_by')
            .order_by('club__name')
        )
        if not u.is_admin and u.club_id:
            qs = qs.filter(club_id=u.club_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.request.user
        ctx['open_count'] = self.get_queryset().filter(is_open=True).count()
        ctx['closed_count'] = self.get_queryset().filter(is_open=False).count()
        return ctx


@require_POST
def close_process_view(request, club_id):
    if not request.user.is_registrador:
        messages.error(request, 'No tiene permiso para cerrar el proceso.')
        return redirect('registrations:process')

    club = get_object_or_404(Club, pk=club_id)

    # Un registrador solo puede cerrar el proceso de su propio club
    if not request.user.is_admin and request.user.club_id != club.pk:
        messages.error(request, 'No puede cerrar el proceso de otro club.')
        return redirect('registrations:process')

    close_process(club=club, user=request.user)
    messages.success(request, f'Proceso cerrado para {club.name}.')
    return redirect('registrations:process')


@require_POST
def reopen_process_view(request, club_id):
    if not request.user.is_admin:
        messages.error(request, 'Solo un administrador puede reabrir el proceso.')
        return redirect('registrations:process')

    club = get_object_or_404(Club, pk=club_id)
    try:
        reopen_process(club=club, user=request.user)
        messages.success(request, f'Proceso reabierto para {club.name}.')
    except ValidationError as e:
        messages.error(request, e.messages[0] if e.messages else str(e))
    return redirect('registrations:process')