from django.contrib import admin
from .models import Registration, RegistrationProcess


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('participant', 'schedule', 'date', 'registered_by', 'created_at')
    list_filter = ('date', 'schedule__specialty', 'participant__club')
    search_fields = ('participant__dni', 'participant__last_name')
    readonly_fields = ('date',)


@admin.register(RegistrationProcess)
class RegistrationProcessAdmin(admin.ModelAdmin):
    list_display = ('club', 'is_open', 'closed_by', 'closed_at')
    list_filter = ('is_open',)