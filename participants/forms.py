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
        self.user = user

        if user and not user.is_admin:
            # --- Registrador / observador ---
            if user.club_id:
                self.fields['club'].queryset = Club.objects.filter(pk=user.club_id)
                self.fields['club'].initial = user.club_id
                self.fields['club'].disabled = True
            else:
                # Sin club asignado: no puede crear participantes
                self.fields['club'].queryset = Club.objects.none()
                self.fields['club'].disabled = True
        else:
            # --- Admin: select normal con todos los clubes ---
            self.fields['club'].queryset = (
                Club.objects.select_related('district')
                .order_by('district__name', 'zone', 'name')
            )
            self.fields['club'].empty_label = '— Selecciona un club —'

    def clean_club(self):
        """Defensa final: para no-admin siempre devuelve su club."""
        if self.user and not self.user.is_admin and self.user.club_id:
            return self.user.club
        return self.cleaned_data.get('club')

    def clean_dni(self):
        dni = (self.cleaned_data.get('dni') or '').strip()
        if not dni.isdigit() or len(dni) != 8:
            raise forms.ValidationError('El DNI debe tener exactamente 8 dígitos numéricos.')
        return dni