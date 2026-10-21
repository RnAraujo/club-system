from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count
from django.contrib import messages
from registrations.models import Registration, RegistrationProcess

from .models import Participant
from .forms import ParticipantForm
from clubs.models import Club
from registrations.models import Registration



class ParticipantListView(LoginRequiredMixin, ListView):
    model = Participant
    template_name = 'participants/list.html'
    context_object_name = 'participants'
    paginate_by = 20

    def get_queryset(self):
        qs = (
            super().get_queryset()
            .select_related('club')
            .annotate(registrations_count=Count('registrations', distinct=True))
        )

        u = self.request.user
        if not u.is_admin and u.club_id:
            qs = qs.filter(club_id=u.club_id)

        q = self.request.GET.get('q')
        club = self.request.GET.get('club')
        if q:
            qs = qs.filter(
                Q(dni__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q)
            )
        if club:
            qs = qs.filter(club_id=club)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.request.user
        if u.is_admin:
            ctx['clubs'] = Club.objects.all()
        elif u.club_id:
            ctx['clubs'] = Club.objects.filter(pk=u.club_id)
        else:
            ctx['clubs'] = Club.objects.none()
        ctx['q'] = self.request.GET.get('q', '')
        ctx['selected_club'] = self.request.GET.get('club', '')
        return ctx


class ParticipantCreateView(LoginRequiredMixin, CreateView):
    model = Participant
    form_class = ParticipantForm
    template_name = 'participants/form.html'
    success_url = reverse_lazy('participants:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        u = self.request.user
        if not u.is_admin and u.club_id:
            initial['club'] = u.club_id
        else:
            club_id = self.request.GET.get('club')
            if club_id:
                initial['club'] = club_id
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_title'] = 'Nuevo participante'
        ctx['cancel_url'] = reverse_lazy('participants:list')
        return ctx

    def form_valid(self, form):
        u = self.request.user
        if not u.is_admin and u.club_id:
            form.instance.club_id = u.club_id
        messages.success(self.request, 'Participante registrado correctamente.')
        return super().form_valid(form)


class ParticipantUpdateView(LoginRequiredMixin, UpdateView):
    model = Participant
    form_class = ParticipantForm
    template_name = 'participants/form.html'
    success_url = reverse_lazy('participants:list')

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user
        if not u.is_admin:
            qs = qs.filter(club_id=u.club_id) if u.club_id else qs.none()
        return qs

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_title'] = 'Editar participante'
        ctx['cancel_url'] = reverse_lazy('participants:list')
        return ctx

    def form_valid(self, form):
        u = self.request.user
        if not u.is_admin and u.club_id:
            form.instance.club_id = u.club_id
        messages.success(self.request, 'Participante actualizado correctamente.')
        return super().form_valid(form)


class ParticipantDetailView(LoginRequiredMixin, DetailView):
    model = Participant
    template_name = 'participants/detail.html'

    def get_queryset(self):
        qs = super().get_queryset().select_related('club')
        u = self.request.user
        if not u.is_admin and u.club_id:
            qs = qs.filter(club_id=u.club_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        registrations = (
            Registration.objects
            .filter(participant=self.object)
            .select_related('schedule__specialty', 'registered_by')
            .order_by('-date', '-created_at')
        )

        ctx['registrations'] = registrations
        ctx['total_registrations'] = registrations.count()

        try:
            ctx['process'] = self.object.club.registration_process
        except RegistrationProcess.DoesNotExist:
            ctx['process'] = None

        return ctx