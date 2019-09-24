from rest_framework import serializers

from pgo.models import (
    PokemonMove, Move, Pokemon, Type,
)


class TypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Type
        fields = (
            'id', 'name', 'slug', 'strong', 'feeble', 'resistant', 'weak', 'immune', 'puny',
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
            'id', 'score', 'move', 'legacy',
        )


class PokemonSerializer(serializers.HyperlinkedModelSerializer):
    primary_type = TypeSerializer()
    secondary_type = TypeSerializer()

    class Meta:
        model = Pokemon
        fields = (
            'id', 'number', 'name', 'primary_type', 'secondary_type',
            'pgo_attack', 'pgo_defense', 'pgo_stamina', 'maximum_cp',
            'compound_resistance', 'compound_weakness',
        )


class SimplePokemonSerializer(serializers.Serializer):
    value = serializers.SerializerMethodField()
    label = serializers.SerializerMethodField()

    class Meta:
        model = Pokemon
        fields = (
            'value', 'label',
        )

    def get_value(self, obj):
        return obj.pk

    def get_label(self, obj):
        label = '{} | {}'.format(obj.name, obj.primary_type.name)

        if obj.secondary_type:
            label = '{} / {}'.format(label, obj.secondary_type.name)
        return label


class BreakpointCalcSerializer(serializers.Serializer):
    attacker = serializers.IntegerField()
    attacker_level = serializers.FloatField(min_value=1, max_value=40)
    attacker_quick_move = serializers.IntegerField()
    attacker_cinematic_move = serializers.IntegerField()
    attacker_atk_iv = serializers.IntegerField(min_value=0, max_value=15)
    weather_condition = serializers.IntegerField(required=False)
    friendship_boost = serializers.DecimalField(required=False, max_digits=3, decimal_places=2)
    defender = serializers.IntegerField()
    defender_quick_move = serializers.IntegerField()
    defender_cinematic_move = serializers.IntegerField()
    defender_cpm = serializers.DecimalField(max_digits=11, decimal_places=10)


class GoodToGoSerializer(serializers.Serializer):
    attacker = serializers.IntegerField()
    quick_move = serializers.IntegerField()
    cinematic_move = serializers.IntegerField()
    attack_iv = serializers.IntegerField(min_value=0, max_value=15)
    weather_condition = serializers.IntegerField(required=False)
    friendship_boost = serializers.DecimalField(required=False, max_digits=3, decimal_places=2)
    tier_3_6_raid_bosses = serializers.BooleanField(required=False)
    tier_1_2_raid_bosses = serializers.BooleanField(required=False)
