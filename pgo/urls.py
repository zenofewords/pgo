from __future__ import unicode_literals

from django.conf.urls import url

from pgo.views import (
    PokemonDetailView, PokemonListView, MoveDetailView,
    MoveListView, MoveSetDetailView, MoveSetListView, TypeDetailView,
    TypeListView, AttackProficiencyView,
)


urlpatterns = (
    url(r'^move/(?P<slug>[\w|\W]+)$',
        MoveDetailView.as_view(), name='move-detail'),
    url(r'^moves/$', MoveListView.as_view(), name='move-list'),
    url(r'^pokemon/(?P<slug>[\w|\W]+)$',
        PokemonDetailView.as_view(), name='pokemon-detail'),
    url(r'^pokemon/$', PokemonListView.as_view(), name='pokemon-list'),
    url(r'^type/(?P<slug>[\w]+)$',
        TypeDetailView.as_view(), name='type-detail'),
    url(r'^types/$', TypeListView.as_view(), name='type-list'),
    url(r'^moveset(?P<pk>[\d]+)/$',
        MoveSetDetailView.as_view(), name='moveset-detail'),
    url(r'^movesets/$', MoveSetListView.as_view(), name='moveset-list'),
    url(r'^$', AttackProficiencyView.as_view(), name='attack-proficiency'),
)
