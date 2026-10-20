from django.db import models


class Participant(models.Model):
    dni = models.CharField(max_length=8, unique=True, verbose_name='DNI')
    first_name = models.CharField(max_length=150, verbose_name='Nombres')
    last_name = models.CharField(max_length=150, verbose_name='Apellidos')
    phone = models.CharField(max_length=15, blank=True, verbose_name='Celular')
    club = models.ForeignKey(
        'clubs.Club', on_delete=models.PROTECT,
        related_name='participants', verbose_name='Club',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Participante'
        verbose_name_plural = 'Participantes'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"