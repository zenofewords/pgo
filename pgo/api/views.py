from rest_framework import response, status, viewsets
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.generics import GenericAPIView

from django.db.models import Q

from pgo.api.serializers import (
    AttackProficiencySerializer, SimpleMoveSerializer, MoveSerializer,
    PokemonSerializer, TypeSerializer,
)
from pgo.models import (
    CPM, Move, Pokemon, Type, TypeEffectivness,
)
from pgo.utils import (
    calculate_dph,
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
        data = self._process_data(serializer.data)

        return response.Response(data, status=status.HTTP_200_OK)

    def _process_data(self, data):
        attacker = self._get_pokemon(data.get('attacker'))
        defender = self._get_pokemon(data.get('defender'))
        qk_move = self._get_move(data.get('quick_move'))
        cc_move = self._get_move(data.get('cinematic_move'))

        attacker_cpm = CPM.objects.get(level=data.get('attacker_level')).value
        defender_cpm = CPM.objects.latest('level').value
        atk_iv = data.get('attack_iv')
        attack_multiplier = (
            (attacker.pgo_attack + atk_iv) * attacker_cpm) / (
            (defender.pgo_defense + 15) * defender_cpm)

        qk_move.damage_per_hit, qk_move.dps = self._calculate_damage(
            attack_multiplier, qk_move, self._is_stab(attacker, qk_move),
            self._get_effectivness(qk_move, defender)
        )
        cc_move.damage_per_hit, cc_move.dps = self._calculate_damage(
            attack_multiplier, cc_move, self._is_stab(attacker, cc_move),
            self._get_effectivness(cc_move, defender)
        )

        return {
            'quick_move': self._serialize(qk_move),
            'cinematic_move': self._serialize(cc_move),
            'attacker': self._serialize(attacker),
            'defender': self._serialize(defender),
        }

    def _serialize(self, obj):
        data = {}
        for key, value in obj.__dict__.items():
            if key != '_state':
                data[key] = value
        return data

    def _get_pokemon(self, id):
        return Pokemon.objects.only('name', 'pgo_attack', 'primary_type_id',
            'secondary_type_id').get(pk=id)

    def _get_move(self, id):
        return Move.objects.only(
            'name', 'power', 'duration', 'move_type_id').get(pk=id)

    def _is_stab(self, pokemon, move):
        return (
            pokemon.primary_type_id == move.move_type_id or
            pokemon.secondary_type_id == move.move_type_id
        )

    def _get_effectivness(self, move, pokemon):
        secondary_type_effectivness = 1.0
        if pokemon.secondary_type_id:
            secondary_type_effectivness = float(TypeEffectivness.objects.get(
                type_offense__id=move.move_type_id,
                type_defense__id=pokemon.secondary_type_id).effectivness.scalar)
        primary_type_effectivness = float(TypeEffectivness.objects.get(
            type_offense__id=move.move_type_id,
            type_defense__id=pokemon.primary_type_id).effectivness.scalar)
        return secondary_type_effectivness * primary_type_effectivness

    def _calculate_damage(self, attack_multiplier, move, stab, move_multiplier):
        dph = calculate_dph(move.power, attack_multiplier, stab, move_multiplier)
        dps = '{0:.2f}'.format(dph / (move.duration / 1000.0))
        return dph, dps
