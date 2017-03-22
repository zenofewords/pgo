from __future__ import unicode_literals

from django.views.generic import (
    DetailView, ListView, TemplateView,
)

from pgo.models import (
    Pokemon, Move, MoveSet, Type,
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

    def get_context_data(self, **kwargs):
        context = super(PokemonDetailView, self).get_context_data(**kwargs)

        context['movesets'] = MoveSet.objects.filter(pokemon=self.object)
        return context


class MoveListView(ListView):
    model = Move

    def get_queryset(self):
        return self.model.objects.select_related('move_type')


class MoveDetailView(DetailView):
    model = Move


class TypeListView(ListView):
    model = Type


class TypeDetailView(DetailView):
    model = Type


class MoveSetListView(ListView):
    model = MoveSet


class MoveSetDetailView(DetailView):
    model = DetailView
