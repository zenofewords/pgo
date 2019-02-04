from __future__ import unicode_literals

from django.contrib import admin

from pgo.models import (
    CPM,
    Friendship,
    Move,
    Moveset,
    Pokemon,
    PokemonMove,
    RaidBoss,
    RaidTier,
    Type,
    TypeEffectiveness,
    TypeEffectivenessScalar,
    WeatherCondition,
)


class MoveAdmin(admin.ModelAdmin):
    search_fields = (
        'name',
    )


class MovesetAdmin(admin.ModelAdmin):
    search_fields = (
        'pokemon__slug',
    )
    raw_id_fields = (
        'pokemon',
        'quick_move',
        'cinematic_move',
    )


class PokemonAdmin(admin.ModelAdmin):
    list_display = (
        'number', 'name', 'generation', 'primary_type', 'secondary_type', 'pgo_stamina',
        'pgo_attack', 'pgo_defense', 'maximum_cp',
    )
    search_fields = (
        'number', 'name', 'generation',
    )
    raw_id_fields = (
        'quick_moves', 'cinematic_moves',
    )


class PokemonMoveAdmin(admin.ModelAdmin):
    search_fields = (
        'pokemon__slug',
    )
    raw_id_fields = (
        'pokemon',
        'move',
    )


class RaidBossAdmin(admin.ModelAdmin):
    list_display = (
        'pokemon', 'raid_tier', 'status',
    )
    list_editable = (
        'status',
    )
    search_fields = (
        'pokemon__slug',
    )


admin.site.register(CPM)
admin.site.register(Friendship)
admin.site.register(Move, MoveAdmin)
admin.site.register(Moveset, MovesetAdmin)
admin.site.register(Pokemon, PokemonAdmin)
admin.site.register(PokemonMove, PokemonMoveAdmin)
admin.site.register(RaidBoss, RaidBossAdmin)
admin.site.register(RaidTier)
admin.site.register(Type)
admin.site.register(TypeEffectiveness)
admin.site.register(TypeEffectivenessScalar)
admin.site.register(WeatherCondition)
