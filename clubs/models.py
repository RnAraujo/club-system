from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class MissionaryDistrict(models.Model):
    """Distrito Misionero — agrupa a varios clubes."""
    name = models.CharField(
        max_length=150, unique=True,
        verbose_name='Distrito Misionero',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Distrito Misionero'
        verbose_name_plural = 'Distritos Misioneros'
        ordering = ['name']

    def __str__(self):
        return self.name


class Club(models.Model):
    district = models.ForeignKey(
        MissionaryDistrict,
        on_delete=models.PROTECT,
        related_name='clubs',
        verbose_name='Distrito Misionero',
    )
    name = models.CharField(max_length=150, verbose_name='Nombre del club')
    zone = models.PositiveSmallIntegerField(
        verbose_name='Zona',
        validators=[MinValueValidator(1), MaxValueValidator(99)],
        help_text='Número de zona (1, 2, 3, ...)',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Club'
        verbose_name_plural = 'Clubes'
        ordering = ['district__name', 'zone', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['district', 'name'],
                name='unique_club_name_per_district',
                violation_error_message='Ya existe un club con ese nombre en este distrito.',
            )
        ]

    def __str__(self):
        return f"{self.name} — Zona {self.zone}"

    @property
    def full_label(self):
        return f"{self.district.name} · Zona {self.zone} · {self.name}"


class Directive(models.Model):
    class Position(models.TextChoices):
        DIRECTOR = 'director', 'Director'
        ASOCIADO = 'asociado', 'Asociado'
        TESORERO = 'tesorero', 'Tesorero'
        SECRETARIO = 'secretario', 'Secretario'
        CONSEJERO = 'consejero', 'Consejero'

    club = models.ForeignKey(
        Club, on_delete=models.CASCADE,
        related_name='directives', verbose_name='Club',
    )
    first_name = models.CharField(max_length=150, verbose_name='Nombres')
    last_name = models.CharField(max_length=150, verbose_name='Apellidos')
    position = models.CharField(
        max_length=20, choices=Position.choices, verbose_name='Cargo',
    )
    phone = models.CharField(max_length=15, blank=True, verbose_name='Celular')
    dni = models.CharField(max_length=8, unique=True, verbose_name='DNI')

    class Meta:
        verbose_name = 'Directivo'
        verbose_name_plural = 'Directiva'
        ordering = ['position']
        constraints = [
            models.UniqueConstraint(
                fields=['club', 'position'],
                name='unique_position_per_club',
                violation_error_message='Este cargo ya está ocupado en el club.',
            )
        ]

    def __str__(self):
        return f"{self.get_position_display()} — {self.last_name}, {self.first_name}"