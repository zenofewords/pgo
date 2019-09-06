from django.urls import path

from pgo.views import (
    BreakpointCalcRedirectView,
    BreakpointCalculatorView,
    GoodToGoView,
    MoveDetailView,
    MoveListView,
    PokemonDetailView,
    PokemonListView,
)

app_name = 'pgo'
urlpatterns = (
    path('pgo', BreakpointCalcRedirectView.as_view(), name='redirect'),
    path('breakpoint-calc/', BreakpointCalculatorView.as_view(), name='breakpoint-calc'),
    path('good-to-go/', GoodToGoView.as_view(), name='good-to-go'),

    path('pokemon/<slug:slug>', PokemonDetailView.as_view(), name='pokemon-detail'),
    path('pokemon/', PokemonListView.as_view(), name='pokemon-list'),
    path('moves/<slug:slug>', MoveDetailView.as_view(), name='move-detail'),
    path('moves/', MoveListView.as_view(), name='move-list'),

    path('', BreakpointCalculatorView.as_view(), name='breakpoint-calc'),
)
