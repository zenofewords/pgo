from django.contrib import admin

from registry.models import Country, Town, Team, Trainer


class CountryAdmin(admin.ModelAdmin):
    fields = (
        'name', 'slug',
    )
    list_display = (
        'name', 'slug', 'trainer_count',
    )

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()
        super(CountryAdmin, self).save_model(request, obj, form, change)


class TownAdmin(admin.ModelAdmin):
    fields = (
        'name', 'slug', 'country',
    )
    list_display = (
        'name', 'slug', 'trainer_count',
    )

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()
        super(TownAdmin, self).save_model(request, obj, form, change)


class TeamAdmin(admin.ModelAdmin):
    fields = (
        'name', 'slug', 'color',
    )
    list_display = (
        'name', 'slug', 'trainer_count',
    )

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()
        super(TeamAdmin, self).save_model(request, obj, form, change)


class TrainerAdmin(admin.ModelAdmin):
    fields = (
        'nickname', 'team', 'legit', 'recruited', 'retired', 'level', 'towns',
    )
    list_display = (
        'nickname', 'team', 'legit', 'recruited', 'retired', 'level', 'created',
    )
    search_fields = (
        'nickname', 'level',
    )

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()
        super(TrainerAdmin, self).save_model(request, obj, form, change)


admin.site.register(Country, CountryAdmin)
admin.site.register(Town, TownAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Trainer, TrainerAdmin)
