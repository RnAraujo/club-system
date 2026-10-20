from django.contrib import admin
from .models import Specialty, SpecialtySchedule


class ScheduleInline(admin.TabularInline):
    model = SpecialtySchedule
    extra = 0
    readonly_fields = ('available_slots',)


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_participants')
    search_fields = ('name',)
    inlines = [ScheduleInline]


@admin.register(SpecialtySchedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('specialty', 'date', 'available_slots')
    list_filter = ('specialty', 'date')