from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'Usuario'}),
        label='Usuario',
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'Contraseña'}),
        label='Contraseña',
    )


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'club', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'input'
        # Solo administradores pueden crear otros administradores
        request = kwargs.get('request')
        if request and not request.user.is_admin:
            self.fields['role'].choices = [
                (User.Role.OBSERVADOR.value, User.Role.OBSERVADOR.label),
            ]