from django import forms
from .models import Registration
from participants.models import Participant
from specialties.models import SpecialtySchedule
from django.core.exceptions import ValidationError
from .services import register_participant


class RegistrationForm(forms.Form):
    participant = forms.ModelChoiceField(
        queryset=Participant.objects.select_related('club').all(),
        label='Participante',
        widget=forms.Select(attrs={'class': 'input'}),
    )
    schedule = forms.ModelChoiceField(
        queryset=SpecialtySchedule.objects.select_related('specialty').filter(available_slots__gt=0),
        label='Especialidad / Fecha',
        widget=forms.Select(attrs={'class': 'input'}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user and not user.is_admin and user.club_id:
            self.fields['participant'].queryset = (
                Participant.objects.filter(club_id=user.club_id).select_related('club')
            )

    def save(self):
        return register_participant(
            participant=self.cleaned_data['participant'],
            schedule=self.cleaned_data['schedule'],
            user=self.user,
        )