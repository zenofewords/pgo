from __future__ import division

from decimal import Decimal

from rest_framework import response, status, viewsets
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.generics import GenericAPIView

from django.db.models import Q

from metrics.utils import update_stats
from pgo.api.serializers import (
    AttackProficiencySerializer, AttackProficiencyStatsSerializer,
    SimpleMoveSerializer, MoveSerializer, PokemonSerializer, TypeSerializer,
)
from pgo.models import (
    CPM, Move, Pokemon, Type, TypeEffectivness,
)
from pgo.utils import (
    calculate_dph,
    calculate_defender_health,
    calculate_weave_damage,
    NEUTRAL_SCALAR,
    RAID_TIER_POKEMON_GROUPS,
)

DEFAULT_EFFECTIVNESS = Decimal(str(NEUTRAL_SCALAR))
EFFECTIVNESS_THRESHOLD = 93
CC_FACTOR = 1.2
MAX_IV = 15
DEFENDER_IV_RANGE = [15]
DEFENDER_LEVEL_LIST = [25, 30, 40]


class MoveViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Move.objects.all()
    serializer_class = MoveSerializer

    def get_queryset(self):
        if 'pokemon-id' in self.request.GET:
            query = int(self.request.GET.get('pokemon-id', 0))

            if query != 0:
                self.serializer_class = SimpleMoveSerializer
                return self.queryset.filter(
                    Q(quick_moves_pokemon__id=query) |
                    Q(cinematic_moves_pokemon__id=query)
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
            pokemon_slug_list = RAID_TIER_POKEMON_GROUPS[
                self.request.GET.get('raid-boss-tier-group')]
            return self.queryset.filter(slug__in=pokemon_slug_list)
        return super(PokemonViewSet, self).get_queryset()


class TypeViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Type.objects.all()
    serializer_class = TypeSerializer


class AttackProficiencyAPIView(GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = AttackProficiencySerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_stats('apro')
        self._fetch_data(serializer.data)
        return response.Response(self._process_data(), status=status.HTTP_200_OK)

    def _fetch_data(self, data):
        cpm_qs = CPM.gyms.all()
        self.max_cpm_value = cpm_qs.last().value

        self.attacker = self._get_pokemon(data.get('attacker'))
        self.attacker.atk_iv = data.get('attack_iv')
        self.attacker.cpm_list = cpm_qs.filter(
            level__gte=data.get('attacker_level')).values('level', 'value')
        self.qk_move = self._get_move(data.get('quick_move'))
        self.cc_move = self._get_move(data.get('cinematic_move'))

        self.defender = self._get_pokemon(data.get('defender'))
        self.defender.level = data.get('defender_level')

        self.raid_tier = data.get('raid_tier', 0)
        if self.raid_tier > 0:
            self.defender.cpm = CPM.raids.get(
                raid_cpm=True, raid_tier=self.raid_tier).value
        else:
            self.defender.cpm = cpm_qs.get(level=self.defender.level).value
        self.defender.defense_iv = data.get('defense_iv')

    def _get_pokemon(self, id):
        return Pokemon.objects.only('name', 'pgo_attack', 'pgo_stamina',
            'primary_type_id', 'secondary_type_id').get(pk=id)

    def _get_move(self, id):
        return Move.objects.only(
            'name', 'power', 'duration', 'move_type_id').get(pk=id)

    def _process_data(self):
        data = {
            'summary': self._get_battle_summary(),
            'quick_move': self._serialize(self.qk_move),
            'cinematic_move': self._serialize(self.cc_move),
            'attacker': self._serialize(self.attacker),
            'defender': self._serialize(self.defender),
            'raid_tier': self.raid_tier,
        }
        return self._assess_attack_iv(data)

    def _get_battle_summary(self):
        self._calculate_move_stats(self.attacker.cpm_list.first()['value'])

        if self.raid_tier > 0:
            stamina = self.defender.raid_stamina
        else:
            stamina = self.defender.pgo_stamina
        self.defender.health = calculate_defender_health(
            stamina + MAX_IV, self.defender.cpm
        )
        battle_time = calculate_weave_damage(
            self.qk_move, self.cc_move, self.defender.health
        )
        return '''At its current level your pokemon would defeat a level {:g}
            {} with {} DEF IV in {:.1f} seconds.'''.format(self.defender.level,
            self.defender.name, self.defender.defense_iv, battle_time)

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
        move.effectivness = self._get_effectivness(move, self.defender)
        move.stab = self._is_stab(self.attacker, move)
        move.damage_per_hit = self._calculate_damage(
            move, move.stab, move.effectivness
        )

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

    def _calculate_damage(self, move, stab, effectivness):
        return calculate_dph(move.power, self.attack_multiplier, stab, effectivness)

    def _assess_attack_iv(self, data):
        self._calculate_move_stats()
        current_qk_dph = self.qk_move.damage_per_hit
        current_cc_dph = self.cc_move.damage_per_hit

        self.attacker.atk_iv = MAX_IV
        self._calculate_move_stats()

        boss_or_level = 'raid boss' if self.raid_tier > 0 else 'level {0:g}'.format(self.defender.level)
        if (current_qk_dph == self.qk_move.damage_per_hit and current_cc_dph /
                self.cc_move.damage_per_hit * 100 > EFFECTIVNESS_THRESHOLD):

            attack_iv_assessment = '''
                Your {}\'s ATK IV is high enough for it to reach the last {}
                breakpoint against a {} {}. <br /><br />Note that powering pokemon
                over level 39 is currently not possible.'''.format(
                self.attacker.name, self.qk_move.name,
                boss_or_level, self.defender.name)
        else:
            attack_iv_assessment = '''
                Unfortunately, your {}\'s ATK IV is too low for it to reach the
                last breakpoint for {} against a {} {}.'''.format(
                self.attacker.name, self.qk_move.name, boss_or_level, self.defender.name)

        data.update({'attack_iv_assessment': attack_iv_assessment})
        return data

    def _serialize(self, obj):
        data = {}
        for key, value in obj.__dict__.items():
            if key != '_state':
                data[key] = value
        return data


class AttackProficiencyStatsAPIView(GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = AttackProficiencyStatsSerializer

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
            def_ivs.append('Attack breakdown against {} def IV'.format(defense_iv))
            def_ivs.append('')
        stats = [{'Defender level': def_ivs}]

        raid_tier = data.get('raid_tier') or None
        if raid_tier:
            cpm_list = CPM.raids.filter(raid_tier=raid_tier)
        else:
            cpm_list = CPM.gyms.filter(level__in=DEFENDER_LEVEL_LIST)

        for cpm in cpm_list:
            stats.append({
                '{0:g}'.format(float(cpm.level)):
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
            dph_list.append(('{} DPH is '.format(qk_move['name']),
                self._build_move_stats(attack_modifiers, qk_move)))
            dph_list.append(('{} DPH is '.format(cc_move['name']),
                self._build_move_stats(attack_modifiers, cc_move)))
        return dph_list

    def _calculate_attack_modifiers(self, attack_multiplier, defense, cpm_value):
        return (
            attack_multiplier / float((defense + defense_iv) * cpm_value)
            for defense_iv in self.defense_iv_range
        )

    def _build_move_stats(self, attack_modifiers, move):
        current_dph = calculate_dph(
            move['power'], attack_modifiers[0],
            move['stab'], move['effectivness'])
        max_dph = calculate_dph(
            move['power'], attack_modifiers[1],
            move['stab'], move['effectivness'])

        if current_dph == max_dph:
            return '{}<br>'.format(current_dph)
        return '{} <b>({} possible)</b><br>'.format(current_dph, max_dph)


class AttackProficiencyDetailAPIView(AttackProficiencyAPIView):

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self._fetch_data(serializer.data)

        data = self._process_data()
        return response.Response(data, status=status.HTTP_200_OK)

    def _process_data(self):
        self._calculate_move_stats(self.attacker.cpm_list.first()['value'])
        starting_qk_dph = self.qk_move.damage_per_hit
        starting_cc_dph = self.cc_move.damage_per_hit

        summary = self._get_battle_summary()
        self.qk_move_proficiency = []
        self.cc_move_proficiency = []
        self._set_qk_move_proficiency(starting_qk_dph)
        self._set_cc_move_proficiency(starting_cc_dph, self._get_max_cc_move_dph())

        return {
            'summary': summary,
            'details': self._get_details_table(starting_qk_dph),
        }

    def _get_max_cc_move_dph(self):
        self._calculate_attack_multiplier()
        self._set_move_damage(self.cc_move)
        return self.cc_move.damage_per_hit

    def _set_qk_move_proficiency(self, starting_qk_dph):
        current_qk_dph = starting_qk_dph

        for cpm in self.attacker.cpm_list:
            self._calculate_attack_multiplier(cpm['value'])
            self._set_move_damage(self.qk_move)

            if current_qk_dph < self.qk_move.damage_per_hit:
                self.qk_move_proficiency.append(
                    (self.qk_move.damage_per_hit, cpm['level'], cpm['value'],))
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
                self.cc_move_proficiency.append(
                    (self.cc_move.damage_per_hit, cpm['level'], cpm['value'],))

            if ([x for x in self.qk_move_proficiency if cpm['value'] == x[2]] or
                    current_cc_dph < self.cc_move.damage_per_hit and
                    current_cc_dph * CC_FACTOR < self.cc_move.damage_per_hit):
                self.cc_move_proficiency.append(
                    (self.cc_move.damage_per_hit, cpm['level'], cpm['value'],))
                current_cc_dph = self.cc_move.damage_per_hit

    def _get_details_table(self, starting_qk_dph):
        details = [('Lvl', self.qk_move.name, self.cc_move.name, 'Battle Duration',)]

        for c in sorted(self.cc_move_proficiency):
            for q in sorted(self.qk_move_proficiency):
                if q[1] == c[1]:
                    starting_qk_dph = q[0]

            # skip redundant rows
            if (starting_qk_dph, c[0]) in [(x[1], x[2]) for x in details[1:]]:
                continue

            self.qk_move.damage_per_hit = starting_qk_dph
            self.cc_move.damage_per_hit = c[0]

            battle_time = calculate_weave_damage(
                self.qk_move, self.cc_move, self.defender.health)
            details.append(self._get_detail_row(c[1], battle_time))

        # edge case when there's improvement for quick moves, but not for cinematic
        if len(self.cc_move_proficiency) == 0 and len(self.qk_move_proficiency) > 0:
            for q in sorted(self.qk_move_proficiency):
                self.qk_move.damage_per_hit = q[0]

                battle_time = calculate_weave_damage(
                    self.qk_move, self.cc_move, self.defender.health)
                details.append(self._get_detail_row(q[1], battle_time))
        return details

    def _get_detail_row(self, level, battle_time):
        return (level, self.qk_move.damage_per_hit,
            self.cc_move.damage_per_hit, '{:.1f}s'.format(battle_time))
