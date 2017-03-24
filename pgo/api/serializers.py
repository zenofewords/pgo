from rest_framework import serializers

from pgo.models import (
    Move, Pokemon, Type,
)


class TypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Type
        fields = (
            'name', 'strong', 'feeble', 'resistant', 'weak',
        )


class MoveSerializer(serializers.HyperlinkedModelSerializer):
    move_type = TypeSerializer()

    class Meta:
        model = Move
        fields = (
            'category', 'move_type', 'power', 'energy_delta', 'duration',
            'dps', 'eps',
        )


class PokemonSerializer(serializers.HyperlinkedModelSerializer):
    primary_type = TypeSerializer()
    secondary_type = TypeSerializer()

    class Meta:
        model = Pokemon
        fields = (
            'number', 'name', 'primary_type', 'secondary_type',
            'pgo_attack', 'pgo_defense', 'pgo_stamina', 'maximum_cp',
        )
