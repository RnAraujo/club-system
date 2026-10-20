from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Specialty, SpecialtySchedule
from .forms import SpecialtyForm, ScheduleForm


class SpecialtyListView(LoginRequiredMixin, ListView):
    model = Specialty
    template_name = 'specialties/list.html'
    context_object_name = 'specialties'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['schedules'] = (
            SpecialtySchedule.objects
            .select_related('specialty')
            .order_by('date')
        )
        return ctx


class SpecialtyCreateView(LoginRequiredMixin, CreateView):
    model = Specialty
    form_class = SpecialtyForm
    template_name = 'specialties/form.html'
    success_url = reverse_lazy('specialties:list')


class ScheduleCreateView(LoginRequiredMixin, CreateView):
    model = SpecialtySchedule
    form_class = ScheduleForm
    template_name = 'specialties/schedule_form.html'
    success_url = reverse_lazy('specialties:list')