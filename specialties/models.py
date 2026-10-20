from django.db import models
from django.core.validators import MinValueValidator


class Specialty(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Nombre')
    max_participants = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Máximo de participantes',
    )

    class Meta:
        verbose_name = 'Especialidad'
        verbose_name_plural = 'Especialidades'
        ordering = ['name']

    def __str__(self):
        return self.name


class SpecialtySchedule(models.Model):
    specialty = models.ForeignKey(
        Specialty, on_delete=models.CASCADE,
        related_name='schedules', verbose_name='Especialidad',
    )
    date = models.DateField(verbose_name='Fecha')
    available_slots = models.PositiveIntegerField(
        default=0, editable=False, verbose_name='Cupos disponibles',
    )

    class Meta:
        verbose_name = 'Programación'
        verbose_name_plural = 'Programaciones'
        ordering = ['date', 'specialty__name']
        constraints = [
            models.UniqueConstraint(
                fields=['specialty', 'date'],
                name='unique_specialty_per_day',
            )
        ]

    def save(self, *args, **kwargs):
        if not self.pk:
            self.available_slots = self.specialty.max_participants
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.specialty.name} — {self.date:%d/%m/%Y}"