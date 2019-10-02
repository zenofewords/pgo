import six.moves.urllib as urllib
import copy
import logging

from collections import OrderedDict
from decimal import Decimal
from operator import itemgetter

from rest_framework import response, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.generics import GenericAPIView

from django.contrib.postgres.search import TrigramSimilarity
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.utils.text import slugify

from pgo.api.serializers import (
    BreakpointCalcSerializer, PokemonMoveSerializer, MoveSerializer,
    SimplePokemonSerializer, PokemonSerializer, TypeSerializer, GoodToGoSerializer,
)
from pgo.models import (
    CPM, PokemonMove, Move, Pokemon, Type, RaidBoss, RaidTier, WeatherCondition,
)
from pgo.utils import (
    calculate_dph,
    calculate_defender_health,
    calculate_cycle_dps,
    get_pokemon_data,
    get_move_data,
    get_top_counter_qs,
    determine_move_effectiveness,
    is_move_stab,
    MAX_IV,
)
logger = logging.getLogger(__name__)


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = 'page_size'
    max_page_size = 2000


class LargeResultModelViewSet(viewsets.ModelViewSet):
    pagination_class = LargeResultsSetPagination


class MoveViewSet(LargeResultModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Move.objects.select_related('move_type')
    serializer_class = MoveSerializer

    def get_queryset(self):
        if 'pokemon-id' in self.request.GET:
            try:
                query = int(self.request.GET.get('pokemon-id', 0))
            except ValueError:
                query = 0

            if query != 0:
                self.serializer_class = PokemonMoveSerializer
                qs = PokemonMove.objects.filter(pokemon_id=query)

                if self.request.GET.get('exclude-legacy') == 'true':
                    qs = qs.exclude(legacy=True)
                return qs
            else:
                return []
        else:
            return super().get_queryset()


class PokemonViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Pokemon.objects.select_related('primary_type', 'secondary_type')
    serializer_class = PokemonSerializer

    def get_queryset(self):
        if 'raid-boss-tier-group' in self.request.GET:
            try:
                raid_tier_ids = RaidBoss.objects.filter(
                    raid_tier=self.request.GET.get('raid-boss-tier-group')
                ).values_list('pokemon__id', flat=True)

                return self.queryset.filter(
                    id__in=raid_tier_ids
                ).select_related(
                    'primary_type', 'secondary_type'
                ).order_by('name')
            except ValueError:
                pass

        return super().get_queryset()


class TypeViewSet(LargeResultModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Type.objects.all()
    serializer_class = TypeSerializer


class PokemonSimpleViewSet(LargeResultModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Pokemon.objects.select_related('primary_type', 'secondary_type')
    serializer_class = SimplePokemonSerializer

    def get_queryset(self):
        pokemon_slug = slugify(self.request.GET.get('pokemon-slug', ''))

        if pokemon_slug:
            return self.queryset.annotate(
                similarity=TrigramSimilarity('slug', pokemon_slug)
            ).filter(
                similarity__gte=0.1
            ).order_by('-similarity')[:10]
        return super().get_queryset()


class BreakpointCalcAPIView(GenericAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = BreakpointCalcSerializer

    def get(self, request, *args, **kwargs):
        self.current_tab = request.GET.get('tab', 'breakpoints')
        self.show_cinematic_breakpoints = request.GET.get('show_cinematic_breakpoints', False)
        self.top_counter_order = request.GET.get('top_counter_order', False)

        serializer = self.get_serializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        self._fetch_data(serializer.data)
        self._set_move_parameters()
        self._set_defender_health()
        self._set_move_stats(self.attacker.cpm_list.first()['value'], self.attacker.atk_iv)

        data = {
            'top_counters': self._get_top_counters_data(),
            'attack_iv_assessment': self._assess_attack_iv(),
            'breakpoint_details': self._get_details_table(self._process_data()),
        }
        return response.Response(data, status=status.HTTP_200_OK)

    def _fetch_data(self, data):
        cpm_qs = CPM.gyms.all()
        self.max_cpm_value = cpm_qs.last().value

        attacker_id = data.get('attacker')
        defender_id = data.get('defender')
        if attacker_id == defender_id:
            pokemon = get_pokemon_data(attacker_id)
            self.attacker = pokemon
            self.defender = copy.deepcopy(pokemon)
        else:
            self.attacker = get_pokemon_data(data.get('attacker'))
            self.defender = get_pokemon_data(data.get('defender'))

        self.attacker.atk_iv = data.get('attacker_atk_iv')
        self.attacker.level = data.get('attacker_level')
        self.attacker.cpm = cpm_qs.get(level=self.attacker.level)
        self.attacker.cpm_list = cpm_qs.filter(level__gte=self.attacker.level).values(
            'level', 'value', 'total_stardust_cost', 'total_candy_cost')

        self.defender.defense_iv = data.get('defense_iv', MAX_IV)
        self.defender.cpm = Decimal(data.get('defender_cpm')[:11])

        attacker_qk_move_id = data.get('attacker_quick_move')
        defender_qk_move_id = data.get('defender_quick_move')
        if attacker_qk_move_id == defender_qk_move_id:
            quick_move = get_move_data(attacker_qk_move_id)
            self.attacker_quick_move = quick_move
            self.defender.quick_move = copy.deepcopy(quick_move)
        else:
            self.attacker_quick_move = get_move_data(attacker_qk_move_id)
            self.defender.quick_move = get_move_data(defender_qk_move_id)

        attacker_cc_move_id = data.get('attacker_cinematic_move')
        defender_cc_move_id = data.get('defender_cinematic_move')
        if attacker_cc_move_id == defender_cc_move_id:
            cinematic_move = get_move_data(attacker_cc_move_id)
            self.attacker_cinematic_move = cinematic_move
            self.defender.cinematic_move = copy.deepcopy(cinematic_move)
        else:
            self.attacker_cinematic_move = get_move_data(attacker_cc_move_id)
            self.defender.cinematic_move = get_move_data(defender_cc_move_id)

        self.friendship_boost = data.get('friendship_boost', 1.00)
        self.raid_tier = None
        raid_tier = int(data.get('defender_cpm')[11:12])
        if raid_tier:
            self.raid_tier = RaidTier.objects.get(tier=raid_tier)

        self.boosted_types = []
        if data.get('weather_condition', 0) > 0:
            self.weather_condition = get_object_or_404(
                WeatherCondition.objects, pk=data.get('weather_condition'))
            self.boosted_types = list(
                self.weather_condition.types_boosted.values_list('pk', flat=True))

    def _process_data(self):
        attacker_starting_cpm = self.attacker.cpm_list.first()

        self._set_move_stats(attacker_cpm=attacker_starting_cpm['value'])
        starting_qk_dph = self.attacker_quick_move.damage_per_hit
        starting_cc_dph = self.attacker_cinematic_move.damage_per_hit

        self.perfect_max_dps = calculate_cycle_dps(
            self._get_max_damage_move(self.attacker_quick_move, attack_iv=MAX_IV),
            self._get_max_damage_move(self.attacker_cinematic_move, attack_iv=MAX_IV)
        )

        self.quick_move_proficiency = []
        self.cinematic_move_proficiency = []
        self.stardust_cost = attacker_starting_cpm['total_stardust_cost']
        self.candy_cost = attacker_starting_cpm['total_candy_cost']

        self._set_quick_move_proficiency(starting_qk_dph)
        self._set_cinematic_move_proficiency(
            starting_cc_dph,
            self._get_max_damage_move(self.attacker_cinematic_move).damage_per_hit
        )
        return starting_qk_dph

    def _set_move_parameters(self):
        self.attacker_quick_move.stab = is_move_stab(
            self.attacker_quick_move, self.attacker)
        self.attacker_cinematic_move.stab = is_move_stab(
            self.attacker_cinematic_move, self.attacker)

        self.attacker_quick_move.effectiveness = determine_move_effectiveness(
            self.attacker_quick_move.move_type, self.defender)
        self.attacker_cinematic_move.effectiveness = determine_move_effectiveness(
            self.attacker_cinematic_move.move_type, self.defender)

        self.attacker_quick_move.weather_boosted = \
            self.attacker_quick_move.move_type_id in self.boosted_types
        self.attacker_cinematic_move.weather_boosted = \
            self.attacker_cinematic_move.move_type_id in self.boosted_types

    def _set_defender_health(self):
        stamina = self.defender.pgo_stamina
        if self.raid_tier:
            self.defender.health = self.raid_tier.tier_stamina
        else:
            self.defender.health = calculate_defender_health(stamina + MAX_IV, self.defender.cpm)

    def _assess_attack_iv(self):
        self._set_move_stats(attack_iv=self.attacker.atk_iv)
        current_qk_dph = self.attacker_quick_move.damage_per_hit
        self._set_move_stats(attack_iv=MAX_IV)

        dph_match = current_qk_dph == self.attacker_quick_move.damage_per_hit
        params = (
            self.attacker.name,
            'high enough' if dph_match else 'too low',
            self.attacker_quick_move.name,
            self.attacker_quick_move.damage_per_hit,
            'tier {} raid boss'.format(
                self.raid_tier.tier) if self.raid_tier else 'level 40, 15 defense IV',
            self.defender.name,
        )
        return '<p>Your {}\'s <b>attack IV is {}</b> for it to reach the final {} breakpoint ({})\
                against a <b>{} {}</b>.</p>'.format(*params)

    def _set_move_stats(self, attacker_cpm=None, attack_iv=None):
        self._calculate_attack_multiplier(attacker_cpm, attack_iv)
        self._set_move_damage(self.attacker_quick_move)
        self._set_move_damage(self.attacker_cinematic_move)

    def _calculate_attack_multiplier(self, attacker_cpm=None, attack_iv=None):
        if not attacker_cpm:
            attacker_cpm = self.max_cpm_value
        if not attack_iv:
            attack_iv = self.attacker.atk_iv

        self.attack_multiplier = (
            (self.attacker.pgo_attack + attack_iv) * attacker_cpm) / (
            (self.defender.pgo_defense + self.defender.defense_iv) * self.defender.cpm)

    def _set_move_damage(self, move):
        move.damage_per_hit = calculate_dph(
            move.power,
            self.attack_multiplier,
            move.stab,
            move.weather_boosted,
            move.effectiveness,
            self.friendship_boost
        )

    def _get_max_damage_move(self, move, attack_iv=None):
        self._calculate_attack_multiplier(attack_iv=attack_iv)
        self._set_move_damage(move)
        return move

    def _set_quick_move_proficiency(self, starting_qk_dph):
        current_qk_dph = starting_qk_dph
        current_cpm = self.attacker.cpm_list[0]

        # include current level
        self.quick_move_proficiency.append((
            starting_qk_dph,
            current_cpm['level'],
            current_cpm['value'],
            current_cpm['total_stardust_cost'],
            current_cpm['total_candy_cost'],
        ))

        for cpm in self.attacker.cpm_list:
            self._calculate_attack_multiplier(cpm['value'])
            self._set_move_damage(self.attacker_quick_move)

            if current_qk_dph < self.attacker_quick_move.damage_per_hit:
                self.quick_move_proficiency.append((
                    self.attacker_quick_move.damage_per_hit,
                    cpm['level'],
                    cpm['value'],
                    cpm['total_stardust_cost'],
                    cpm['total_candy_cost'],
                ))
                current_qk_dph = self.attacker_quick_move.damage_per_hit

    def _set_cinematic_move_proficiency(self, starting_cc_dph, max_cc_dph):
        current_cc_dph = starting_cc_dph

        if starting_cc_dph == max_cc_dph:
            return

        for index, cpm in enumerate(self.attacker.cpm_list):
            self._calculate_attack_multiplier(cpm['value'])
            self._set_move_damage(self.attacker_cinematic_move)

            show_all_cc_breakpoints = (
                self.show_cinematic_breakpoints
                and current_cc_dph < self.attacker_cinematic_move.damage_per_hit
            )
            if (
                [x for x in self.quick_move_proficiency if cpm['value'] == x[2]]
                or show_all_cc_breakpoints
                or self.attacker_cinematic_move.damage_per_hit == max_cc_dph
            ):
                self.cinematic_move_proficiency.append((
                    self.attacker_cinematic_move.damage_per_hit,
                    cpm['level'],
                    cpm['value'],
                    cpm['total_stardust_cost'],
                    cpm['total_candy_cost'],
                ))
                current_cc_dph = self.attacker_cinematic_move.damage_per_hit

    def _get_details_table(self, starting_qk_dph):
        details = []

        self.battle_duration = self.raid_tier.battle_duration if self.raid_tier else 99
        for c in sorted(self.cinematic_move_proficiency):
            for q in sorted(self.quick_move_proficiency):
                if q[1] == c[1]:
                    starting_qk_dph = q[0]

            # skip redundant rows
            if (starting_qk_dph, c[0]) in [(x[2], x[3]) for x in details[1:]]:
                continue

            self.attacker_quick_move.damage_per_hit = starting_qk_dph
            self.attacker_cinematic_move.damage_per_hit = c[0]

            cycle_dps = calculate_cycle_dps(
                self.attacker_quick_move, self.attacker_cinematic_move)
            details.append(self._get_detail_row(
                c[1], cycle_dps,
                self._trainers_required(cycle_dps), c[3], c[4]))

        # edge case when there's improvement for quick moves, but not for cinematic
        if len(self.cinematic_move_proficiency) == 0 and len(self.quick_move_proficiency) > 0:
            for q in sorted(self.quick_move_proficiency):
                self.attacker_quick_move.damage_per_hit = q[0]

                cycle_dps = calculate_cycle_dps(
                    self.attacker_quick_move, self.attacker_cinematic_move)
                details.append(self._get_detail_row(
                    q[1], cycle_dps,
                    self._trainers_required(cycle_dps), q[3], q[4]))
        return details

    def _trainers_required(self, cycle_dps):
        return self.defender.health / self.battle_duration / (cycle_dps / 1.10)

    def _get_detail_row(self, level, cycle_dps, trainers_required, stardust_cost, candy_cost):
        return ('{:g}'.format(float(level)), self._format_powerup_cost(stardust_cost, candy_cost),
                self.attacker_quick_move.damage_per_hit,
                self.attacker_cinematic_move.damage_per_hit,
                self._format_dps(cycle_dps), '{:.2f}'.format(trainers_required))

    def _format_powerup_cost(self, stardust_cost, candy_cost):
        if stardust_cost - self.stardust_cost == 0 and candy_cost - self.candy_cost == 0:
            return '- | -'

        return '{:g}k | {}'.format(
            (stardust_cost - self.stardust_cost) / 1000,
            (candy_cost - self.candy_cost)
        )

    def _format_dps(self, cycle_dps):
        self.cycle_dps = cycle_dps
        dps_percentage = self.cycle_dps * 100 / self.perfect_max_dps
        return '{:g} ({:g}%)'.format(round(cycle_dps, 1), round(dps_percentage, 1))

    def _get_top_counters_data(self):
        if self.current_tab != 'counters':
            return {}

        top_counters = []
        for pokemon in get_top_counter_qs(self.defender):
            attacker_multiplier = (
                (pokemon.pgo_attack + self.attacker.atk_iv) * self.attacker.cpm.value) / (
                (self.defender.pgo_defense + MAX_IV) * self.defender.cpm)
            defender_multiplier = (
                (self.defender.pgo_attack + MAX_IV) * self.defender.cpm) / (
                (pokemon.pgo_defense + MAX_IV) * self.max_cpm_value)

            moveset_data = []
            for moveset in pokemon.moveset_set.all():
                quick_move = moveset.quick_move.move
                cinematic_move = moveset.cinematic_move.move

                quick_move.damage_per_hit = calculate_dph(
                    quick_move.power,
                    attacker_multiplier,
                    moveset.quick_move.stab,
                    quick_move.move_type_id in self.boosted_types,
                    determine_move_effectiveness(
                        moveset.quick_move.move_type.title(), self.defender
                    ),
                    self.friendship_boost
                )
                cinematic_move.damage_per_hit = calculate_dph(
                    cinematic_move.power,
                    attacker_multiplier,
                    moveset.cinematic_move.stab,
                    cinematic_move.move_type_id in self.boosted_types,
                    determine_move_effectiveness(
                        moveset.cinematic_move.move_type.title(), self.defender
                    ),
                    self.friendship_boost
                )
                dps = calculate_cycle_dps(quick_move, cinematic_move)
                moveset_data.append((
                    moveset.quick_move.move.name,
                    moveset.cinematic_move.move.name,
                    round(dps, 1),
                    moveset.cinematic_move.move.energy_delta
                ))

            moveset_data = sorted(moveset_data, key=itemgetter(2), reverse=True)[:20]
            top_counters.append((
                self._get_top_counter_url(pokemon, moveset_data[0]),
                moveset_data,
                moveset_data[0][2],
                self._get_score(pokemon, defender_multiplier, moveset_data)
            ))
        return sorted(top_counters, key=itemgetter(3), reverse=True)[:30]

    def _get_score(self, pokemon, defender_multiplier, moveset_data):
        dps = moveset_data[0][2]
        if self.top_counter_order == 'dps':
            return dps

        quick_move_dph = calculate_dph(
            self.defender.quick_move.power,
            defender_multiplier,
            is_move_stab(self.defender.quick_move, self.defender),
            self.defender.quick_move.move_type_id in self.boosted_types,
            determine_move_effectiveness(self.defender.quick_move.move_type, pokemon),
        )
        cinematic_move_dph = calculate_dph(
            self.defender.cinematic_move.power,
            defender_multiplier,
            is_move_stab(self.defender.cinematic_move, self.defender),
            self.defender.cinematic_move.move_type_id in self.boosted_types,
            determine_move_effectiveness(self.defender.cinematic_move.move_type, pokemon),
        )
        health = int((pokemon.pgo_stamina + MAX_IV) * self.max_cpm_value)
        score = dps * 20
        score += pokemon.bulk / 800

        cinematic_move_resisted = pokemon.compound_resistance.get(
            self.defender.cinematic_move.move_type.name)
        if cinematic_move_resisted:
            score += 60 if float(cinematic_move_resisted) < 0.4 else 20

        quick_move_resisted = pokemon.compound_resistance.get(
            self.defender.quick_move.move_type.name)
        if quick_move_resisted:
            score += 30 if float(quick_move_resisted) < 0.4 else 20

        cinematic_move_amplified = pokemon.compound_weakness.get(
            self.defender.cinematic_move.move_type.name)
        if cinematic_move_amplified:
            score -= 60 if float(cinematic_move_amplified) > 2.5 else 20

        quick_move_amplified = pokemon.compound_weakness.get(
            self.defender.quick_move.move_type.name)
        if quick_move_amplified:
            score -= 30 if float(quick_move_amplified) > 2.5 else 20

        if moveset_data[0][3] == -100:
            score -= 20
        elif moveset_data[0][3] == -33:
            score += 10

        quick_move_threshold = 2 if self.defender.quick_move.duration > 1000 else 3
        cm_energy_delta = self.defender.cinematic_move.energy_delta
        if cm_energy_delta == -100 or cm_energy_delta == -50:
            if health - cinematic_move_dph < 0:
                score += cm_energy_delta * 1.5
            elif health - (cinematic_move_dph + quick_move_dph) < 0:
                score += cm_energy_delta * 1.5
            elif health - (cinematic_move_dph + quick_move_threshold * quick_move_dph) < 0:
                score += cm_energy_delta * 1.5
        else:
            treshold = cinematic_move_dph * 2 + quick_move_threshold * quick_move_dph
            if health - treshold < 0 or health - quick_move_dph * 5 < 0:
                score -= 70
        return score

    def _get_top_counter_url(self, pokemon, moveset_data):
        params = urllib.parse.urlencode({
            'attacker': pokemon.slug,
            'attacker_level': self.attacker.cpm.level,
            'attacker_quick_move': moveset_data[0],
            'attacker_cinematic_move': moveset_data[1],
            'attacker_atk_iv': self.attacker.atk_iv,
            'weather_condition': self.weather_condition.pk,
            'friendship_boost': self.friendship_boost,
            'defender': self.defender.slug,
            'defender_quick_move': self.defender.quick_move.slug,
            'defender_cinematic_move': self.defender.cinematic_move.slug,
            'defender_cpm': '{}{}'.format(
                self.defender.cpm,
                self.raid_tier.tier if self.raid_tier else 0
            ),
            'tab': 'breakpoints',
        })
        return '<a href="{0}?{1}">{2}</a>'.format(
            reverse('pgo:breakpoint-calc'), params, pokemon.name,
        )


class GoodToGoAPIView(GenericAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = GoodToGoSerializer

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        self._fetch_data(serializer.data)
        return response.Response(self._process_data(), status=status.HTTP_200_OK)

    def _fetch_data(self, data):
        self.attacker = get_object_or_404(Pokemon, pk=data.get('attacker'))
        self.quick_move = get_object_or_404(Move, pk=data.get('quick_move'))
        self.cinematic_move = get_object_or_404(Move, pk=data.get('cinematic_move'))
        self.boosted_types = list(get_object_or_404(WeatherCondition, pk=data.get(
            'weather_condition')).types_boosted.values_list('pk', flat=True))
        self.attack_iv = data.get('attack_iv')
        self.friendship_boost = data.get('friendship_boost', 1.00)

        self.tier_3_6_raid_bosses = RaidBoss.objects.filter(
            raid_tier__tier__in=[3, 4, 5, 6]
        ).order_by('-raid_tier', '-pokemon__slug') if data.get('tier_3_6_raid_bosses') else []

        self.tier_1_2_raid_bosses = RaidBoss.objects.filter(
            raid_tier__tier__in=[1, 2]
        ).order_by('-raid_tier', '-pokemon__slug') if data.get('tier_1_2_raid_bosses') else []

        self.max_cpm_value = CPM.gyms.last().value

    def _process_data(self):
        total_breakpoints = 0
        total_breakpoints_reached = 0

        self.matchup_data = OrderedDict()
        for defender in self.tier_3_6_raid_bosses:
            self._get_breakpoint_data(defender)

        tier_3_6 = []
        for key, value in self.matchup_data.items():
            breakpoints_reached = sum(
                [1 if x['final_breakpoint_reached'] is True else 0 for x in value])

            tier_3_6.append({
                'tier': key,
                'quick_move': self.quick_move.name,
                'final_breakpoints_reached': breakpoints_reached,
                'total_breakpoints': len(value),
                'matchups': [x for x in sorted(
                    value, key=itemgetter('final_breakpoint_reached'), reverse=True)
                ],
            })
            total_breakpoints += len(value)
            total_breakpoints_reached += breakpoints_reached

        self.matchup_data = OrderedDict()
        for defender in self.tier_1_2_raid_bosses:
            self._get_breakpoint_data(defender)

        tier_1_2 = []
        for key, value in self.matchup_data.items():
            breakpoints_reached = sum(
                [1 if x['final_breakpoint_reached'] is True else 0 for x in value])

            tier_1_2.append({
                'tier': key,
                'quick_move': self.quick_move.name,
                'final_breakpoints_reached': breakpoints_reached,
                'total_breakpoints': len(value),
                'matchups': [x for x in sorted(
                    value, key=itemgetter('final_breakpoint_reached'), reverse=True)
                ],
            })
            total_breakpoints += len(value)
            total_breakpoints_reached += breakpoints_reached

        return {
            'tier_3_6_raid_bosses': tier_3_6,
            'tier_1_2_raid_bosses': tier_1_2,
            'summary': self._get_summary(total_breakpoints_reached, total_breakpoints)
        }

    def _get_breakpoint_data(self, defender):
        stab = is_move_stab(self.quick_move, self.attacker)
        weather_boosted = self.quick_move.move_type_id in self.boosted_types
        effectiveness = determine_move_effectiveness(self.quick_move.move_type, defender)
        max_multiplier = self._get_attack_multiplier(MAX_IV, defender)

        max_damage_per_hit = calculate_dph(
            self.quick_move.power, max_multiplier, stab,
            weather_boosted, effectiveness, self.friendship_boost
        )

        actual_multiplier = self._get_attack_multiplier(self.attack_iv, defender)
        actual_damage_per_hit = calculate_dph(
            self.quick_move.power, actual_multiplier, stab,
            weather_boosted, effectiveness, self.friendship_boost
        )

        tier = defender.raid_tier.tier
        matchup_stats = {
            'defender': defender.pokemon.name,
            'quick_move': self.quick_move.name,
            'damage_per_hit': actual_damage_per_hit,
            'max_damage_per_hit': max_damage_per_hit,
            'final_breakpoint_reached': actual_damage_per_hit == max_damage_per_hit
        }

        if tier in self.matchup_data:
            self.matchup_data[tier].append(matchup_stats)
        else:
            self.matchup_data[tier] = [matchup_stats]

    def _get_summary(self, total_breakpoints_reached, total_breakpoints):
        return '''
            <p>Your {} can reach the final {} breakpoint in <b>{} / {}</b> tested matchups.</p>
            '''.format(
            self.attacker.name, self.quick_move.name, total_breakpoints_reached, total_breakpoints
        )

    def _get_attack_multiplier(self, attack_iv, defender):
        return ((self.attacker.pgo_attack + attack_iv) * self.max_cpm_value) / (
            (defender.pokemon.pgo_defense + MAX_IV) * defender.raid_tier.raid_cpm.value)
