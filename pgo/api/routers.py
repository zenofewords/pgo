from rest_framework import routers

from pgo.api.views import (
    MoveViewSet, PokemonViewSet, TypeViewSet,
)


pgo_router = routers.DefaultRouter()

pgo_router.register(r'moves', MoveViewSet)
pgo_router.register(r'pokemon', PokemonViewSet)
pgo_router.register(r'types', TypeViewSet)
