from __future__ import division

from decimal import Decimal
from math import floor

from django.db.models import Q, Max
from django.http import Http404
from django.utils.text import slugify

from pgo.models import Move, Pokemon, RaidBoss, Type, TypeEffectiveness

SUPER_EFFECTIVE_SCALAR = 1.4
NOT_VERY_EFFECTIVE_SCALAR = 0.714
IMMUNE = 0.51
NEUTRAL_SCALAR = 1.0
STAB_SCALAR = 1.2
WEATHER_BOOST_SCALAR = 1.2
MAX_IV = 15
DEFAULT_EFFECTIVENESS = Decimal(str(NEUTRAL_SCALAR))


class Frailty(object):
    NEUTRAL = '{neutral}'
    RESILIENT = '{resilient}'
    FRAGILE = '{fragile}'


def calculate_cycle_dps(quick_move, cinematic_move):
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


def calculate_dph(
        power, attack_multiplier, stab, weather_boost, effectiveness=1.0, friendship_boost=1.0):

    def _get_stab(stab):
        return STAB_SCALAR if stab else NEUTRAL_SCALAR

    def _get_weather_boost(weather_boost):
        return WEATHER_BOOST_SCALAR if weather_boost else NEUTRAL_SCALAR

    return int(floor(
        0.5 * power * float(attack_multiplier) * _get_stab(stab) * float(effectiveness) *
        _get_weather_boost(weather_boost) * float(friendship_boost))
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
            'name', 'pgo_attack', 'pgo_stamina', 'primary_type_id', 'secondary_type_id',
            'compound_weakness', 'compound_resistance',
        ).prefetch_related(
            'quick_moves__move__move_type',
            'cinematic_moves__move__move_type'
        ).get(pk=id)
    except Pokemon.DoesNotExist:
        raise Http404


def get_move_data(id):
    try:
        return Move.objects.only(
            'name', 'power', 'duration', 'move_type_id'
        ).select_related(
            'move_type'
        ).get(pk=id)
    except Move.DoesNotExist:
        raise Http404


def determine_move_effectiveness(move_type, pokemon):
    if isinstance(pokemon, RaidBoss):
        pokemon = pokemon.pokemon

    effectiveness = 1.0
    if pokemon.compound_resistance.get(move_type.name):
        effectiveness = pokemon.compound_resistance[move_type.name]
    if pokemon.compound_weakness.get(move_type.name):
        effectiveness = pokemon.compound_weakness[move_type.name]
    return effectiveness


def is_move_stab(move, pokemon):
    return (
        pokemon.primary_type_id == move.move_type_id or
        pokemon.secondary_type_id == move.move_type_id
    )


def get_top_counter_qs(defender):
    defender_weakness = [x.lower() for x in defender.compound_weakness.keys()]
    defender_resistance = [x.lower() for x in defender.compound_resistance.keys()]
    defender_qk_move_type = defender.quick_move.move_type
    defender_cm_move_type = defender.cinematic_move.move_type
    queryset = Pokemon.objects.implemented().filter(
        stat_product__gte=500,
        pgo_attack__gte=170
    )

    qs_id_list = []
    # S = pokemon with a quick and charge move that is SE against the defender,
    # and they resist the defender’s quick and charge move
    s_id_list = list(queryset.filter(
        Q(
            quick_moves__move_type__in=defender_weakness,
            cinematic_moves__move_type__in=defender_weakness
        )
            & Q(compound_resistance__icontains=defender_qk_move_type)
            & Q(compound_resistance__icontains=defender_cm_move_type)
        ).distinct().values_list(
            'id', flat=True
        ))
    qs_id_list += s_id_list

    # A = pokemon with a quick and charge move that is SE against the defender,
    # and they resist the defender’s charge move, excluding S
    a_id_list = list(queryset.filter(
            quick_moves__move_type__in=defender_weakness,
            cinematic_moves__move_type__in=defender_weakness,
            compound_resistance__icontains=defender_cm_move_type,
            stat_product__gte=510
        ).exclude(
            id__in=qs_id_list
        ).values_list('id', flat=True))
    qs_id_list += a_id_list

    # B = pokemon with a charge move that is SE against the defender, their quick move is not resisted,
    # and they resist the defender’s quick and charge move, excluding A
    b_id_list = list(queryset.filter(
            Q(cinematic_moves__move_type__in=defender_weakness)
            & Q(compound_resistance__icontains=defender_qk_move_type)
            & Q(compound_resistance__icontains=defender_cm_move_type)
            & Q(stat_product__gte=530)
        ).exclude(
            quick_moves__move_type__in=defender_resistance
        ).exclude(
            id__in=qs_id_list
        ).values_list('id', flat=True))
    qs_id_list += b_id_list

    # C = pokemon with a charge move that is SE against the defender, their quick move is not resisted,
    # and they resist the defender’s charge move, excluding B
    c_id_list = list(queryset.filter(
            cinematic_moves__move_type__in=defender_weakness,
            compound_resistance__icontains=defender_cm_move_type,
            stat_product__gte=550
        ).exclude(
            quick_moves__move_type__in=defender_resistance
        ).exclude(
            id__in=qs_id_list
        ).values_list('id', flat=True))
    qs_id_list += c_id_list

    # D = pokemon with a quick and charge move that is SE against the defender,
    # and they are not weak to the defender’s quick or charge move, excluding C
    d_id_list = list(queryset.filter(
            quick_moves__move_type__in=defender_weakness,
            cinematic_moves__move_type__in=defender_weakness,
            stat_product__gte=570
        ).exclude(
            Q(compound_weakness__icontains=defender_qk_move_type)
            | Q(compound_weakness__icontains=defender_cm_move_type)
        ).exclude(
            id__in=qs_id_list
        ).values_list('id', flat=True))
    qs_id_list += d_id_list

    # E = pokemon with a quick and charge move that is SE against the defender,
    # and they are not weak to the defender’s charge move, excluding D
    e_id_list = list(queryset.filter(
            quick_moves__move_type__in=defender_weakness,
            cinematic_moves__move_type__in=defender_weakness,
        ).exclude(
            compound_weakness__icontains=defender_cm_move_type
        ).exclude(
            id__in=qs_id_list
        ).values_list('id', flat=True))
    qs_id_list += e_id_list

    # F = pokemon with a charge move that is SE against the defender,
    # and they are not weak to the defender's charge move, excluding E
    f_id_list = list(queryset.filter(
            stat_product__gte=550,
            pgo_attack__gte=200,
            cinematic_moves__move_type__in=defender_weakness,
        ).exclude(
            compound_weakness__icontains=defender_cm_move_type
        ).exclude(
            id__in=qs_id_list
        ).values_list('id', flat=True))
    qs_id_list += f_id_list

    # strong pokemon who are not weak to the defender's charge move
    g_id_list = list(queryset.filter(
            pgo_attack__gte=190,
            stat_product__gte=600,
        ).exclude(
            compound_weakness__icontains=defender_cm_move_type
        ).exclude(
            id__in=qs_id_list
        ).order_by(
            '-pgo_attack'
        ).values_list('id', flat=True)[:20])
    qs_id_list += g_id_list

    # strong pokemon with a charge or quick move that is SE against the defender
    h_id_list = list(queryset.filter(
            Q(
                Q(
                    pgo_attack__gte=190,
                    stat_product__gte=600
                ) | Q(
                    pgo_attack__gte=250,
                    stat_product__gte=550
                )) &
            Q(
                Q(cinematic_moves__move_type__in=defender_weakness) |
                Q(quick_moves__move_type__in=defender_weakness)
            )
        ).exclude(
            id__in=qs_id_list
        ).order_by(
            '-pgo_attack'
        ).values_list(
            'id', flat=True
        ).distinct()[:15])
    qs_id_list += h_id_list

    return queryset.filter(id__in=qs_id_list).prefetch_related(
        'moveset_set__quick_move__move__move_type',
        'moveset_set__cinematic_move__move__move_type',
    )
