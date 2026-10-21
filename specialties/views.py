from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.contrib import messages
from django.utils import timezone

from accounts.mixins import AdminRequiredMixin
from .models import Specialty, SpecialtySchedule
from .forms import SpecialtyForm, ScheduleForm


# ========================= ESPECIALIDADES =========================

class SpecialtyListView(LoginRequiredMixin, ListView):
    model = Specialty
    template_name = 'specialties/list.html'
    context_object_name = 'specialties'
    paginate_by = 12

    def get_queryset(self):
        qs = (
            super().get_queryset()
            .annotate(
                schedules_count=Count('schedules', distinct=True),
                total_registered=Count('schedules__registrations', distinct=True),
            )
        )
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(name__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()

        schedules = (
            SpecialtySchedule.objects
            .select_related('specialty')
            .annotate(registered=Count('registrations', distinct=True))
            .order_by('date', 'specialty__name')
        )

        specialty_id = self.request.GET.get('specialty')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        only_future = self.request.GET.get('only_future', '1')

        if specialty_id:
            schedules = schedules.filter(specialty_id=specialty_id)
        if date_from:
            schedules = schedules.filter(date__gte=date_from)
        if date_to:
            schedules = schedules.filter(date__lte=date_to)
        if only_future == '1' and not date_from:
            schedules = schedules.filter(date__gte=today)

        ctx.update({
            'schedules': schedules,
            'specialties_all': Specialty.objects.all(),
            'today': today,
            'selected_specialty': specialty_id or '',
            'date_from': date_from or '',
            'date_to': date_to or '',
            'only_future': only_future,
            'q': self.request.GET.get('q', ''),
        })
        return ctx


class SpecialtyCreateView(AdminRequiredMixin, CreateView):
    model = Specialty
    form_class = SpecialtyForm
    template_name = 'specialties/form.html'
    success_url = reverse_lazy('specialties:list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_title'] = 'Nueva especialidad'
        ctx['cancel_url'] = reverse_lazy('specialties:list')
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Especialidad creada correctamente.')
        return super().form_valid(form)


class SpecialtyUpdateView(AdminRequiredMixin, UpdateView):
    model = Specialty
    form_class = SpecialtyForm
    template_name = 'specialties/form.html'
    success_url = reverse_lazy('specialties:list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_title'] = 'Editar especialidad'
        ctx['cancel_url'] = reverse_lazy('specialties:list')
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Especialidad actualizada correctamente.')
        return super().form_valid(form)


class SpecialtyDeleteView(AdminRequiredMixin, DeleteView):
    model = Specialty
    template_name = 'specialties/confirm_delete.html'
    success_url = reverse_lazy('specialties:list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Eliminar especialidad'
        ctx['cancel_url'] = reverse_lazy('specialties:list')
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Especialidad eliminada.')
        return super().form_valid(form)


# ========================= PROGRAMACIONES =========================

class ScheduleCreateView(AdminRequiredMixin, CreateView):
    model = SpecialtySchedule
    form_class = ScheduleForm
    template_name = 'specialties/schedule_form.html'
    success_url = reverse_lazy('specialties:list')

    def get_initial(self):
        initial = super().get_initial()
        specialty_id = self.request.GET.get('specialty')
        if specialty_id:
            initial['specialty'] = specialty_id
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_title'] = 'Nueva programación'
        ctx['cancel_url'] = reverse_lazy('specialties:list')
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Programación creada correctamente.')
        return super().form_valid(form)


class ScheduleUpdateView(AdminRequiredMixin, UpdateView):
    model = SpecialtySchedule
    form_class = ScheduleForm
    template_name = 'specialties/schedule_form.html'
    success_url = reverse_lazy('specialties:list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_title'] = 'Editar programación'
        ctx['cancel_url'] = reverse_lazy('specialties:list')
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Programación actualizada correctamente.')
        return super().form_valid(form)


class ScheduleDeleteView(AdminRequiredMixin, DeleteView):
    model = SpecialtySchedule
    template_name = 'specialties/confirm_delete.html'
    success_url = reverse_lazy('specialties:list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Eliminar programación'
        ctx['cancel_url'] = reverse_lazy('specialties:list')
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Programación eliminada.')
        return super().form_valid(form)