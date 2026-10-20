from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib import messages
from .forms import LoginForm, RegisterForm
from .mixins import AdminRequiredMixin


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'accounts/login.html'


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Usuario registrado correctamente.')
        return super().form_valid(form)