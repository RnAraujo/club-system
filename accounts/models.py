from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrador'
        REGISTRADOR = 'registrador', 'Registrador'
        OBSERVADOR = 'observador', 'Observador'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.OBSERVADOR,
        verbose_name='Rol',
    )
    club = models.ForeignKey(
        'clubs.Club',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name='Club',
    )

    @property
    def is_admin(self):
        return self.is_superuser or self.role == self.Role.ADMIN

    @property
    def is_registrador(self):
        return self.is_admin or self.role == self.Role.REGISTRADOR

    @property
    def is_observador(self):
        return True  # every role can observe