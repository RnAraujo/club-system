from django import forms

from .models import Participant
from clubs.models import Club


class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ['dni', 'first_name', 'last_name', 'phone', 'club']
        labels = {
            'dni': 'DNI',
            'first_name': 'Nombres',
            'last_name': 'Apellidos',
            'phone': 'Celular',
            'club': 'Club',
        }
        help_texts = {
            'dni': 'Documento Nacional de Identidad (8 dígitos).',
            'phone': 'Opcional. Número de contacto del apoderado.',
        }
        widgets = {
            'dni': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej.: 76543210',
                'maxlength': 8,
                'inputmode': 'numeric',
                'autocomplete': 'off',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej.: Ana',
                'autocomplete': 'off',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej.: Torres',
                'autocomplete': 'off',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej.: 999888777',
                'inputmode': 'tel',
            }),
            'club': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and not user.is_admin and user.club_id:
            self.fields['club'].queryset = Club.objects.filter(pk=user.club_id)
            self.fields['club'].initial = user.club_id
            self.fields['club'].widget.attrs['disabled'] = True