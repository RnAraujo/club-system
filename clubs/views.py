from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Club, Directive
from .forms import ClubForm, DirectiveForm


class ClubListView(LoginRequiredMixin, ListView):
    model = Club
    template_name = 'clubs/list.html'
    context_object_name = 'clubs'
    paginate_by = 12


class ClubCreateView(LoginRequiredMixin, CreateView):
    model = Club
    form_class = ClubForm
    template_name = 'clubs/form.html'
    success_url = reverse_lazy('clubs:list')


class ClubUpdateView(LoginRequiredMixin, UpdateView):
    model = Club
    form_class = ClubForm
    template_name = 'clubs/form.html'
    success_url = reverse_lazy('clubs:list')


class ClubDetailView(LoginRequiredMixin, DetailView):
    model = Club
    template_name = 'clubs/detail.html'


class DirectiveListView(LoginRequiredMixin, ListView):
    model = Directive
    template_name = 'clubs/directive_list.html'
    context_object_name = 'directives'

    def get_queryset(self):
        qs = super().get_queryset().select_related('club')
        club_id = self.request.GET.get('club')
        if club_id:
            qs = qs.filter(club_id=club_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['clubs'] = Club.objects.all()
        ctx['selected_club'] = self.request.GET.get('club', '')
        return ctx


class DirectiveCreateView(LoginRequiredMixin, CreateView):
    model = Directive
    form_class = DirectiveForm
    template_name = 'clubs/form.html'
    success_url = reverse_lazy('clubs:directive_list')