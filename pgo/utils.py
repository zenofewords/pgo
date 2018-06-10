from __future__ import division

from decimal import Decimal
from math import floor

from django.http import Http404

from pgo.models import Move, Pokemon, RaidBoss, TypeEffectivness

SUPER_EFFECTIVE_SCALAR = 1.4
NOT_VERY_EFFECTIVE_SCALAR = 0.714
IMMUNE = 0.51
NEUTRAL_SCALAR = 1.0
STAB_SCALAR = 1.2
WEATHER_BOOST_SCALAR = 1.2
TIMEOUT = 99000
CINEMATIC_MOVE_FACTOR = 1.1
MAX_IV = 15
DEFAULT_EFFECTIVNESS = Decimal(str(NEUTRAL_SCALAR))


class Frailty(object):
    NEUTRAL = '{neutral}'
    RESILIENT = '{resilient}'
    FRAGILE = '{fragile}'


def calculate_weave_damage(quick_move, cinematic_move):
    if quick_move.energy_delta > 0:
        quick_moves_required = (cinematic_move.energy_delta * - 1) / quick_move.energy_delta
    else:
        quick_moves_required = 0
    cycle_dps = (
        quick_moves_required * quick_move.damage_per_hit + cinematic_move.damage_per_hit) / (
        (quick_moves_required * quick_move.duration + cinematic_move.duration) / 1000)

    # nerf moveset damage for single bar charge moves
    if cinematic_move.energy_delta == -100:
        cycle_dps = cycle_dps / 1.06

    return cycle_dps


def calculate_dph(power, attack_multiplier, stab, weather_boost, effectivness=1.0):

    def _get_stab(stab):
        return STAB_SCALAR if stab else NEUTRAL_SCALAR

    def _get_weather_boost(weather_boost):
        return WEATHER_BOOST_SCALAR if weather_boost else NEUTRAL_SCALAR

    return int(
        floor(0.5 * power * float(attack_multiplier) * _get_stab(
            stab) * float(effectivness) * _get_weather_boost(weather_boost))
    ) + 1


def calculate_health(total_stamina, cpm):
    return int(floor(total_stamina * cpm))


def calculate_defender_health(total_stamina, cpm):
    return calculate_health(total_stamina, cpm) * 2


def calculate_defense(total_defense, cpm):
    return int(floor(total_defense * cpm))


def get_pokemon_data(id):
    try:
        return Pokemon.objects.only(
            'name', 'pgo_attack', 'pgo_stamina', 'primary_type_id', 'secondary_type_id'
        ).get(pk=id)
    except Pokemon.DoesNotExist:
        raise Http404


def get_move_data(id):
    try:
        return Move.objects.only('name', 'power', 'duration', 'move_type_id').get(pk=id)
    except Move.DoesNotExist:
        raise Http404


def determine_move_effectivness(move, pokemon):
    if isinstance(pokemon, RaidBoss):
        pokemon = pokemon.pokemon

    secondary_type_effectivness = DEFAULT_EFFECTIVNESS
    if pokemon.secondary_type_id:
        secondary_type_effectivness = TypeEffectivness.objects.get(
            type_offense__id=move.move_type_id,
            type_defense__id=pokemon.secondary_type_id).effectivness.scalar
    primary_type_effectivness = TypeEffectivness.objects.get(
        type_offense__id=move.move_type_id,
        type_defense__id=pokemon.primary_type_id).effectivness.scalar
    return secondary_type_effectivness * primary_type_effectivness


def is_move_stab(move, pokemon):
    return (
        pokemon.primary_type_id == move.move_type_id or
        pokemon.secondary_type_id == move.move_type_id
    )
