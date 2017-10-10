from django.contrib import admin

from registry.models import Country, Town, Team, Trainer


class ReadOnlyMixin:
    readonly_fields = ('trainer_count',)


class CountryAdmin(ReadOnlyMixin, admin.ModelAdmin):
    fields = (
        'name', 'slug',
    )
    list_display = (
        'name', 'slug', 'trainer_count',
    )


class TownAdmin(ReadOnlyMixin, admin.ModelAdmin):
    fields = (
        'name', 'slug', 'country',
    )
    list_display = (
        'name', 'slug', 'trainer_count',
    )


class TeamAdmin(ReadOnlyMixin, admin.ModelAdmin):
    fields = (
        'name', 'slug', 'color',
    )
    list_display = (
        'name', 'slug', 'trainer_count',
    )


class TrainerAdmin(admin.ModelAdmin):
    fields = (
        'nickname', 'team', 'legit', 'recruited', 'retired', 'level', 'town',
    )
    list_display = (
        'nickname', 'team', 'legit', 'recruited', 'retired', 'level', 'town', 'created',
    )
    search_fields = (
        'nickname', 'level',
    )


admin.site.register(Country, CountryAdmin)
admin.site.register(Town, TownAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Trainer, TrainerAdmin)
