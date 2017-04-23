from __future__ import unicode_literals

from django.contrib import admin

from pgo.models import (
    CPM,
    Move,
    MoveSet,
    Pokemon,
    Type,
    TypeEffectivness,
    TypeEffectivnessScalar,
)


class PokemonAdmin(admin.ModelAdmin):
    list_display = (
        'number', 'name', 'primary_type', 'secondary_type', 'pgo_stamina',
        'pgo_attack', 'pgo_defense', 'maximum_cp',
    )


admin.site.register(CPM)
admin.site.register(Move)
admin.site.register(MoveSet)
admin.site.register(Pokemon, PokemonAdmin)
admin.site.register(Type)
admin.site.register(TypeEffectivness)
admin.site.register(TypeEffectivnessScalar)
