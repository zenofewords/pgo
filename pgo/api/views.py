from __future__ import division

from decimal import Decimal

from rest_framework import response, status, viewsets
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.generics import GenericAPIView

from django.db.models import Q

from pgo.api.serializers import (
    AttackProficiencySerializer, AttackProficiencyStatsSerializer,
    AttackProficiencyDetailSerializer, SimpleMoveSerializer, MoveSerializer,
    PokemonSerializer, TypeSerializer,
)
from pgo.models import (
    CPM, Move, Pokemon, Type, TypeEffectivness,
)
from pgo.utils import (
    calculate_dph,
    simulate_weave_damage,
    calculate_defender_health,
    calculate_defense,
)


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

        self._fetch_data(serializer.data)
        data = self._process_data(serializer.data)
        return response.Response(data, status=status.HTTP_200_OK)

    def _fetch_data(self, data):
        self.attacker = self._get_pokemon(data.get('attacker'))
        self.attacker.cpm_list = tuple(CPM.objects.filter(level__gte=data.get(
            'attacker_level')).values_list('value', 'level'))
        self.attacker.atk_iv = data.get('attack_iv')
        self.qk_move = self._get_move(data.get('quick_move'))
        self.cc_move = self._get_move(data.get('cinematic_move'))

        self.defender = self._get_pokemon(data.get('defender'))
        self.defender.level = data.get('defender_level')
        self.defender.cpm = self._get_cpm(self.defender.level)
        self.defender.defense_iv = data.get('defense_iv')

    def _process_data(self, data):
        self._calculate_move_stats()
        battle_time = self._simulate_battle()

        return {
            'quick_move': self._serialize(self.qk_move),
            'cinematic_move': self._serialize(self.cc_move),
            'attacker': self._serialize(self.attacker),
            'defender': self._serialize(self.defender),
            'summary': self._get_summary(battle_time)
        }

    def _simulate_battle(self):
        self.defender.health = calculate_defender_health(
            self.defender.pgo_stamina + 15, self.defender.cpm)
        self.defender.defense = calculate_defense(
            self.defender.pgo_defense + self.defender.defense_iv, self.defender.cpm)
        self.weave_damage, battle_time = simulate_weave_damage(
            self.qk_move, self.cc_move, self.defender.health)

        return battle_time

    def _get_summary(self, battle_time):
        if battle_time >= 99:
            return '''
                Your {} would do {} damage to a level {:g} {} with {} defense
                and {} health, before timing out.'''.format(
                self.attacker.name, self.weave_damage, self.defender.level,
                self.defender.name, self.defender.defense, self.defender.health)
        else:
            return '''
                Your {} would do {} damage to a level {:g} {} with {} defense
                and {} health, finishing the battle in {} seconds.'''.format(
                self.attacker.name, self.weave_damage, self.defender.level,
                self.defender.name, self.defender.defense, self.defender.health,
                battle_time)

    def _get_cpm(self, level):
        return CPM.objects.get(level=level).value

    def _calculate_move_stats(self, attacker_cpm=None):
        if not attacker_cpm:
            attacker_cpm = self.attacker.cpm_list[0][0]

        self._calculate_attack_multiplier(attacker_cpm)
        self._set_move_damage(self.qk_move)
        self._set_move_damage(self.cc_move)

    def _calculate_attack_multiplier(self, attacker_cpm):
        self.attack_multiplier = (
            (self.attacker.pgo_attack + self.attacker.atk_iv) * attacker_cpm) / (
            (self.defender.pgo_defense + self.defender.defense_iv) * self.defender.cpm)

    def _set_move_damage(self, move):
        move.effectivness = self._get_effectivness(move, self.defender)
        move.stab = self._is_stab(self.attacker, move)
        move.damage_per_hit, move.dps = self._calculate_damage(
            move, move.stab, move.effectivness
        )

    def _serialize(self, obj):
        data = {}
        for key, value in obj.__dict__.items():
            if key != '_state':
                data[key] = value
        return data

    def _get_pokemon(self, id):
        return Pokemon.objects.only('name', 'pgo_attack', 'pgo_stamina',
            'primary_type_id', 'secondary_type_id').get(pk=id)

    def _get_move(self, id):
        return Move.objects.only(
            'name', 'power', 'duration', 'move_type_id').get(pk=id)

    def _is_stab(self, pokemon, move):
        return (
            pokemon.primary_type_id == move.move_type_id or
            pokemon.secondary_type_id == move.move_type_id
        )

    def _get_effectivness(self, move, pokemon):
        secondary_type_effectivness = Decimal('1.0')
        if pokemon.secondary_type_id:
            secondary_type_effectivness = TypeEffectivness.objects.get(
                type_offense__id=move.move_type_id,
                type_defense__id=pokemon.secondary_type_id).effectivness.scalar
        primary_type_effectivness = TypeEffectivness.objects.get(
            type_offense__id=move.move_type_id,
            type_defense__id=pokemon.primary_type_id).effectivness.scalar
        return secondary_type_effectivness * primary_type_effectivness

    def _calculate_damage(self, move, stab, effectivness):
        dph = calculate_dph(move.power, self.attack_multiplier, stab, effectivness)
        dps = '{0:.2f}'.format(dph / (move.duration / 1000.0))
        return dph, dps


class AttackProficiencyStatsAPIView(GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = AttackProficiencyStatsSerializer
    levels = CPM.objects.filter(level__gte=30)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = self._process_data(serializer.data)
        return response.Response(data, status=status.HTTP_200_OK)

    def _process_data(self, data):
        self.defense_iv_range = range(10, 16)
        defender_cpm_list = list(CPM.objects.filter(level__gte=37))

        total_attack = data['attacker']['pgo_attack'] + data['attacker']['atk_iv']
        self.attack_multiplier = total_attack * data['attacker']['cpm_list'][0][0]
        self.max_attack_multiplier = total_attack * float(defender_cpm_list[-1].value)

        def_ivs = []
        for defense_iv in self.defense_iv_range:
            def_ivs.append(defense_iv)
            def_ivs.append('')
        stats = [{'L/IV': def_ivs}]

        for cpm in defender_cpm_list:
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
            dph_list.append(self._calc_move_stats(attack_modifiers, qk_move))
            dph_list.append(self._calc_move_stats(attack_modifiers, cc_move))
        return dph_list

    def _calculate_attack_modifiers(self, attack_multiplier, defense, cpm_value):
        return (
            attack_multiplier / float((defense + defense_iv) * cpm_value)
            for defense_iv in self.defense_iv_range
        )

    def _calc_move_stats(self, attack_modifiers, move):
        current_dph = calculate_dph(
            move['power'], attack_modifiers[0],
            move['stab'], move['effectivness'])
        max_dph = calculate_dph(
            move['power'], attack_modifiers[1],
            move['stab'], move['effectivness'])

        if current_dph / max_dph * 100 < 93:
            return '{} ({}) *'.format(current_dph, max_dph)
        if current_dph == max_dph:
            return '{}'.format(current_dph)
        return '{} ({})'.format(current_dph, max_dph)


class AttackProficiencyDetailAPIView(AttackProficiencyAPIView):
    permission_classes = (AllowAny,)
    serializer_class = AttackProficiencyDetailSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = self._process_data(serializer.data)
        return response.Response(data, status=status.HTTP_200_OK)

    def _process_data(self, data):
        self._fetch_data(data)
        self._calculate_move_stats()
        starting_qk_dph = self.qk_move.damage_per_hit
        starting_cc_dph = self.cc_move.damage_per_hit

        summary = self._get_summary(self._simulate_battle())
        self.qk_move_proficiency = []
        self.cc_move_proficiency = []
        self._set_qk_move_proficiency(starting_qk_dph)
        self._set_cc_move_proficiency(starting_cc_dph, self._get_max_cc_move_dph())

        info = {
            'summary': summary,
            'details': self._get_details(starting_qk_dph),
        }
        return info

    def _get_max_cc_move_dph(self):
        self._calculate_attack_multiplier(self.attacker.cpm_list[-1][0])
        self._set_move_damage(self.cc_move)
        return self.cc_move.damage_per_hit

    def _set_qk_move_proficiency(self, starting_qk_dph):
        current_qk_dph = starting_qk_dph

        for cpm_value in self.attacker.cpm_list:
            self._calculate_attack_multiplier(cpm_value[0])
            self._set_move_damage(self.qk_move)

            if current_qk_dph < self.qk_move.damage_per_hit:
                self.qk_move_proficiency.append(
                    (self.qk_move.damage_per_hit, cpm_value[1], cpm_value[0],))
                current_qk_dph = self.qk_move.damage_per_hit

    def _set_cc_move_proficiency(self, starting_cc_dph, max_cc_dph):
        current_cc_dph = starting_cc_dph

        if starting_cc_dph == max_cc_dph:
            return

        for index, cpm_value in enumerate(self.attacker.cpm_list):
            self._calculate_attack_multiplier(cpm_value[0])
            self._set_move_damage(self.cc_move)

            if self.cc_move.damage_per_hit == max_cc_dph:
                self.cc_move_proficiency.append(
                    (self.cc_move.damage_per_hit, cpm_value[1], cpm_value[0],))
                break

            if ([x for x in self.qk_move_proficiency if cpm_value[0] == x[2]] or
                    current_cc_dph < self.cc_move.damage_per_hit and
                    current_cc_dph / self.cc_move.damage_per_hit * 100 < 93):
                self.cc_move_proficiency.append(
                    (self.cc_move.damage_per_hit, cpm_value[1], cpm_value[0],))
                current_cc_dph = self.cc_move.damage_per_hit

    def _get_details(self, starting_qk_dph):
        details = [('Lvl', self.qk_move.name, self.cc_move.name, 'Battle Time',)]

        for c in sorted(self.cc_move_proficiency):
            for q in sorted(self.qk_move_proficiency):
                if q[1] == c[1]:
                    starting_qk_dph = q[0]

            self.qk_move.damage_per_hit = starting_qk_dph
            self.cc_move.damage_per_hit = c[0]
            battle_time = self._simulate_battle()

            details.append((c[1], starting_qk_dph, c[0],
                '{}s'.format(battle_time) if battle_time < 99 else 'Timed Out'))
        return details