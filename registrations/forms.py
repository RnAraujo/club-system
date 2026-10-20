from django import forms
from django.utils import timezone

from participants.models import Participant
from specialties.models import SpecialtySchedule

from .services import register_participant


class RegistrationForm(forms.Form):
    participant = forms.ModelChoiceField(
        queryset=Participant.objects.select_related('club').all(),
        label='Participante',
        empty_label='— Selecciona un participante —',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    schedule = forms.ModelChoiceField(
        queryset=(
            SpecialtySchedule.objects
            .select_related('specialty')
            .filter(
                available_slots__gt=0,
                date__gte=timezone.localdate(),
            )
            .order_by('date', 'specialty__name')
        ),
        label='Especialidad / Fecha',
        empty_label='— Selecciona una especialidad —',
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Solo se muestran programaciones de hoy en adelante con cupos disponibles.',
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user and not user.is_admin and user.club_id:
            self.fields['participant'].queryset = (
                Participant.objects
                .filter(club_id=user.club_id)
                .select_related('club')
            )

    def save(self):
        return register_participant(
            participant=self.cleaned_data['participant'],
            schedule=self.cleaned_data['schedule'],
            user=self.user,
        )