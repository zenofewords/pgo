from __future__ import division

from decimal import Decimal
from math import floor

from django.db.models import Q, Max
from django.http import Http404
from django.utils.text import slugify

from pgo.models import Move, Pokemon, RaidBoss, TopCounter, Type, TypeEffectivness

SUPER_EFFECTIVE_SCALAR = 1.4
NOT_VERY_EFFECTIVE_SCALAR = 0.714
IMMUNE = 0.51
NEUTRAL_SCALAR = 1.0
STAB_SCALAR = 1.2
WEATHER_BOOST_SCALAR = 1.2
MAX_IV = 15
DEFAULT_EFFECTIVNESS = Decimal(str(NEUTRAL_SCALAR))


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
        power, attack_multiplier, stab, weather_boost, effectivness=1.0, friendship_boost=1.0):

    def _get_stab(stab):
        return STAB_SCALAR if stab else NEUTRAL_SCALAR

    def _get_weather_boost(weather_boost):
        return WEATHER_BOOST_SCALAR if weather_boost else NEUTRAL_SCALAR

    return int(floor(
        0.5 * power * float(attack_multiplier) * _get_stab(stab) * float(effectivness) *
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


def get_top_counter_qs(defender, weather_condition_id, defender_cpm):
    quick_move_type = defender.quick_move.move_type
    quick_move_resistance = quick_move_type.puny + quick_move_type.feeble
    quick_resisted_types = [slugify(x[0]) for x in quick_move_resistance]
    quick_resisted_type_ids = list(
        Type.objects.filter(slug__in=quick_resisted_types).values_list('id', flat=True)
    )
    quick_vulnerable_types = [slugify(x[0]) for x in quick_move_type.strong]
    quick_vulnerable_type_ids = list(Type.objects.filter(
        slug__in=quick_vulnerable_types).values_list('pk', flat=True)
    )

    cinematic_move_type = defender.cinematic_move.move_type
    cinematic_move_resistance = cinematic_move_type.puny + cinematic_move_type.feeble
    cinematic_resisted_types = [slugify(x[0]) for x in cinematic_move_resistance]
    cinematic_resisted_type_ids = list(
        Type.objects.filter(slug__in=cinematic_resisted_types).values_list('id', flat=True)
    )
    cinematic_vulnerable_types = [slugify(x[0]) for x in cinematic_move_type.strong]
    cinematic_vulnerable_type_ids = list(Type.objects.filter(
        slug__in=cinematic_vulnerable_types).values_list('pk', flat=True)
    )

    base_counter_qs = TopCounter.objects.filter(
        defender_id=defender.pk,
        defender_cpm=defender_cpm,
    ).exclude(
        counter__slug__in=['jirachi', 'celebi']
    )
    max_neutral_dps = base_counter_qs.filter(
        weather_condition_id=8
    ).aggregate(Max('highest_dps'))['highest_dps__max']

    # exclude if without resitance to c move and stats below treshold
    return base_counter_qs.filter(
        weather_condition_id=weather_condition_id
    ).exclude(
        (
            ~Q(counter__primary_type_id__in=cinematic_resisted_type_ids) & (
                (
                    Q(counter__secondary_type__isnull=False) &
                    ~Q(counter__secondary_type_id__in=cinematic_resisted_type_ids)
                ) | Q(counter__secondary_type__isnull=True)
            )
        ) & (
            Q(highest_dps__lte=max_neutral_dps * Decimal('0.7')) &
            Q(counter__pgo_attack__lte=210) &
            Q(counter__pgo_defense__lte=190)
        )
    ).exclude(  # double weak to c move and DPS below treshold
        (
            Q(counter__primary_type_id__in=cinematic_vulnerable_type_ids) &
            Q(counter__secondary_type_id__in=cinematic_vulnerable_type_ids)
        ) & Q(highest_dps__lte=max_neutral_dps * Decimal('0.9'))
    ).exclude(  # double weak to q move, DPS and HP below treshold
        (
            Q(counter__primary_type_id__in=quick_vulnerable_type_ids) &
            Q(counter__secondary_type_id__in=quick_vulnerable_type_ids)
        ) & (Q(highest_dps__lte=max_neutral_dps * Decimal('0.8')) & Q(counter_hp__lte=180))
    ).exclude(  # weak to both q and c, doesn't resist c move, DPS below treshold
        (
            Q(counter__primary_type_id__in=quick_vulnerable_type_ids) |
            Q(counter__secondary_type_id__in=quick_vulnerable_type_ids)
        ) &
        (
            (
                Q(counter__primary_type_id__in=cinematic_vulnerable_type_ids) |
                Q(counter__secondary_type_id__in=cinematic_vulnerable_type_ids)
            ) & (
                ~Q(counter__primary_type_id__in=cinematic_resisted_type_ids) &
                ~Q(counter__secondary_type_id__in=cinematic_resisted_type_ids)
            )
        ) & Q(highest_dps__lte=max_neutral_dps * Decimal('0.8'))
    ).exclude(  # weak to c move without resistance, DPS and HP below treshold
        ((
            Q(counter__primary_type_id__in=cinematic_vulnerable_type_ids) |
            Q(counter__secondary_type_id__in=cinematic_vulnerable_type_ids)
        ) & (
            ~Q(counter__primary_type_id__in=cinematic_resisted_type_ids) & (
                (
                    Q(counter__secondary_type__isnull=False) &
                    ~Q(counter__secondary_type_id__in=cinematic_resisted_type_ids)
                ) | Q(counter__secondary_type__isnull=True)
            )
        ) & (Q(highest_dps__lte=max_neutral_dps * Decimal('0.8')) & Q(counter_hp__lte=180)))
    ).exclude(  # weak to q move, DPS and HP below treshold
        (
            Q(counter__primary_type_id__in=quick_vulnerable_type_ids) |
            Q(counter__secondary_type_id__in=quick_vulnerable_type_ids)
        ) & (Q(highest_dps__lte=max_neutral_dps * Decimal('0.7')) & Q(counter_hp__lte=170))
    ).exclude(  # doesn't resist either move, stats below treshold
        (
            ~Q(counter__primary_type_id__in=cinematic_resisted_type_ids) & (
                (
                    Q(counter__secondary_type__isnull=False) &
                    ~Q(counter__secondary_type_id__in=cinematic_resisted_type_ids)
                ) | Q(counter__secondary_type__isnull=True)
            )
        ) & (
            ~Q(counter__primary_type_id__in=quick_resisted_type_ids) & (
                (
                    Q(counter__secondary_type__isnull=False) &
                    ~Q(counter__secondary_type_id__in=quick_resisted_type_ids)
                ) | Q(counter__secondary_type__isnull=True)
            )
        ) & (
            (
                Q(counter_hp__lte=120) &
                Q(counter__pgo_defense__lte=185) &
                Q(highest_dps__lte=max_neutral_dps * Decimal('0.97'))
            ) | (
                Q(counter_hp__lte=130) & Q(counter__pgo_defense__lte=150)
            ) | (
                Q(counter_hp__lte=130) &
                Q(highest_dps__lte=max_neutral_dps * Decimal('0.8'))
            ) | (
                (
                    Q(counter__pgo_defense__lte=150) |
                    Q(counter_hp__lte=150)
                ) & Q(highest_dps__lte=max_neutral_dps * Decimal('0.8'))
            )
        )
    ).exclude(  # HP below treshold and doesn't resist q move
        (
            ~Q(counter__primary_type_id__in=quick_resisted_type_ids) & (
                (
                    Q(counter__secondary_type__isnull=False) &
                    ~Q(counter__secondary_type_id__in=quick_resisted_type_ids)
                ) | Q(counter__secondary_type__isnull=True)
            )
        ) & Q(counter_hp__lte=100)
    ).order_by('-score')[:18]
