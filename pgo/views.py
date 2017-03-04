from __future__ import unicode_literals

from django.views.generic import (
    DetailView, ListView
)

from pgo.models import Pokemon


class PokemonListView(ListView):
    model = Pokemon


class PokemonDetailView(DetailView):
    model = Pokemon
