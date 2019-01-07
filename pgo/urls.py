from __future__ import unicode_literals

from django.conf.urls import url

from pgo.views import (
    BreakpointCalcRedirectView,
    BreakpointCalculatorView,
    GoodToGoView,
    MoveListView,
    PokemonListView,
    PvPView,
)

app_name = 'pgo'
urlpatterns = (
    url(r'^pgo', BreakpointCalcRedirectView.as_view(), name='breakpoint-calc-redirect'),
    url(r'^breakpoint-calc/$', BreakpointCalculatorView.as_view(), name='breakpoint-calc'),
    url(r'^good-to-go/$', GoodToGoView.as_view(), name='good-to-go'),
    url(r'^pv3p/$', PvPView.as_view(), name='pvp'),

    url(r'^pokemon/$', PokemonListView.as_view(), name='pokemon-list'),
    url(r'^moves/$', MoveListView.as_view(), name='move-list'),
    url(r'^$', BreakpointCalculatorView.as_view(), name='breakpoint-calc'),
)
