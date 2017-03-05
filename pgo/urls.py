from __future__ import unicode_literals

from django.conf.urls import url

from pgo.views import (
    PGoHomeView, PokemonDetailView, PokemonListView, MoveDetailView,
    MoveListView,
)


urlpatterns = (
    url(r'^moves/(?P<slug>[\w|\W]+)$',
        MoveDetailView.as_view(), name='move-detail'),
    url(r'^moves/$', MoveListView.as_view(), name='move-list'),
    url(r'^pokemon/(?P<slug>[\w|\W]+)$',
        PokemonDetailView.as_view(), name='pokemon-detail'),
    url(r'^pokemon/$', PokemonListView.as_view(), name='pokemon-list'),
    url(r'^$', PGoHomeView.as_view(), name='pgo-home'),
)
