from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from django.db.models import Q

from pgo.api.serializers import (
    SimpleMoveSerializer, MoveSerializer, PokemonSerializer, TypeSerializer,
)
from pgo.models import (
    Move, Pokemon, Type,
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
