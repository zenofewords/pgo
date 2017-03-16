from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from pgo.api.serializers import (
    MoveSerializer, PokemonSerializer, TypeSerializer,
)
from pgo.models import (
    Move, Pokemon, Type,
)


class MoveViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Move.objects.all()
    serializer_class = MoveSerializer


class PokemonViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Pokemon.objects.all()
    serializer_class = PokemonSerializer


class TypeViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Type.objects.all()
    serializer_class = TypeSerializer
