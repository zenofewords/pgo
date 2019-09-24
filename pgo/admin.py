from django.contrib import admin

from pgo.models import (
    CPM,
    EffectivenessScalar,
    Friendship,
    Move,
    MoveAvailability,
    Moveset,
    Pokemon,
    PokemonMove,
    RaidBoss,
    RaidTier,
    Type,
    WeatherCondition,
)


class FriendshipAdmin(admin.ModelAdmin):
    list_display = (
        'level', 'damage_boost', 'order',
    )
    list_editable = (
        'order',
    )
    ordering = ('order',)


class MoveAdmin(admin.ModelAdmin):
    search_fields = (
        'name',
    )


class MoveAvailabilityAdmin(admin.ModelAdmin):
    search_fields = (
        'pokemon_move__pokemon__name', 'available_from', 'available_to', 'legacy_status',
    )
    raw_id_fields = (
        'pokemon_move',
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
        'pokemon', 'raid_tier',
    )
    list_editable = (
        'raid_tier',
    )
    search_fields = (
        'pokemon__slug',
    )


admin.site.register(CPM)
admin.site.register(EffectivenessScalar)
admin.site.register(Friendship, FriendshipAdmin)
admin.site.register(Move, MoveAdmin)
admin.site.register(MoveAvailability, MoveAvailabilityAdmin)
admin.site.register(Moveset, MovesetAdmin)
admin.site.register(Pokemon, PokemonAdmin)
admin.site.register(PokemonMove, PokemonMoveAdmin)
admin.site.register(RaidBoss, RaidBossAdmin)
admin.site.register(RaidTier)
admin.site.register(Type)
admin.site.register(WeatherCondition)
