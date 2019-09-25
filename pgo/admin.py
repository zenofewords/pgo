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
from pgo.utils import (
    calculate_weave_damage,
    calculate_pokemon_move_score,
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

    def save_model(self, request, obj, form, change):
        legacy = obj.legacy
        obj.legacy = False
        obj.move_type = obj.move.move_type.slug

        super().save_model(request, obj, form, change)
        pokemon = obj.pokemon

        if obj.cinematic:
            if obj not in pokemon.cinematic_moves.all():
                pokemon.cinematic_moves.add(obj)
        else:
            if obj not in pokemon.quick_moves.all():
                pokemon.quick_moves.add(obj)

        for quick_move in pokemon.quick_moves.filter(legacy=False):
            for cinematic_move in pokemon.cinematic_moves.filter(legacy=False):
                Moveset.objects.get_or_create(
                    pokemon=pokemon,
                    key='{} - {}'.format(quick_move.move, cinematic_move.move),
                    defaults={
                        'quick_move': quick_move,
                        'cinematic_move': cinematic_move,
                    }
                )
        obj.legacy = legacy
        obj.save()
        calculate_weave_damage(obj.pokemon)

        for moveset in obj.pokemon.moveset_set.all():
            calculate_pokemon_move_score(moveset)


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
