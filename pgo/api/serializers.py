from rest_framework import serializers

from pgo.models import (
    PokemonMove, Move, Pokemon, Type,
)


class TypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Type
        fields = (
            'id', 'name', 'strong', 'feeble', 'resistant', 'weak', 'immune', 'puny',
        )


class MoveSerializer(serializers.HyperlinkedModelSerializer):
    move_type = TypeSerializer()

    class Meta:
        model = Move
        fields = (
            'id', 'name', 'category', 'move_type', 'power', 'energy_delta',
            'duration', 'dps', 'eps',
        )


class SimpleMoveSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Move
        fields = (
            'id', 'name', 'category', 'power',
        )


class PokemonMoveSerializer(serializers.HyperlinkedModelSerializer):
    move = SimpleMoveSerializer()

    class Meta:
        model = PokemonMove
        fields = (
            'id', 'score', 'move',
        )


class PokemonSerializer(serializers.HyperlinkedModelSerializer):
    primary_type = TypeSerializer()
    secondary_type = TypeSerializer()

    class Meta:
        model = Pokemon
        fields = (
            'id', 'number', 'name', 'primary_type', 'secondary_type',
            'pgo_attack', 'pgo_defense', 'pgo_stamina', 'maximum_cp',
        )


class BreakpointCalcSerializer(serializers.Serializer):
    attacker = serializers.IntegerField()
    quick_move = serializers.IntegerField()
    cinematic_move = serializers.IntegerField()
    attacker_lvl = serializers.FloatField()
    attack_iv = serializers.IntegerField()
    defender = serializers.IntegerField()
    defender_lvl = serializers.FloatField()
    defense_iv = serializers.IntegerField()
    raid_tier = serializers.IntegerField(required=False)
    weather_condition = serializers.IntegerField(required=False)


class BreakpointCalcStatsSerializer(serializers.Serializer):
    attacker = serializers.JSONField()
    quick_move = serializers.JSONField()
    cinematic_move = serializers.JSONField()
    defender = serializers.JSONField()
    raid_tier = serializers.IntegerField(required=False)
    weather_condition = serializers.IntegerField(required=False)


class GoodToGoSerializer(serializers.Serializer):
    attacker = serializers.IntegerField()
    quick_move = serializers.IntegerField()
    cinematic_move = serializers.IntegerField()
    attack_iv = serializers.IntegerField()
    weather_condition = serializers.IntegerField(required=False)
    current_raid_bosses = serializers.BooleanField(required=False)
    past_raid_bosses = serializers.BooleanField(required=False)
    relevant_defenders = serializers.BooleanField(required=False)
