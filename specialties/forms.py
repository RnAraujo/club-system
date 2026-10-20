from django import forms
from .models import Specialty, SpecialtySchedule


class SpecialtyForm(forms.ModelForm):
    class Meta:
        model = Specialty
        fields = ['name', 'max_participants']
        labels = {
            'name': 'Nombre de la especialidad',
            'max_participants': 'Máximo de participantes',
        }
        help_texts = {
            'name': 'Debe ser único en el sistema.',
            'max_participants': 'Cupo máximo que se asignará a cada programación.',
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
        }


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