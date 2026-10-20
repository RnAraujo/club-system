from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from .models import Participant
from .forms import ParticipantForm
from registrations.models import Registration


class ParticipantListView(LoginRequiredMixin, ListView):
    model = Participant
    template_name = 'participants/list.html'
    context_object_name = 'participants'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('club')
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
        from clubs.models import Club
        ctx = super().get_context_data(**kwargs)
        ctx['clubs'] = Club.objects.all()
        ctx['q'] = self.request.GET.get('q', '')
        ctx['selected_club'] = self.request.GET.get('club', '')
        return ctx


class ParticipantCreateView(LoginRequiredMixin, CreateView):
    model = Participant
    form_class = ParticipantForm
    template_name = 'participants/form.html'
    success_url = reverse_lazy('participants:list')


class ParticipantUpdateView(LoginRequiredMixin, UpdateView):
    model = Participant
    form_class = ParticipantForm
    template_name = 'participants/form.html'
    success_url = reverse_lazy('participants:list')


class ParticipantDetailView(LoginRequiredMixin, DetailView):
    model = Participant
    template_name = 'participants/detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['registrations'] = (
            Registration.objects
            .filter(participant=self.object)
            .select_related('schedule__specialty')
            .order_by('-date')
        )
        return ctx