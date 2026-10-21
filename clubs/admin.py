from django.contrib import admin
from .models import Club, Directive, MissionaryDistrict


class DirectiveInline(admin.TabularInline):
    model = Directive
    extra = 0


@admin.register(MissionaryDistrict)
class MissionaryDistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'clubs_count', 'created_at')
    search_fields = ('name',)

    def clubs_count(self, obj):
        return obj.clubs.count()
    clubs_count.short_description = 'Clubes'


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ('name', 'district', 'zone', 'participants_count', 'created_at')
    list_filter = ('district', 'zone')
    search_fields = ('name', 'district__name')
    ordering = ('district__name', 'zone', 'name')
    inlines = [DirectiveInline]

    def participants_count(self, obj):
        return obj.participants.count()
    participants_count.short_description = 'Participantes'


@admin.register(Directive)
class DirectiveAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'position', 'club', 'dni')
    list_filter = ('club__district', 'club', 'position')
    search_fields = ('first_name', 'last_name', 'dni')