from __future__ import division

from decimal import Decimal

from rest_framework import response, status, viewsets
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.generics import GenericAPIView

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.http import Http404

from pgo.api.serializers import (
    BreakpointCalcSerializer, BreakpointCalcStatsSerializer,
    PokemonMoveSerializer, MoveSerializer, PokemonSerializer, TypeSerializer,
)
from pgo.models import (
    CPM, PokemonMove, Move, Pokemon, Type, TypeEffectivness, RaidBoss, WeatherCondition, RaidTier,
)
from pgo.utils import (
    calculate_dph,
    calculate_defender_health,
    calculate_weave_damage,
    NEUTRAL_SCALAR,
)


DEFAULT_EFFECTIVNESS = Decimal(str(NEUTRAL_SCALAR))
CC_FACTOR = 1.1
MAX_IV = 15
DEFENDER_IV_RANGE = [15]
DEFENDER_LEVEL_LIST = [40]


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
            raid_boss_ids = RaidBoss.objects.filter(
                raid_tier=self.request.GET.get('raid-boss-tier-group')
            ).values_list('pokemon__id', flat=True)

            return self.queryset.filter(id__in=raid_boss_ids).order_by('name')
        return super(PokemonViewSet, self).get_queryset()


class TypeViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Type.objects.all()
    serializer_class = TypeSerializer


class BreakpointCalcAPIView(GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = BreakpointCalcSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self._fetch_data(serializer.data)
        return response.Response(self._process_data(), status=status.HTTP_200_OK)

    def _fetch_data(self, data):
        cpm_qs = CPM.gyms.all()
        self.max_cpm_value = cpm_qs.last().value

        self.attacker = self._get_pokemon(data.get('attacker'))
        self.attacker.atk_iv = data.get('attack_iv')
        self.attacker.cpm_list = cpm_qs.filter(level__gte=data.get(
            'attacker_lvl')).values('level', 'value', 'total_powerup_cost')
        self.qk_move = self._get_move(data.get('quick_move'))
        self.cc_move = self._get_move(data.get('cinematic_move'))

        self.defender = self._get_pokemon(data.get('defender'))
        self.defender.level = data.get('defender_lvl')

        self.raid_tier = self._verify_raid_tier(data.get('raid_tier', 0))
        if self.raid_tier > 0:
            self.defender.cpm = CPM.raids.get(
                raid_cpm=True, raid_tier=self.raid_tier).value
        else:
            self.defender.cpm = cpm_qs.get(level=self.defender.level).value
        self.defender.defense_iv = data.get('defense_iv')
        self.boss_or_level = ('raid boss' if self.raid_tier > 0 else
            'level {:g}'.format(self.defender.level))

        self.boosted_types = []
        if data.get('weather_condition', 0) > 0:
            self.weather_condition = get_object_or_404(
                WeatherCondition.objects, pk=data.get('weather_condition'))
            self.boosted_types = list(
                self.weather_condition.types_boosted.values_list('pk', flat=True))

    def _verify_raid_tier(self, tier):
        if tier in RaidTier.objects.values_list('tier', flat=True):
            return tier
        return 0

    def _get_pokemon(self, id):
        try:
            return Pokemon.objects.only('name', 'pgo_attack', 'pgo_stamina', 'primary_type_id',
                'secondary_type_id').get(pk=id)
        except Pokemon.DoesNotExist:
            raise Http404

    def _get_move(self, id):
        try:
            return Move.objects.only('name', 'power', 'duration', 'move_type_id').get(pk=id)
        except Move.DoesNotExist:
            raise Http404

    def _process_data(self):
        return {
            'summary': self._get_battle_summary(),
            'quick_move': self._serialize(self.qk_move),
            'cinematic_move': self._serialize(self.cc_move),
            'attacker': self._serialize(self.attacker),
            'defender': self._serialize(self.defender),
            'raid_tier': self.raid_tier,
            'weather_boost': self._check_weather_boost(),
            'attack_iv_assessment': self._assess_attack_iv(),
        }

    def _get_battle_summary(self):
        self._set_move_parameters()
        self._calculate_move_stats(self.attacker.cpm_list.first()['value'])

        if self.raid_tier > 0:
            stamina = self.defender.raidboss_set.get(
                raid_tier=self.raid_tier).raid_tier.tier_stamina
        else:
            stamina = self.defender.pgo_stamina
        self.defender.health = calculate_defender_health(
            stamina + MAX_IV, self.defender.cpm
        )
        self.cycle_dps, battle_time = calculate_weave_damage(
            self.qk_move, self.cc_move, self.defender.health
        )

        max_damage_qk = self._get_max_damage_move(self.qk_move)
        self.max_damage_cc = self._get_max_damage_move(self.cc_move)
        self.max_dps, _ = calculate_weave_damage(max_damage_qk, self.max_damage_cc)

        return '''Your {} would do {:g} DPS ({:g}%) to a {} {},
            knocking it out in {:.1f} seconds.'''.format(
            self.attacker.name, round(self.cycle_dps, 1),
            round(self.cycle_dps * 100 / self.max_dps, 1), self.boss_or_level,
            self.defender.name, battle_time)

    def _get_max_damage_move(self, move):
        self._calculate_attack_multiplier()
        self._set_move_damage(move)
        return move

    def _set_move_parameters(self):
        self.qk_move.stab = self._is_stab(self.attacker, self.qk_move)
        self.cc_move.stab = self._is_stab(self.attacker, self.cc_move)

        self.qk_move.effectivness = self._get_effectivness(
            self.qk_move, self.defender)
        self.cc_move.effectivness = self._get_effectivness(
            self.cc_move, self.defender)

        self.qk_move.weather_boosted = self.qk_move.move_type_id in self.boosted_types
        self.cc_move.weather_boosted = self.cc_move.move_type_id in self.boosted_types

    def _calculate_move_stats(self, attacker_cpm=None):
        self._calculate_attack_multiplier(attacker_cpm)
        self._set_move_damage(self.qk_move)
        self._set_move_damage(self.cc_move)

    def _calculate_attack_multiplier(self, attacker_cpm=None):
        if not attacker_cpm:
            attacker_cpm = self.max_cpm_value

        self.attack_multiplier = (
            (self.attacker.pgo_attack + self.attacker.atk_iv) * attacker_cpm) / (
            (self.defender.pgo_defense + self.defender.defense_iv) * self.defender.cpm)

    def _set_move_damage(self, move):
        move.damage_per_hit = self._calculate_damage(move)

    def _get_effectivness(self, move, pokemon):
        secondary_type_effectivness = DEFAULT_EFFECTIVNESS
        if pokemon.secondary_type_id:
            secondary_type_effectivness = TypeEffectivness.objects.get(
                type_offense__id=move.move_type_id,
                type_defense__id=pokemon.secondary_type_id).effectivness.scalar
        primary_type_effectivness = TypeEffectivness.objects.get(
            type_offense__id=move.move_type_id,
            type_defense__id=pokemon.primary_type_id).effectivness.scalar
        return secondary_type_effectivness * primary_type_effectivness

    def _is_stab(self, pokemon, move):
        return (
            pokemon.primary_type_id == move.move_type_id or
            pokemon.secondary_type_id == move.move_type_id
        )

    def _calculate_damage(self, move):
        return calculate_dph(
            move.power, self.attack_multiplier, move.stab, move.weather_boosted, move.effectivness)

    def _check_weather_boost(self):
        weather_boost_info = ''
        if self.qk_move.weather_boosted or self.cc_move.weather_boosted:
            qk_move_boosted = self.qk_move.name if self.qk_move.weather_boosted else ''
            cc_move_boosted = self.cc_move.name if self.cc_move.weather_boosted else ''

            conjuction = ' and ' if qk_move_boosted and cc_move_boosted else ''
            verb = 'are' if qk_move_boosted and cc_move_boosted else 'is'

            weather_boost_info = '<br><br>{0}{1}{2} {3} boosted by {4} weather.'.format(
                qk_move_boosted, conjuction, cc_move_boosted,
                verb, self.weather_condition
            )
        return weather_boost_info

    def _assess_attack_iv(self):
        self._calculate_move_stats()
        current_qk_dph = self.qk_move.damage_per_hit

        self.attacker.atk_iv = MAX_IV
        self._calculate_move_stats()

        if (current_qk_dph == self.qk_move.damage_per_hit):
            attack_iv_assessment = '''
                Your {}\'s <b>attack IV is high enough</b> for it to reach the last {}
                breakpoint against a {} {}.'''.format(
                self.attacker.name, self.qk_move.name,
                self.boss_or_level, self.defender.name)
        else:
            attack_iv_assessment = '''
                Unfortunately, your {}\'s <b>attack IV is too low</b> for it to reach the
                last breakpoint for {} against a {} {}.'''.format(
                self.attacker.name, self.qk_move.name, self.boss_or_level, self.defender.name)

        return attack_iv_assessment

    def _serialize(self, obj):
        data = {}
        for key, value in obj.__dict__.items():
            if key != '_state':
                data[key] = value
        return data


class BreakpointCalcStatsAPIView(GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = BreakpointCalcStatsSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = self._process_data(serializer.data)
        return response.Response(data, status=status.HTTP_200_OK)

    def _process_data(self, data):
        self.defense_iv_range = DEFENDER_IV_RANGE
        attacker_cpm_list = data['attacker']['cpm_list']

        total_attack = data['attacker']['pgo_attack'] + data['attacker']['atk_iv']
        self.attack_multiplier = total_attack * attacker_cpm_list[0]['value']
        self.max_attack_multiplier = total_attack * attacker_cpm_list[-1]['value']

        def_ivs = []
        for defense_iv in self.defense_iv_range:
            def_ivs.append('Attack breakdown against {} DEF IV'.format(defense_iv))
            def_ivs.append('')
        stats = [{'Defender level': def_ivs}]

        raid_tier = data.get('raid_tier') or None
        if raid_tier:
            cpm_list = CPM.raids.filter(raid_tier=raid_tier)
        else:
            cpm_list = CPM.gyms.filter(level__in=DEFENDER_LEVEL_LIST)

        self.boosted_types = []
        if data.get('weather_condition', 0) > 0:
            weather_condition = get_object_or_404(
                WeatherCondition.objects, pk=data.get('weather_condition'))
            self.boosted_types = list(weather_condition.types_boosted.values_list('pk', flat=True))

        for cpm in cpm_list:
            stats.append({
                '{:g}'.format(float(cpm.level)):
                self._calculate_moves_dph(
                    cpm.value,
                    data['defender']['pgo_defense'],
                    data['quick_move'],
                    data['cinematic_move']
                )
            })
        return stats

    def _calculate_moves_dph(self, cpm_value, defense, qk_move, cc_move):
        attack_modifiers = self._calculate_attack_modifiers(
            self.attack_multiplier, defense, cpm_value)
        max_attack_modifiers = self._calculate_attack_modifiers(
            self.max_attack_multiplier, defense, cpm_value)

        dph_list = []
        for attack_modifiers in zip(attack_modifiers, max_attack_modifiers):
            dph_list.append(('{} would do '.format(qk_move['name']),
                self._build_move_stats(attack_modifiers, qk_move)))
            dph_list.append(('{} would do '.format(cc_move['name']),
                self._build_move_stats(attack_modifiers, cc_move)))
        return dph_list

    def _calculate_attack_modifiers(self, attack_multiplier, defense, cpm_value):
        return (
            attack_multiplier / float((defense + defense_iv) * cpm_value)
            for defense_iv in self.defense_iv_range
        )

    def _build_move_stats(self, attack_modifiers, move):
        current_dph = calculate_dph(
            move['power'], attack_modifiers[0], move['stab'],
            move['weather_boosted'], move['effectivness'])
        max_dph = calculate_dph(
            move['power'], attack_modifiers[1], move['stab'],
            move['weather_boosted'], move['effectivness'])

        if current_dph == max_dph:
            return '{}<br>'.format(current_dph)
        return '{} <b>({} possible)</b><br>'.format(current_dph, max_dph)


class BreakpointCalcDetailAPIView(BreakpointCalcAPIView):

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self._fetch_data(serializer.data)

        data = self._process_data()
        return response.Response(data, status=status.HTTP_200_OK)

    def _process_data(self):
        self._set_move_parameters()

        self._calculate_move_stats(self.attacker.cpm_list.first()['value'])
        starting_qk_dph = self.qk_move.damage_per_hit
        starting_cc_dph = self.cc_move.damage_per_hit

        summary = self._get_battle_summary()
        self.qk_move_proficiency = []
        self.cc_move_proficiency = []
        self.powerup_cost = self.attacker.cpm_list.first()['total_powerup_cost']

        self._set_qk_move_proficiency(starting_qk_dph)
        self._set_cc_move_proficiency(
            starting_cc_dph, self.max_damage_cc.damage_per_hit)

        details_table = self._get_details_table(starting_qk_dph)
        return {
            'summary': summary,
            'details': details_table,
        }

    def _set_qk_move_proficiency(self, starting_qk_dph):
        current_qk_dph = starting_qk_dph

        for cpm in self.attacker.cpm_list:
            self._calculate_attack_multiplier(cpm['value'])
            self._set_move_damage(self.qk_move)

            if current_qk_dph < self.qk_move.damage_per_hit:
                self.qk_move_proficiency.append((self.qk_move.damage_per_hit,
                    cpm['level'], cpm['value'], cpm['total_powerup_cost'],))
                current_qk_dph = self.qk_move.damage_per_hit

    def _set_cc_move_proficiency(self, starting_cc_dph, max_cc_dph):
        current_cc_dph = starting_cc_dph

        if starting_cc_dph == max_cc_dph:
            return

        for index, cpm in enumerate(self.attacker.cpm_list):
            self._calculate_attack_multiplier(cpm['value'])
            self._set_move_damage(self.cc_move)

            # ensure to get the max cinematic move damage row, which might
            # otherwise get filtered out
            if self.cc_move.damage_per_hit == max_cc_dph:
                self.cc_move_proficiency.append((self.cc_move.damage_per_hit,
                    cpm['level'], cpm['value'], cpm['total_powerup_cost'],))

            if ([x for x in self.qk_move_proficiency if cpm['value'] == x[2]] or
                    current_cc_dph < self.cc_move.damage_per_hit and
                    current_cc_dph * CC_FACTOR < self.cc_move.damage_per_hit):
                self.cc_move_proficiency.append((self.cc_move.damage_per_hit,
                    cpm['level'], cpm['value'], cpm['total_powerup_cost'],))
                current_cc_dph = self.cc_move.damage_per_hit

    def _get_details_table(self, starting_qk_dph):
        details = [('Level ($)', self.qk_move.name, self.cc_move.name, 'DPS (%)', 'Time to KO',)]

        for c in sorted(self.cc_move_proficiency):
            for q in sorted(self.qk_move_proficiency):
                if q[1] == c[1]:
                    starting_qk_dph = q[0]

            # skip redundant rows
            if (starting_qk_dph, c[0]) in [(x[1], x[2]) for x in details[1:]]:
                continue

            self.qk_move.damage_per_hit = starting_qk_dph
            self.cc_move.damage_per_hit = c[0]

            cycle_dps, battle_time = calculate_weave_damage(
                self.qk_move, self.cc_move, self.defender.health)
            details.append(
                self._get_detail_row(c[1], cycle_dps, battle_time, c[3]))

        # edge case when there's improvement for quick moves, but not for cinematic
        if len(self.cc_move_proficiency) == 0 and len(self.qk_move_proficiency) > 0:
            for q in sorted(self.qk_move_proficiency):
                self.qk_move.damage_per_hit = q[0]

                cycle_dps, battle_time = calculate_weave_damage(
                    self.qk_move, self.cc_move, self.defender.health)
                details.append(
                    self._get_detail_row(q[1], cycle_dps, battle_time, q[3]))
        return details

    def _get_detail_row(self, level, cycle_dps, battle_time, powerup_cost):
        return (self._level_and_pu_cost(level, powerup_cost),
            self.qk_move.damage_per_hit, self.cc_move.damage_per_hit,
            self._get_formatted_dps(cycle_dps), '{:.1f}s'.format(battle_time))

    def _level_and_pu_cost(self, level, powerup_cost):
        return '{:g} ({:g}k)'.format(
            float(level), (powerup_cost - self.powerup_cost) / 1000)

    def _get_formatted_dps(self, cycle_dps):
        self.cycle_dps = cycle_dps
        dps_percentage = self.cycle_dps * 100 / self.max_dps
        return '{:g} ({:g}%)'.format(round(cycle_dps, 1), round(dps_percentage, 1))
