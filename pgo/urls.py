from __future__ import unicode_literals

from django.conf.urls import url

from pgo.views import (
    PokemonDetailView, PokemonListView, MoveDetailView, MoveListView, MovesetDetailView,
    MovesetListView, TypeDetailView, TypeListView, BreakpointCalculatorView,
    BreakpointCalcRedirectView, GoodToGoView,
)


urlpatterns = (
    url(r'^pgo', BreakpointCalcRedirectView.as_view(), name='breakpoint-calc-redirect'),
    url(r'^breakpoint-calc/$', BreakpointCalculatorView.as_view(), name='breakpoint-calc'),
    url(r'^good-to-go/$', GoodToGoView.as_view(), name='good-to-go'),
    url(r'^move/(?P<slug>[\w|\W]+)$', MoveDetailView.as_view(), name='move-detail'),
    url(r'^moves/$', MoveListView.as_view(), name='move-list'),
    url(r'^pokemon/(?P<slug>[\w|\W]+)$', PokemonDetailView.as_view(), name='pokemon-detail'),
    url(r'^pokemon/$', PokemonListView.as_view(), name='pokemon-list'),
    url(r'^type/(?P<slug>[\w]+)$', TypeDetailView.as_view(), name='type-detail'),
    url(r'^types/$', TypeListView.as_view(), name='type-list'),
    url(r'^moveset(?P<pk>[\d]+)/$', MovesetDetailView.as_view(), name='moveset-detail'),
    url(r'^movesets/$', MovesetListView.as_view(), name='moveset-list'),
)
