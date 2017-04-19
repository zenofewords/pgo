from rest_framework import serializers

from pgo.models import (
    Move, Pokemon, Type,
)


class TypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Type
        fields = (
            'id', 'name', 'strong', 'feeble', 'resistant', 'weak',
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
            'id', 'name', 'category',
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


# todo rework and extract attacker and defender serializer (needs js rework)
class AttackProficiencySerializer(serializers.Serializer):
    attacker = serializers.IntegerField()
    quick_move = serializers.IntegerField()
    cinematic_move = serializers.IntegerField()
    attacker_level = serializers.FloatField()
    attack_iv = serializers.IntegerField()
    defender = serializers.IntegerField()
    defender_level = serializers.FloatField()
    defense_iv = serializers.IntegerField()


class AttackProficiencyStatsSerializer(serializers.Serializer):
    attacker = serializers.JSONField()
    quick_move = serializers.JSONField()
    cinematic_move = serializers.JSONField()
    defender = serializers.JSONField()


class AttackProficiencyDetailSerializer(serializers.Serializer):
    attacker = serializers.IntegerField()
    quick_move = serializers.IntegerField()
    cinematic_move = serializers.IntegerField()
    attacker_level = serializers.FloatField()
    attack_iv = serializers.IntegerField()
    defender = serializers.IntegerField()
    defender_level = serializers.FloatField()
    defense_iv = serializers.IntegerField()
