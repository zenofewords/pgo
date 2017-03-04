from __future__ import unicode_literals

from django.conf.urls import url

from pgo.views import (
    PokemonDetailView, PokemonListView
)


urlpatterns = (
    url(r'^pokemon/(?P<slug>[\w|\W]+)$',
        PokemonDetailView.as_view(), name='pokemon-detail'),
    url(r'^$', PokemonListView.as_view(), name='pokemon-list'),
)
