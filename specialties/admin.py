from django.contrib import admin
from .models import Specialty, SpecialtySchedule


class ScheduleInline(admin.TabularInline):
    model = SpecialtySchedule
    extra = 0
    readonly_fields = ('available_slots',)
    fields = ('date', 'available_slots')
    ordering = ('date',)


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'max_participants',
        'responsible_last_name',
        'responsible_first_name',
        'responsible_dni',
        'responsible_phone',
        'total_schedules',
        'total_registered',
    )
    list_filter = ('name',)
    search_fields = (
        'name',
        'responsible_first_name',
        'responsible_last_name',
        'responsible_dni',
        'responsible_phone',
    )
    ordering = ('name',)
    inlines = [ScheduleInline]

    fieldsets = (
        ('Datos de la especialidad', {
            'fields': ('name', 'max_participants'),
        }),
        ('Responsable de la especialidad', {
            'description': (
                'Persona a cargo de la especialidad. '
                'Estos datos son asignados por el administrador.'
            ),
            'fields': (
                'responsible_first_name',
                'responsible_last_name',
                'responsible_dni',
                'responsible_phone',
            ),
        }),
    )

    def total_schedules(self, obj):
        return obj.schedules.count()
    total_schedules.short_description = 'Programaciones'

    def total_registered(self, obj):
        return SpecialtySchedule.objects.filter(
            specialty=obj
        ).aggregate(
            total=admin.utils.models.Count('registrations')
        )['total'] or 0
    total_registered.short_description = 'Inscritos'


@admin.register(SpecialtySchedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'specialty',
        'date',
        'available_slots',
        'max_participants_display',
        'registered_display',
    )
    list_filter = ('specialty', 'date')
    search_fields = ('specialty__name',)
    ordering = ('-date', 'specialty__name')
    readonly_fields = ('available_slots',)
    date_hierarchy = 'date'

    def max_participants_display(self, obj):
        return obj.specialty.max_participants
    max_participants_display.short_description = 'Cupo máximo'

    def registered_display(self, obj):
        return obj.registrations.count()
    registered_display.short_description = 'Inscritos'