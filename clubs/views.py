from django.urls import reverse_lazy
from django.views.generic import (
    ListView, CreateView, UpdateView, DetailView, DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.contrib import messages
from django.shortcuts import redirect

from accounts.mixins import AdminRequiredMixin, RegistradorRequiredMixin
from .models import Club, Directive, MissionaryDistrict
from .forms import ClubForm, DirectiveForm, MissionaryDistrictForm


# ================= CLUB =================

class ClubListView(LoginRequiredMixin, ListView):
    model = Club
    template_name = 'clubs/list.html'
    context_object_name = 'clubs'
    paginate_by = 12

    def get_queryset(self):
        qs = (
            super().get_queryset()
            .select_related('district')
            .annotate(
                participants_count=Count('participants', distinct=True),
                directives_count=Count('directives', distinct=True),
            )
        )

        if not self.request.user.is_admin:
            if self.request.user.club_id:
                qs = qs.filter(pk=self.request.user.club_id)
            else:
                qs = qs.none()

        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(district__name__icontains=q))

        district = self.request.GET.get('district')
        if district:
            qs = qs.filter(district_id=district)

        zone = self.request.GET.get('zone')
        if zone:
            qs = qs.filter(zone=zone)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        base = super().get_queryset() if self.request.user.is_admin else self.get_queryset()
        ctx['districts'] = MissionaryDistrict.objects.order_by('name')
        ctx['zones'] = (
            base.values_list('zone', flat=True).distinct().order_by('zone')
        )
        ctx['q'] = self.request.GET.get('q', '')
        ctx['selected_district'] = self.request.GET.get('district', '')
        ctx['selected_zone'] = self.request.GET.get('zone', '')
        return ctx


class ClubCreateView(AdminRequiredMixin, CreateView):
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


class ClubUpdateView(AdminRequiredMixin, UpdateView):
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

    def get_queryset(self):
        qs = super().get_queryset().select_related('district')
        u = self.request.user
        if not u.is_admin:
            if u.club_id:
                qs = qs.filter(pk=u.club_id)
            else:
                qs = qs.none()
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['directives'] = self.object.directives.order_by('position')
        ctx['participants'] = self.object.participants.order_by('last_name')[:10]
        ctx['participants_total'] = self.object.participants.count()
        ctx['registrations_total'] = (
            self.object.participants.values('registrations').count()
        )
        return ctx


# ================= DIRECTIVA =================

class DirectiveListView(LoginRequiredMixin, ListView):
    model = Directive
    template_name = 'clubs/directive_list.html'
    context_object_name = 'directives'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().select_related('club__district')
        u = self.request.user

        if not u.is_admin:
            if u.club_id:
                qs = qs.filter(club_id=u.club_id)
            else:
                qs = qs.none()

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
        u = self.request.user
        if u.is_admin:
            ctx['clubs'] = Club.objects.select_related('district').order_by(
                'district__name', 'zone', 'name'
            )
        elif u.club_id:
            ctx['clubs'] = Club.objects.filter(pk=u.club_id)
        else:
            ctx['clubs'] = Club.objects.none()
        ctx['selected_club'] = self.request.GET.get('club', '')
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


class DirectiveCreateView(RegistradorRequiredMixin, CreateView):
    model = Directive
    form_class = DirectiveForm
    template_name = 'clubs/directive_form.html'
    success_url = reverse_lazy('clubs:directive_list')

    def get_initial(self):
        initial = super().get_initial()
        club_id = self.request.GET.get('club')
        if club_id:
            initial['club'] = club_id
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_title'] = 'Nuevo directivo'
        ctx['cancel_url'] = reverse_lazy('clubs:directive_list')
        return ctx

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Directivo registrado correctamente.')
        return super().form_valid(form)


class DirectiveUpdateView(RegistradorRequiredMixin, UpdateView):
    model = Directive
    form_class = DirectiveForm
    template_name = 'clubs/directive_form.html'
    success_url = reverse_lazy('clubs:directive_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_title'] = 'Editar directivo'
        ctx['cancel_url'] = reverse_lazy('clubs:directive_list')
        return ctx

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Directivo actualizado correctamente.')
        return super().form_valid(form)


class DirectiveDeleteView(RegistradorRequiredMixin, DeleteView):
    model = Directive
    template_name = 'clubs/confirm_delete.html'
    success_url = reverse_lazy('clubs:directive_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Eliminar directivo'
        ctx['cancel_url'] = reverse_lazy('clubs:directive_list')
        return ctx

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Directivo eliminado.')
        return super().form_valid(form)


# ================= DISTRITOS (solo admin) =================

class DistrictListView(AdminRequiredMixin, ListView):
    model = MissionaryDistrict
    template_name = 'clubs/district_list.html'
    context_object_name = 'districts'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().annotate(clubs_count=Count('clubs', distinct=True))
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(name__icontains=q)
        return qs.order_by('name')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


class DistrictCreateView(AdminRequiredMixin, CreateView):
    model = MissionaryDistrict
    form_class = MissionaryDistrictForm
    template_name = 'clubs/district_form.html'
    success_url = reverse_lazy('clubs:district_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_title'] = 'Nuevo distrito misionero'
        ctx['cancel_url'] = reverse_lazy('clubs:district_list')
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Distrito misionero creado correctamente.')
        return super().form_valid(form)


class DistrictUpdateView(AdminRequiredMixin, UpdateView):
    model = MissionaryDistrict
    form_class = MissionaryDistrictForm
    template_name = 'clubs/district_form.html'
    success_url = reverse_lazy('clubs:district_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_title'] = 'Editar distrito misionero'
        ctx['cancel_url'] = reverse_lazy('clubs:district_list')
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Distrito misionero actualizado correctamente.')
        return super().form_valid(form)


class DistrictDeleteView(AdminRequiredMixin, DeleteView):
    model = MissionaryDistrict
    template_name = 'clubs/confirm_delete.html'
    success_url = reverse_lazy('clubs:district_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Eliminar distrito misionero'
        ctx['cancel_url'] = reverse_lazy('clubs:district_list')
        return ctx

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Distrito misionero eliminado.')
            return response
        except ProtectedError:
            messages.error(
                self.request,
                'No se puede eliminar: el distrito tiene clubes asociados. '
                'Reasigna o elimina primero esos clubes.',
            )
            return redirect('clubs:district_list')