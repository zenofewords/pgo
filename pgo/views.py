from __future__ import unicode_literals

from django.views.generic import (
    DetailView, ListView
)

from pgo.models import Pokemon


class PokemonListView(ListView):
    model = Pokemon
    paginate_by = 300

    def get_queryset(self):
        return self.model.objects.select_related('primary_type', 'secondary_type')


class PokemonDetailView(DetailView):
    model = Pokemon

    def get_queryset(self):
        return self.model.objects.select_related(
            'primary_type', 'secondary_type').prefetch_related(
            'quick_moves', 'cinematic_moves')
