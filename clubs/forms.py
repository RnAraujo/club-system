from django import forms
from .models import Club, Directive


class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ['name', 'zone']
        labels = {
            'name': 'Nombre del club',
            'zone': 'Zona',
        }
        help_texts = {
            'name': 'Nombre oficial del club (debe ser único).',
            'zone': 'Zona o sector al que pertenece el club.',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej.: Club Los Andes',
                'autocomplete': 'off',
            }),
            'zone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej.: Zona Norte',
                'autocomplete': 'off',
            }),
        }


class DirectiveForm(forms.ModelForm):
    class Meta:
        model = Directive
        fields = ['club', 'first_name', 'last_name', 'position', 'phone', 'dni']
        labels = {
            'club': 'Club',
            'first_name': 'Nombres',
            'last_name': 'Apellidos',
            'position': 'Cargo',
            'phone': 'Celular',
            'dni': 'DNI',
        }
        help_texts = {
            'position': 'Un cargo solo puede estar ocupado por una persona por club.',
            'dni': 'Documento Nacional de Identidad (8 dígitos).',
            'phone': 'Opcional. Número de contacto.',
        }
        widgets = {
            'club': forms.Select(attrs={'class': 'form-select'}),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej.: Juan',
                'autocomplete': 'off',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej.: Pérez',
                'autocomplete': 'off',
            }),
            'position': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej.: 999888777',
                'inputmode': 'tel',
            }),
            'dni': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '8 dígitos',
                'maxlength': 8,
                'inputmode': 'numeric',
                'autocomplete': 'off',
            }),
        }