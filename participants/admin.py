from django.contrib import admin
from .models import Participant


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('dni', 'last_name', 'first_name', 'club')
    list_filter = ('club',)
    search_fields = ('dni', 'first_name', 'last_name')