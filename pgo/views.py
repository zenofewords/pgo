from __future__ import unicode_literals

from django.views.generic import (
    DetailView, ListView, TemplateView,
)

from pgo.models import (
    Pokemon, Move,
)


class PGoHomeView(TemplateView):
    template_name = 'pgo/pgo_home.html'


class PokemonListView(ListView):
    model = Pokemon

    def get_queryset(self):
        return self.model.objects.select_related('primary_type', 'secondary_type')


class PokemonDetailView(DetailView):
    model = Pokemon

    def get_queryset(self):
        return self.model.objects.select_related(
            'primary_type', 'secondary_type').prefetch_related(
            'quick_moves', 'cinematic_moves')


class MoveListView(ListView):
    model = Move

    def get_queryset(self):
        return self.model.objects.select_related('move_type')


class MoveDetailView(DetailView):
    model = Move
