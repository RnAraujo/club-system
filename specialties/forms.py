from django import forms
from .models import Specialty, SpecialtySchedule


class SpecialtyForm(forms.ModelForm):
    class Meta:
        model = Specialty
        fields = [
            'name', 'max_participants',
            'responsible_first_name', 'responsible_last_name',
            'responsible_phone', 'responsible_dni',
        ]
        labels = {
            'name': 'Nombre de la especialidad',
            'max_participants': 'Máximo de participantes',
            'responsible_first_name': 'Nombres',
            'responsible_last_name': 'Apellidos',
            'responsible_phone': 'Celular',
            'responsible_dni': 'DNI',
        }
        help_texts = {
            'name': 'Debe ser único en el sistema.',
            'max_participants': 'Cupo máximo que se asignará a cada programación.',
            'responsible_dni': 'Documento Nacional de Identidad (8 dígitos).',
            'responsible_phone': 'Número de contacto del responsable.',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej.: Fútbol',
                'autocomplete': 'off',
            }),
            'max_participants': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej.: 30',
                'min': 1,
                'inputmode': 'numeric',
            }),
            'responsible_first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej.: Juan',
                'autocomplete': 'off',
            }),
            'responsible_last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej.: Pérez',
                'autocomplete': 'off',
            }),
            'responsible_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej.: 999888777',
                'inputmode': 'tel',
            }),
            'responsible_dni': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '8 dígitos',
                'maxlength': 8,
                'inputmode': 'numeric',
                'autocomplete': 'off',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Los 4 campos del responsable son obligatorios a nivel de formulario
        for name in (
            'responsible_first_name', 'responsible_last_name',
            'responsible_phone', 'responsible_dni',
        ):
            self.fields[name].required = True

    def clean_responsible_dni(self):
        dni = (self.cleaned_data.get('responsible_dni') or '').strip()
        if not dni.isdigit() or len(dni) != 8:
            raise forms.ValidationError('El DNI debe tener exactamente 8 dígitos numéricos.')
        return dni


class ScheduleForm(forms.ModelForm):
    class Meta:
        model = SpecialtySchedule
        fields = ['specialty', 'date']
        labels = {
            'specialty': 'Especialidad',
            'date': 'Fecha de programación',
        }
        help_texts = {
            'date': 'Un participante solo puede inscribirse una vez por día.',
        }
        widgets = {
            'specialty': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
        }

    def clean(self):
        cleaned = super().clean()

        # Unicidad (specialty, date) — mensaje más amigable que la excepción de BD
        specialty = cleaned.get('specialty')
        date = cleaned.get('date')
        if specialty and date:
            qs = SpecialtySchedule.objects.filter(specialty=specialty, date=date)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    'Ya existe una programación para esta especialidad en esa fecha.'
                )

        # No permitir cambiar specialty o date si ya hay inscripciones
        if self.instance.pk and self.instance.registrations.exists():
            changed = set(self.changed_data)
            if 'specialty' in changed or 'date' in changed:
                raise forms.ValidationError(
                    'No se puede cambiar la especialidad ni la fecha porque '
                    'ya tiene inscripciones registradas.'
                )

        return cleaned