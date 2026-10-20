from django.db import models
from django.conf import settings
from participants.models import Participant
from specialties.models import SpecialtySchedule


class Registration(models.Model):
    participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE,
        related_name='registrations', verbose_name='Participante',
    )
    schedule = models.ForeignKey(
        SpecialtySchedule, on_delete=models.PROTECT,
        related_name='registrations', verbose_name='Programación',
    )
    date = models.DateField(editable=False, verbose_name='Fecha')
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Registrado por',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Inscripción'
        verbose_name_plural = 'Inscripciones'
        ordering = ['-date', 'participant__last_name']
        constraints = [
            models.UniqueConstraint(
                fields=['participant', 'date'],
                name='unique_registration_per_day',
                violation_error_message='El participante ya tiene una inscripción para este día.',
            )
        ]

    def save(self, *args, **kwargs):
        self.date = self.schedule.date
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.participant} → {self.schedule.specialty} ({self.date})"


class RegistrationProcess(models.Model):
    club = models.OneToOneField(
        'clubs.Club', on_delete=models.CASCADE,
        related_name='registration_process', verbose_name='Club',
    )
    is_open = models.BooleanField(default=True, verbose_name='Abierto')
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='closed_processes',
    )
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Proceso de inscripción'
        verbose_name_plural = 'Procesos de inscripción'

    def __str__(self):
        return f"{self.club.name} — {'Abierto' if self.is_open else 'Cerrado'}"