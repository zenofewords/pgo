from __future__ import unicode_literals

from rest_framework import routers

from pgo.api.views import (
    MoveViewSet, PokemonViewSet, TypeViewSet, PokemonSimpleViewSet,
)


pgo_router = routers.DefaultRouter()

pgo_router.register(r'moves', MoveViewSet)
pgo_router.register(r'pokemon', PokemonViewSet)
pgo_router.register(r'types', TypeViewSet)
pgo_router.register(r'simple/pokemon', PokemonSimpleViewSet, 'simple-pokemon')
