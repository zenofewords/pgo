from __future__ import division, unicode_literals

import six.moves.urllib as urllib

from collections import OrderedDict
from decimal import Decimal

from rest_framework import response, status, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.generics import GenericAPIView

from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.text import slugify

from pgo.api.serializers import (
    BreakpointCalcSerializer, PokemonMoveSerializer, MoveSerializer,
    PokemonSerializer, TypeSerializer, GoodToGoSerializer,
)
from pgo.models import (
    CPM, PokemonMove, Move, Pokemon, Type, RaidBoss, WeatherCondition, RaidBossStatus, TopCounter,
)
from pgo.utils import (
    calculate_dph,
    calculate_defender_health,
    calculate_weave_damage,
    get_pokemon_data,
    get_move_data,
    determine_move_effectivness,
    is_move_stab,
    CINEMATIC_MOVE_FACTOR,
    MAX_IV,
)


class MoveViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Move.objects.all()
    serializer_class = MoveSerializer

    def get_queryset(self):
        if 'pokemon-id' in self.request.GET:
            query = int(self.request.GET.get('pokemon-id', 0))

            if query != 0:
                self.serializer_class = PokemonMoveSerializer
                return PokemonMove.objects.filter(
                    Q(pokemon_id=query) &
                    (
                        Q(move__quick_moves_pokemon__id=query) |
                        Q(move__cinematic_moves_pokemon__id=query)
                    )
                )
            else:
                return []
        else:
            return super(MoveViewSet, self).get_queryset()


class PokemonViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Pokemon.objects.all()
    serializer_class = PokemonSerializer

    def get_queryset(self):
        if 'raid-boss-tier-group' in self.request.GET:
            raid_tier_ids = RaidBoss.objects.filter(
                raid_tier=self.request.GET.get('raid-boss-tier-group')
            ).values_list('pokemon__id', flat=True)

            return self.queryset.filter(id__in=raid_tier_ids).order_by('name')
        return super(PokemonViewSet, self).get_queryset()


class TypeViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Type.objects.all()
    serializer_class = TypeSerializer


class BreakpointCalcAPIView(GenericAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = BreakpointCalcSerializer

    def get(self, request, *args, **kwargs):
        self.show_cinematic_breakpoints = request.GET.get('show_cinematic_breakpoints')

        serializer = self.get_serializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        self._fetch_data(serializer.data)
        self._set_move_parameters()
        self._set_defender_health()
        self._set_move_stats(self.attacker.cpm_list.first()['value'], self.attacker.atk_iv)

        data = {
            'top_counters': self._get_top_counters(),
            'attack_iv_assessment': self._assess_attack_iv(),
            'breakpoint_details': self._get_details_table(self._process_data()),
        }
        return response.Response(data, status=status.HTTP_200_OK)

    def _fetch_data(self, data):
        cpm_qs = CPM.gyms.all()
        self.max_cpm_value = cpm_qs.last().value

        self.attacker = get_pokemon_data(data.get('attacker'))
        self.attacker.atk_iv = data.get('attacker_atk_iv')
        self.attacker.level = data.get('attacker_level')
        self.attacker.cpm_list = cpm_qs.filter(level__gte=self.attacker.level).values(
            'level', 'value', 'total_stardust_cost', 'total_candy_cost')
        self.quick_move = get_move_data(data.get('quick_move'))
        self.cinematic_move = get_move_data(data.get('cinematic_move'))
        self.defender = get_pokemon_data(data.get('defender'))
        self.defender.defense_iv = data.get('defense_iv', MAX_IV)
        self.defender.cpm = Decimal(data.get('defender_cpm')[:11])
        self.raid_tier = int(data.get('defender_cpm')[11:12])

        self.boosted_types = []
        if data.get('weather_condition', 0) > 0:
            self.weather_condition = get_object_or_404(
                WeatherCondition.objects, pk=data.get('weather_condition'))
            self.boosted_types = list(
                self.weather_condition.types_boosted.values_list('pk', flat=True))

    def _process_data(self):
        attacker_starting_cpm = self.attacker.cpm_list.first()

        self._set_move_stats(attacker_cpm=attacker_starting_cpm['value'])
        starting_qk_dph = self.quick_move.damage_per_hit
        starting_cc_dph = self.cinematic_move.damage_per_hit

        self.perfect_max_dps, _ = calculate_weave_damage(
            self._get_max_damage_move(self.quick_move, attack_iv=MAX_IV),
            self._get_max_damage_move(self.cinematic_move, attack_iv=MAX_IV)
        )

        self.quick_move_proficiency = []
        self.cinematic_move_proficiency = []
        self.stardust_cost = attacker_starting_cpm['total_stardust_cost']
        self.candy_cost = attacker_starting_cpm['total_candy_cost']

        self._set_quick_move_proficiency(starting_qk_dph)
        self._set_cinematic_move_proficiency(
            starting_cc_dph,
            self._get_max_damage_move(self.cinematic_move).damage_per_hit
        )
        return starting_qk_dph

    def _set_move_parameters(self):
        self.quick_move.stab = is_move_stab(self.quick_move, self.attacker)
        self.cinematic_move.stab = is_move_stab(self.cinematic_move, self.attacker)

        self.quick_move.effectivness = determine_move_effectivness(self.quick_move, self.defender)
        self.cinematic_move.effectivness = determine_move_effectivness(
            self.cinematic_move, self.defender)

        self.quick_move.weather_boosted = self.quick_move.move_type_id in self.boosted_types
        self.cinematic_move.weather_boosted = self.cinematic_move.move_type_id in self.boosted_types

    def _set_defender_health(self):
        stamina = self.defender.pgo_stamina
        if self.raid_tier:
            stamina = self.defender.raidboss_set.get(raid_tier=self.raid_tier).raid_tier.tier_stamina
        self.defender.health = calculate_defender_health(stamina + MAX_IV, self.defender.cpm)

    def _assess_attack_iv(self):
        self._set_move_stats(attack_iv=self.attacker.atk_iv)
        current_qk_dph = self.quick_move.damage_per_hit
        self._set_move_stats(attack_iv=MAX_IV)

        params = (
            self.attacker.name,
            'high enough' if current_qk_dph == self.quick_move.damage_per_hit else 'too low',
            self.quick_move.name,
            self.quick_move.damage_per_hit,
            'tier {} raid boss'.format(self.raid_tier) if self.raid_tier else 'level 40, 15 defense IV',
            self.defender.name,
        )
        return 'Your {}\'s <b>attack IV is {}</b> for it to reach the final {} breakpoint ({})\
                against a {} {}.'.format(*params)

    def _set_move_stats(self, attacker_cpm=None, attack_iv=None):
        self._calculate_attack_multiplier(attacker_cpm, attack_iv)
        self._set_move_damage(self.quick_move)
        self._set_move_damage(self.cinematic_move)

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
            move.effectivness
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
            self._set_move_damage(self.quick_move)

            if current_qk_dph < self.quick_move.damage_per_hit:
                self.quick_move_proficiency.append((
                    self.quick_move.damage_per_hit,
                    cpm['level'],
                    cpm['value'],
                    cpm['total_stardust_cost'],
                    cpm['total_candy_cost'],
                ))
                current_qk_dph = self.quick_move.damage_per_hit

    def _set_cinematic_move_proficiency(self, starting_cc_dph, max_cc_dph):
        current_cc_dph = starting_cc_dph

        if starting_cc_dph == max_cc_dph:
            return

        for index, cpm in enumerate(self.attacker.cpm_list):
            self._calculate_attack_multiplier(cpm['value'])
            self._set_move_damage(self.cinematic_move)

            # ensure to get the max cinematic move damage row, which might otherwise get filtered out
            if self.cinematic_move.damage_per_hit == max_cc_dph:
                self.cinematic_move_proficiency.append((
                    self.cinematic_move.damage_per_hit,
                    cpm['level'],
                    cpm['value'],
                    cpm['total_stardust_cost'],
                    cpm['total_candy_cost'],
                ))

            if ([x for x in self.quick_move_proficiency if cpm['value'] == x[2]]
                or (self.show_cinematic_breakpoints and current_cc_dph < self.cinematic_move.damage_per_hit)):
                self.cinematic_move_proficiency.append((
                    self.cinematic_move.damage_per_hit,
                    cpm['level'],
                    cpm['value'],
                    cpm['total_stardust_cost'],
                    cpm['total_candy_cost'],
                ))
                current_cc_dph = self.cinematic_move.damage_per_hit

    def _get_details_table(self, starting_qk_dph):
        details = []

        for c in sorted(self.cinematic_move_proficiency):
            for q in sorted(self.quick_move_proficiency):
                if q[1] == c[1]:
                    starting_qk_dph = q[0]

            # skip redundant rows
            if (starting_qk_dph, c[0]) in [(x[2], x[3]) for x in details[1:]]:
                continue

            self.quick_move.damage_per_hit = starting_qk_dph
            self.cinematic_move.damage_per_hit = c[0]

            cycle_dps, battle_time = calculate_weave_damage(
                self.quick_move, self.cinematic_move, self.defender.health)
            details.append(
                self._get_detail_row(c[1], cycle_dps, battle_time, c[3], c[4]))

        # edge case when there's improvement for quick moves, but not for cinematic
        if len(self.cinematic_move_proficiency) == 0 and len(self.quick_move_proficiency) > 0:
            for q in sorted(self.quick_move_proficiency):
                self.quick_move.damage_per_hit = q[0]

                cycle_dps, battle_time = calculate_weave_damage(
                    self.quick_move, self.cinematic_move, self.defender.health)
                details.append(
                    self._get_detail_row(q[1], cycle_dps, battle_time, q[3], q[4]))
        return details

    def _get_detail_row(self, level, cycle_dps, battle_time, stardust_cost, candy_cost):
        return ('{:g}'.format(float(level)), self._format_powerup_cost(stardust_cost, candy_cost),
                self.quick_move.damage_per_hit, self.cinematic_move.damage_per_hit,
                self._format_dps(cycle_dps), '{:.1f}s'.format(battle_time))

    def _format_powerup_cost(self, stardust_cost, candy_cost):
        if stardust_cost - self.stardust_cost == 0 and candy_cost - self.candy_cost == 0:
            return '- / -'

        return '{:g}k / {}'.format(
            (stardust_cost - self.stardust_cost) / 1000,
            (candy_cost - self.candy_cost)
        )

    def _format_dps(self, cycle_dps):
        self.cycle_dps = cycle_dps
        dps_percentage = self.cycle_dps * 100 / self.perfect_max_dps
        return '{:g} ({:g}%)'.format(round(cycle_dps, 1), round(dps_percentage, 1))

    def _get_top_counters(self):
        top_counters_qs = TopCounter.objects.filter(
            defender_id=self.defender.pk,
            defender_cpm=self.defender.cpm,
            weather_condition_id=self.weather_condition.pk
        ).order_by('-highest_dps')[:15]

        top_counters = OrderedDict()
        cycle_dps, _ = calculate_weave_damage(self.quick_move, self.cinematic_move)
        # todo: refactor this nonsense
        for top_counter in top_counters_qs:
            if round(cycle_dps, 1) >= top_counter.highest_dps:
                top_counters['user_{}'.format(self.attacker.name)] = [(
                    '<b>{}</b> (L{:g}, {}A)'.format(
                        self.attacker.name,
                        self.attacker.level,
                        self.attacker.atk_iv,
                    ),
                    self.quick_move.name,
                    self.cinematic_move.name,
                    round(cycle_dps, 1),
                )]
            moveset_data = []
            for data_row in top_counter.moveset_data:
                moveset_data.append((
                    self._get_top_counter_url(top_counter, data_row[1], data_row[2]),
                    data_row[1],
                    data_row[2],
                    round(data_row[0], 1),
                ))
            top_counters[top_counter.counter.name] = moveset_data

        if not 'user_{}'.format(self.attacker.name) in top_counters:
            top_counters['user_{}'.format(self.attacker.name)] = [(
                    '<b>{}</b> (L{:g}, {}A)'.format(
                        self.attacker.name,
                        self.attacker.level,
                        self.attacker.atk_iv,
                    ),
                    self.quick_move.name,
                    self.cinematic_move.name,
                    round(cycle_dps, 1),
                )]
        return top_counters

    def _get_top_counter_url(self, top_counter, quick_move, cinematic_move):
        params = urllib.parse.urlencode({
            'attacker': top_counter.counter.slug,
            'attacker_level': 20,
            'quick_move': slugify(quick_move),
            'cinematic_move': slugify(cinematic_move),
            'attacker_atk_iv': 15,
            'weather_condition': top_counter.weather_condition_id,
            'defender': top_counter.defender.slug,
            'defender_cpm': '{}{}'.format(top_counter.defender_cpm, self.raid_tier),
            'tab': 'breakpoints',
        })
        return '<a href="{0}?{1}">{2}</a>'.format(
            reverse('pgo:breakpoint-calc'), params, top_counter.counter.name,
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

        self.current_raid_bosses = RaidBoss.objects.filter(
            Q(status=RaidBossStatus.CURRENT) | Q(status=RaidBossStatus.ANTICIPATED)
        ).order_by('-raid_tier', '-pokemon__slug') if data.get('current_raid_bosses') else []

        self.past_raid_bosses = RaidBoss.objects.filter(status=RaidBossStatus.PAST).order_by(
            '-raid_tier', '-pokemon__slug') if data.get('past_raid_bosses') else []
        # todo devise a better metric for relevant defenders
        self.relevant_defenders = Pokemon.objects.filter(
            maximum_cp__gte=2000) if data.get('relevant_defenders') else []

        self.max_cpm_value = CPM.gyms.last().value

    # TODO DRY THIS
    def _process_data(self):
        total_breakpoints = 0
        total_breakpoints_reached = 0

        self.matchup_data = OrderedDict()
        for defender in self.current_raid_bosses:
            self._get_breakpoint_data(defender)

        current = []
        for key, value in self.matchup_data.items():
            breakpoints_reached = sum(
                [1 if x['final_breakpoint_reached'] is True else 0 for x in value])

            current.append({
                'tier': key,
                'quick_move': self.quick_move.name,
                'final_breakpoints_reached': breakpoints_reached,
                'total_breakpoints': len(value),
                'matchups': [x for x in value],
            })
            total_breakpoints += len(value)
            total_breakpoints_reached += breakpoints_reached

        self.matchup_data = OrderedDict()
        for defender in self.past_raid_bosses:
            self._get_breakpoint_data(defender)

        past = []
        for key, value in self.matchup_data.items():
            breakpoints_reached = sum(
                [1 if x['final_breakpoint_reached'] is True else 0 for x in value])

            past.append({
                'tier': key,
                'quick_move': self.quick_move.name,
                'final_breakpoints_reached': breakpoints_reached,
                'total_breakpoints': len(value),
                'matchups': [x for x in value],
            })
            total_breakpoints += len(value)
            total_breakpoints_reached += breakpoints_reached

        # for defender in self.relevant_defenders:
        #     self._get_breakpoint_data(defender)
        return {
            'current': current,
            'past': past,
            'summary': self._get_summary(total_breakpoints_reached, total_breakpoints)
        }

    def _get_breakpoint_data(self, defender):
        stab = is_move_stab(self.quick_move, self.attacker)
        weather_boosted = self.quick_move.move_type_id in self.boosted_types
        effectivness = determine_move_effectivness(self.quick_move, defender)
        max_multiplier = self._get_attack_multiplier(MAX_IV, defender)

        max_damage_per_hit = calculate_dph(
            self.quick_move.power, max_multiplier, stab, weather_boosted, effectivness)

        actual_multiplier = self._get_attack_multiplier(self.attack_iv, defender)
        actual_damage_per_hit = calculate_dph(
            self.quick_move.power, actual_multiplier, stab, weather_boosted, effectivness)

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
            <p>
            Your {} can reach the final {} breakpoint in <b>{} out of the {}</b> tested matchups.
            </p>
            <p>You can review the details below.</p>
            '''.format(
            self.attacker.name, self.quick_move.name, total_breakpoints_reached, total_breakpoints
        )

    def _get_attack_multiplier(self, attack_iv, defender):
        return ((self.attacker.pgo_attack + attack_iv) * self.max_cpm_value) / (
            (defender.pokemon.pgo_defense + MAX_IV) * defender.raid_tier.raid_cpm.value)
