from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from .models import Registration, RegistrationProcess
from specialties.models import SpecialtySchedule


@transaction.atomic
def register_participant(*, participant, schedule: SpecialtySchedule, user):
    """Inscribe un participante validando todas las reglas de negocio."""
    # 1. Proceso abierto
    process, _ = RegistrationProcess.objects.get_or_create(club=participant.club)
    if not process.is_open:
        raise ValidationError('El proceso de inscripción está cerrado para este club.')

    # 2. Bloquear programación para evitar sobreventa
    schedule_locked = SpecialtySchedule.objects.select_for_update().get(pk=schedule.pk)
    if schedule_locked.available_slots <= 0:
        raise ValidationError('No hay cupos disponibles para esta especialidad.')

    # 3. Un niño por especialidad por día (constraint DB + check explícito)
    if Registration.objects.filter(participant=participant, date=schedule.date).exists():
        raise ValidationError('El participante ya tiene una inscripción para este día.')

    # 4. Crear
    reg = Registration.objects.create(
        participant=participant,
        schedule=schedule_locked,
        registered_by=user,
    )

    # 5. Descontar cupo
    schedule_locked.available_slots -= 1
    schedule_locked.save(update_fields=['available_slots'])

    return reg


def close_process(*, club, user):
    process, _ = RegistrationProcess.objects.get_or_create(club=club)
    process.is_open = False
    process.closed_by = user
    process.closed_at = timezone.now()
    process.save()
    return process


def reopen_process(*, club, user):
    if not user.is_admin:
        raise ValidationError('Solo un administrador puede reabrir el proceso.')
    process, _ = RegistrationProcess.objects.get_or_create(club=club)
    process.is_open = True
    process.closed_by = None
    process.closed_at = None
    process.save()
    return process