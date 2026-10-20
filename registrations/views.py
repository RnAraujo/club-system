from django.views.generic import ListView, CreateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.core.exceptions import ValidationError
from .models import Registration, RegistrationProcess
from .forms import RegistrationForm
from .services import close_process, reopen_process
from accounts.mixins import RegistradorRequiredMixin, AdminRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from clubs.models import Club


class RegistrationListView(LoginRequiredMixin, ListView):
    model = Registration
    template_name = 'registrations/list.html'
    context_object_name = 'registrations'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().select_related(
            'participant__club', 'schedule__specialty', 'registered_by'
        )
        u = self.request.user
        if not u.is_admin and u.club_id:
            qs = qs.filter(participant__club_id=u.club_id)
        return qs


class RegistrationCreateView(RegistradorRequiredMixin, FormView):
    template_name = 'registrations/form.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('registrations:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        try:
            form.save()
            messages.success(self.request, 'Inscripción registrada correctamente.')
            return super().form_valid(form)
        except ValidationError as e:
            form.add_error(None, e.message)
            return self.form_invalid(form)


class ProcessListView(LoginRequiredMixin, ListView):
    model = RegistrationProcess
    template_name = 'registrations/process.html'
    context_object_name = 'processes'

    def get_queryset(self):
        qs = super().get_queryset().select_related('club', 'closed_by')
        u = self.request.user
        if not u.is_admin and u.club_id:
            qs = qs.filter(club_id=u.club_id)
        return qs


def close_process_view(request, club_id):
    if not request.user.is_registrador:
        messages.error(request, 'No tiene permiso para cerrar el proceso.')
        return redirect('registrations:process')
    club = get_object_or_404(Club, pk=club_id)
    close_process(club=club, user=request.user)
    messages.success(request, f'Proceso cerrado para {club.name}.')
    return redirect('registrations:process')


def reopen_process_view(request, club_id):
    if not request.user.is_admin:
        messages.error(request, 'Solo un administrador puede reabrir el proceso.')
        return redirect('registrations:process')
    club = get_object_or_404(Club, pk=club_id)
    try:
        reopen_process(club=club, user=request.user)
        messages.success(request, f'Proceso reabierto para {club.name}.')
    except ValidationError as e:
        messages.error(request, e.message)
    return redirect('registrations:process')