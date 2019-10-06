from collections import OrderedDict
from decimal import Decimal
from math import floor, pow, sqrt

from django.db.models import Q
from django.http import Http404
from django.template.defaultfilters import slugify

from pgo.models import (
    CPM,
    Move,
    Moveset,
    Pokemon,
    PokemonMove,
    RaidBoss,
    Type,
)

NEUTRAL_SCALAR = 1.0
STAB_SCALAR = 1.2
WEATHER_BOOST_SCALAR = 1.2
MAX_IV = 15
LEVELS = (20.0, 25.0, 30.0, 35.0, 40.0)
cpm = CPM.gyms.get(level=Decimal('40.0')).value
NAVIGATION_ITEM_MAP = (
    ('/breakpoint-calc/', 'Breakpoint calculator',),
    ('/good-to-go/', 'Good to go',),
    ('/pokemon/', 'Pokemon',),
    ('/moves/', 'Moves',),
)
TIER_CPM_MAP = (
    (6, '0.790000000',),
    (5, '0.790000000',),
    (4, '0.790000000',),
    (3, '0.730000000',),
    (2, '0.670000000',),
    (1, '0.597400000',),
    (40, '0.790300000',),
)


def get_navigation_items():
    navigation_items = OrderedDict()
    for nav_item in NAVIGATION_ITEM_MAP:
        navigation_items[nav_item[0]] = nav_item[1]
    return navigation_items


def get_tier_cpm_map():
    tier_cpm_map = OrderedDict()
    for tc in TIER_CPM_MAP:
        tier_cpm_map[tc[0]] = tc[1]
    return tier_cpm_map


def get_stab(stab):
    return STAB_SCALAR if stab else NEUTRAL_SCALAR


def is_stab(pokemon, move_type):
    return move_type in (pokemon.primary_type, pokemon.secondary_type)


def calculate_move_stats(move):
    move.dps = move.power / (move.duration / 1000.0)
    move.eps = move.energy_delta / (move.duration / 1000.0)
    move.save()


def calculate_pokemon_stats(pokemon):
    attack = pokemon.pgo_attack + MAX_IV
    defense = pokemon.pgo_defense + MAX_IV
    stamina = pokemon.pgo_stamina + MAX_IV

    pokemon.maximum_cp = attack * sqrt(defense) * sqrt(stamina) * pow(cpm, 2) / 10.0
    pokemon.stat_sum = pokemon.pgo_attack + pokemon.pgo_defense + pokemon.pgo_stamina
    pokemon.stat_product = pokemon.pgo_attack * pokemon.pgo_defense * pokemon.pgo_stamina
    pokemon.bulk = pokemon.pgo_defense * pokemon.pgo_stamina
    return pokemon


def calculate_weave_damage(pokemon):
    def get_moveset(pokemon, quick_move, cinematic_move):
        return Moveset.objects.filter(
            pokemon=pokemon,
            key='{} - {}'.format(quick_move.name, cinematic_move.name)
        ).first()

    def get_base_attack(attack, level):
        return float((attack + MAX_IV) * CPM.gyms.get(level=level).value)

    def calculate_dph(power, attack, stab):
        return floor(0.5 * power * attack * stab) + 1

    def calculate_weave(attack, qk_move, cc_move, stab):
        weave_damage = {}

        for level in LEVELS:
            base_attack = get_base_attack(attack, level)
            qk_move.damage_per_hit = calculate_dph(qk_move.power, base_attack, get_stab(stab[0]))
            cc_move.damage_per_hit = calculate_dph(cc_move.power, base_attack, get_stab(stab[1]))

            cycle_dps = calculate_cycle_dps(qk_move, cc_move)

            weave_damage[level] = cycle_dps
        return weave_damage

    for quick_move in pokemon.quick_moves.all():
        stab = [False, False]
        stab[0] = is_stab(pokemon, quick_move.move.move_type)

        for cinematic_move in pokemon.cinematic_moves.all():
            stab[1] = is_stab(pokemon, cinematic_move.move.move_type)
            moveset = get_moveset(pokemon, quick_move.move, cinematic_move.move)

            if moveset:
                moveset.weave_damage = sorted(calculate_weave(
                    pokemon.pgo_attack, quick_move.move, cinematic_move.move, stab).items()
                )
                moveset.save()


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

    def _get_weather_boost(weather_boost):
        return WEATHER_BOOST_SCALAR if weather_boost else NEUTRAL_SCALAR

    return int(floor(
        0.5 * power * float(attack_multiplier) * get_stab(stab) * float(effectiveness)
        * _get_weather_boost(weather_boost) * float(friendship_boost))
    ) + 1


def calculate_pokemon_move_score(moveset):
    def update_or_create_pokemon_move(moveset, move):
        pokemon = moveset.pokemon
        new_score = Decimal(moveset.weave_damage[4][1] / 100)

        obj, created = PokemonMove.objects.get_or_create(
            pokemon=pokemon,
            move=move,
            defaults={
                'stab': is_stab(pokemon, move.move_type),
                'score': new_score,
            }
        )
        if not created and obj.pokemon == pokemon:
            obj.stab = is_stab(pokemon, move.move_type)
            obj.score = new_score if new_score > obj.score else obj.score
            obj.save()
        return obj

    moves = moveset.key.split(' - ', 1)
    update_or_create_pokemon_move(moveset, Move.objects.get(slug=slugify(moves[0])))
    update_or_create_pokemon_move(moveset, Move.objects.get(slug=slugify(moves[1])))


def calculate_health(total_stamina, cpm):
    return int(floor(total_stamina * cpm))


def calculate_defender_health(total_stamina, cpm):
    return calculate_health(total_stamina, cpm) * 2


def calculate_defense(total_defense, cpm):
    return int(floor(total_defense * cpm))


def get_pokemon_data(slug):
    try:
        return Pokemon.objects.get(slug=slug)
    except Pokemon.DoesNotExist:
        raise Http404


def get_move_data(id):
    try:
        return Move.objects.select_related('move_type').get(pk=id)
    except Move.DoesNotExist:
        raise Http404


def determine_move_effectiveness(move_type, pokemon):
    if isinstance(pokemon, RaidBoss):
        pokemon = pokemon.pokemon

    if isinstance(move_type, Type):
        move_type = move_type.name

    effectiveness = 1.0
    if pokemon.compound_resistance.get(move_type):
        effectiveness = pokemon.compound_resistance[move_type]
    if pokemon.compound_weakness.get(move_type):
        effectiveness = pokemon.compound_weakness[move_type]
    return effectiveness


def is_move_stab(move, pokemon):
    return (
        pokemon.primary_type_id == move.move_type_id
        or pokemon.secondary_type_id == move.move_type_id
    )


def get_top_counter_qs(defender):
    defender_weakness = [x.lower() for x in defender.compound_weakness.keys()]
    defender_resistance = [x.lower() for x in defender.compound_resistance.keys()]
    defender_qk_move_type = defender.quick_move.move_type
    defender_cm_move_type = defender.cinematic_move.move_type
    queryset = Pokemon.objects.implemented().filter(
        stat_sum__gte=500,
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
        stat_sum__gte=510
    ).exclude(
        id__in=qs_id_list
    ).values_list('id', flat=True))
    qs_id_list += a_id_list

    # B = pokemon with a charge move that is SE against the defender, their quick move is not
    # resisted, and they resist the defender’s quick and charge move, excluding A
    b_id_list = list(queryset.filter(
        Q(cinematic_moves__move_type__in=defender_weakness)
        & Q(compound_resistance__icontains=defender_qk_move_type)
        & Q(compound_resistance__icontains=defender_cm_move_type)
        & Q(stat_sum__gte=530)
    ).exclude(
        quick_moves__move_type__in=defender_resistance
    ).exclude(
        id__in=qs_id_list
    ).values_list('id', flat=True))
    qs_id_list += b_id_list

    # C = pokemon with a charge move that is SE against the defender, their quick move is not
    # resisted, and they resist the defender’s charge move, excluding B
    c_id_list = list(queryset.filter(
        cinematic_moves__move_type__in=defender_weakness,
        compound_resistance__icontains=defender_cm_move_type,
        stat_sum__gte=550
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
        stat_sum__gte=570
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
        stat_sum__gte=550,
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
        stat_sum__gte=600,
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
                stat_sum__gte=600
            ) | Q(
                pgo_attack__gte=250,
                stat_sum__gte=550
            ))
        & Q(
            Q(cinematic_moves__move_type__in=defender_weakness)
            | Q(quick_moves__move_type__in=defender_weakness)
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
        'moveset_set__quick_move__move',
        'moveset_set__cinematic_move__move',
    )
