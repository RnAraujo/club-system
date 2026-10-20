from django.contrib import admin
from .models import Club, Directive


class DirectiveInline(admin.TabularInline):
    model = Directive
    extra = 0


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ('name', 'zone', 'created_at')
    search_fields = ('name', 'zone')
    inlines = [DirectiveInline]


@admin.register(Directive)
class DirectiveAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'position', 'club', 'dni')
    list_filter = ('club', 'position')
    search_fields = ('first_name', 'last_name', 'dni')