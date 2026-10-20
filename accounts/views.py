from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView
from django.contrib import messages
from django.db.models import Q

from .forms import LoginForm, RegisterForm, UserUpdateForm
from .mixins import AdminRequiredMixin
from .models import User


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'accounts/login.html'


class RegisterView(AdminRequiredMixin, CreateView):
    """Solo el administrador puede crear nuevos usuarios."""
    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:user_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_title'] = 'Nuevo usuario'
        ctx['cancel_url'] = reverse_lazy('accounts:user_list')
        return ctx

    def form_valid(self, form):
        messages.success(
            self.request,
            f'Usuario "{form.cleaned_data["username"]}" creado correctamente.'
        )
        return super().form_valid(form)


class UserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().select_related('club')

        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                Q(username__icontains=q) |
                Q(email__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q)
            )

        role = self.request.GET.get('role')
        if role:
            qs = qs.filter(role=role)

        return qs.order_by('username')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        ctx['selected_role'] = self.request.GET.get('role', '')
        ctx['roles'] = User.Role.choices
        return ctx


class UserUpdateView(AdminRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_title'] = f'Editar usuario: {self.object.username}'
        ctx['cancel_url'] = reverse_lazy('accounts:user_list')
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Usuario actualizado correctamente.')
        return super().form_valid(form)