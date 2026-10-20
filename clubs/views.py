from django.urls import reverse_lazy
from django.views.generic import (
    ListView, CreateView, UpdateView, DetailView, DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.contrib import messages

from .models import Club, Directive
from .forms import ClubForm, DirectiveForm


# ============ CLUB ============

class ClubListView(LoginRequiredMixin, ListView):
    model = Club
    template_name = 'clubs/list.html'
    context_object_name = 'clubs'
    paginate_by = 12

    def get_queryset(self):
        qs = super().get_queryset().annotate(
            participants_count=Count('participants', distinct=True),
            directives_count=Count('directives', distinct=True),
        )
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(zone__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


class ClubCreateView(LoginRequiredMixin, CreateView):
    model = Club
    form_class = ClubForm
    template_name = 'clubs/form.html'
    success_url = reverse_lazy('clubs:list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_title'] = 'Nuevo club'
        ctx['cancel_url'] = reverse_lazy('clubs:list')
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Club creado correctamente.')
        return super().form_valid(form)


class ClubUpdateView(LoginRequiredMixin, UpdateView):
    model = Club
    form_class = ClubForm
    template_name = 'clubs/form.html'
    success_url = reverse_lazy('clubs:list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_title'] = 'Editar club'
        ctx['cancel_url'] = reverse_lazy('clubs:list')
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Club actualizado correctamente.')
        return super().form_valid(form)


class ClubDetailView(LoginRequiredMixin, DetailView):
    model = Club
    template_name = 'clubs/detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['directives'] = self.object.directives.order_by('position')
        ctx['participants'] = self.object.participants.order_by('last_name')[:10]
        ctx['participants_total'] = self.object.participants.count()
        ctx['registrations_total'] = (
            self.object.participants
            .values('registrations')
            .count()
        )
        return ctx


# ============ DIRECTIVA ============

class DirectiveListView(LoginRequiredMixin, ListView):
    model = Directive
    template_name = 'clubs/directive_list.html'
    context_object_name = 'directives'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().select_related('club')
        club_id = self.request.GET.get('club')
        q = self.request.GET.get('q')
        if club_id:
            qs = qs.filter(club_id=club_id)
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(dni__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['clubs'] = Club.objects.all()
        ctx['selected_club'] = self.request.GET.get('club', '')
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


class DirectiveCreateView(LoginRequiredMixin, CreateView):
    model = Directive
    form_class = DirectiveForm
    template_name = 'clubs/form.html'
    success_url = reverse_lazy('clubs:directive_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_title'] = 'Nuevo directivo'
        ctx['cancel_url'] = reverse_lazy('clubs:directive_list')
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Directivo registrado correctamente.')
        return super().form_valid(form)


class DirectiveUpdateView(LoginRequiredMixin, UpdateView):
    model = Directive
    form_class = DirectiveForm
    template_name = 'clubs/form.html'
    success_url = reverse_lazy('clubs:directive_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_title'] = 'Editar directivo'
        ctx['cancel_url'] = reverse_lazy('clubs:directive_list')
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Directivo actualizado correctamente.')
        return super().form_valid(form)


class DirectiveDeleteView(LoginRequiredMixin, DeleteView):
    model = Directive
    template_name = 'clubs/confirm_delete.html'
    success_url = reverse_lazy('clubs:directive_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Eliminar directivo'
        ctx['cancel_url'] = reverse_lazy('clubs:directive_list')
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Directivo eliminado.')
        return super().form_valid(form)