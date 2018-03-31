from __future__ import division, unicode_literals

from collections import OrderedDict
from decimal import Decimal

from rest_framework import response, status, viewsets
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.generics import GenericAPIView

from django.db.models import Q
from django.shortcuts import get_object_or_404

from pgo.api.serializers import (
    BreakpointCalcSerializer, PokemonMoveSerializer, MoveSerializer,
    PokemonSerializer, TypeSerializer, GoodToGoSerializer,
)
from pgo.models import (
    CPM, PokemonMove, Move, Pokemon, Type, TypeEffectivness, RaidBoss, WeatherCondition,
    RaidBossStatus,
)
from pgo.utils import (
    calculate_dph,
    calculate_defender_health,
    calculate_weave_damage,
    get_pokemon_data,
    get_move_data,
    determine_move_effectivness,
    is_move_stab,
    DEFAULT_EFFECTIVNESS,
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
    permission_classes = (AllowAny,)
    serializer_class = BreakpointCalcSerializer

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        self._fetch_data(serializer.data)

        self._set_move_parameters()
        data = {
            'weather_boost': self._check_weather_boost(),
            'attack_iv_assessment': self._assess_attack_iv(),
            'damager_per_hit_details': self._calculate_moves_dph(
                self.defender.cpm,
                self.defender.pgo_defense,
                self.quick_move,
                self.cinematic_move
            )
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

    def _get_max_damage_move(self, move):
        self._calculate_attack_multiplier()
        self._set_move_damage(move)
        return move

    def _set_move_parameters(self):
        self.quick_move.stab = is_move_stab(self.quick_move, self.attacker)
        self.cinematic_move.stab = is_move_stab(self.cinematic_move, self.attacker)

        self.quick_move.effectivness = determine_move_effectivness(self.quick_move, self.defender)
        self.cinematic_move.effectivness = determine_move_effectivness(
            self.cinematic_move, self.defender)

        self.quick_move.weather_boosted = self.quick_move.move_type_id in self.boosted_types
        self.cinematic_move.weather_boosted = self.cinematic_move.move_type_id in self.boosted_types

    def _calculate_move_stats(self, attacker_cpm=None, attack_iv=None):
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

    def _check_weather_boost(self):
        weather_boost_info = ''
        if self.quick_move.weather_boosted or self.cinematic_move.weather_boosted:
            quick_move_boosted = self.quick_move.name if self.quick_move.weather_boosted else ''
            cinematic_move_boosted = self.cinematic_move.name if self.cinematic_move.weather_boosted else ''

            conjuction = ' and ' if quick_move_boosted and cinematic_move_boosted else ''
            verb = 'are' if quick_move_boosted and cinematic_move_boosted else 'is'

            weather_boost_info = '{0}{1}{2} {3} boosted by {4} weather.'.format(
                quick_move_boosted, conjuction, cinematic_move_boosted,
                verb, self.weather_condition
            )
        return weather_boost_info

    def _assess_attack_iv(self):
        self._calculate_move_stats()
        self.current_qk_dph = self.quick_move.damage_per_hit
        self._calculate_move_stats(attack_iv=MAX_IV)

        params = (
            self.attacker.name,
            self.quick_move.name,
            self.quick_move.damage_per_hit,
        )
        if (self.current_qk_dph == self.quick_move.damage_per_hit):
            return 'Your {}\'s <b>attack IV is high enough</b> for it to reach the final {} \
                    breakpoint ({}) in this matchup!'.format(*params)
        else:
            return 'Unfortunately, your {}\'s <b>attack IV is too low</b> for it to reach the \
                    final breakpoint for {} ({}) in this matchup.'''.format(*params)

    def _calculate_moves_dph(self, cpm_value, defense, quick_move, cinematic_move):
        total_attack = self.attacker.pgo_attack + self.attacker.atk_iv

        attack_multiplier = total_attack * CPM.objects.get(
            level=self.attacker.level, raid_cpm=False).value
        max_attack_multiplier = total_attack * self.max_cpm_value
        attack_modifier = attack_multiplier / ((defense + MAX_IV) * cpm_value)
        max_attack_modifier = max_attack_multiplier / ((defense + MAX_IV) * cpm_value)

        return {
            'quick_move': 'At level {:g}, its {} would do {} and '.format(
                self.attacker.level,
                quick_move.name,
                self._build_move_stats(attack_modifier, max_attack_modifier, quick_move)
            ),
            'cinematic_move': '{} {} possible damage per hit.'.format(
                cinematic_move.name,
                self._build_move_stats(attack_modifier, max_attack_modifier, cinematic_move)
            )
        }

    def _build_move_stats(self, attack_modifier, max_attack_modifier, move):
        current_dph = calculate_dph(
            move.power, attack_modifier, move.stab, move.weather_boosted, move.effectivness)
        max_dph = calculate_dph(
            move.power, max_attack_modifier, move.stab, move.weather_boosted, move.effectivness)

        return '<b>{}</b> / {},'.format(current_dph, max_dph)


class BreakpointCalcDetailAPIView(BreakpointCalcAPIView):

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        self._fetch_data(serializer.data)
        return response.Response(self._process_data(), status=status.HTTP_200_OK)

    def _process_data(self):
        self._set_move_parameters()

        self._calculate_move_stats(attacker_cpm=self.attacker.cpm_list.first()['value'])
        starting_qk_dph = self.quick_move.damage_per_hit
        starting_cc_dph = self.cinematic_move.damage_per_hit

        summary = self._get_battle_summary()
        self.quick_move_proficiency = []
        self.cinematic_move_proficiency = []
        self.stardust_cost = self.attacker.cpm_list.first()['total_stardust_cost']
        self.candy_cost = self.attacker.cpm_list.first()['total_candy_cost']

        self._set_quick_move_proficiency(starting_qk_dph)
        self._set_cinematic_move_proficiency(
            starting_cc_dph, self.max_damage_cc.damage_per_hit)

        details_table = self._get_details_table(starting_qk_dph)
        return {
            'summary': summary,
            'details': details_table,
        }

    def _get_battle_summary(self):
        self._set_move_parameters()
        self._calculate_move_stats(attacker_cpm=self.attacker.cpm_list.first()['value'])

        stamina = self.defender.pgo_stamina
        if self.raid_tier:
            stamina = self.defender.raidboss_set.get(
                raid_tier=self.raid_tier).raid_tier.tier_stamina

        self.defender.health = calculate_defender_health(
            stamina + MAX_IV, self.defender.cpm
        )
        self.cycle_dps, battle_time = calculate_weave_damage(
            self.quick_move, self.cinematic_move, self.defender.health
        )

        max_damage_qk = self._get_max_damage_move(self.quick_move)
        self.max_damage_cc = self._get_max_damage_move(self.cinematic_move)
        self.max_dps, _ = calculate_weave_damage(max_damage_qk, self.max_damage_cc)

        return (
            'Your {} would do <b>{:g} DPS ({:g}%)</b> to a {} {}, knocking it out in {:.1f} seconds.'
            .format(
                self.attacker.name,
                round(self.cycle_dps, 1),
                round(self.cycle_dps * 100 / self.max_dps, 1),
                'tier {} raid boss'.format(
                    self.raid_tier) if self.raid_tier else 'level 40, 15 defense IV',
                self.defender.name,
                battle_time
            )
        )

    def _set_quick_move_proficiency(self, starting_qk_dph):
        current_qk_dph = starting_qk_dph

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

            # ensure to get the max cinematic move damage row, which might
            # otherwise get filtered out
            if self.cinematic_move.damage_per_hit == max_cc_dph:
                self.cinematic_move_proficiency.append((
                    self.cinematic_move.damage_per_hit,
                    cpm['level'],
                    cpm['value'],
                    cpm['total_stardust_cost'],
                    cpm['total_candy_cost'],
                ))

            if ([x for x in self.quick_move_proficiency if cpm['value'] == x[2]] or
                    current_cc_dph < self.cinematic_move.damage_per_hit and
                    current_cc_dph * CINEMATIC_MOVE_FACTOR < self.cinematic_move.damage_per_hit):
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
        return (self._format_level(level), self._format_powerup_cost(stardust_cost, candy_cost),
                self.quick_move.damage_per_hit, self.cinematic_move.damage_per_hit,
                self._format_dps(cycle_dps), '{:.1f}s'.format(battle_time))

    def _format_level(self, level):
        return '{:g}'.format(float(level))

    def _format_powerup_cost(self, stardust_cost, candy_cost):
        return '{:g}k / {}'.format(
            (stardust_cost - self.stardust_cost) / 1000,
            (candy_cost - self.candy_cost)
        )

    def _format_dps(self, cycle_dps):
        self.cycle_dps = cycle_dps
        dps_percentage = self.cycle_dps * 100 / self.max_dps
        return '{:g} ({:g}%)'.format(round(cycle_dps, 1), round(dps_percentage, 1))


class GoodToGoAPIView(GenericAPIView):
    permission_classes = (AllowAny,)
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
        stab = is_move_stab(self.attacker, self.quick_move)
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
