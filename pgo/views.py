from __future__ import unicode_literals

from django.views.generic import (
    DetailView, ListView, TemplateView,
)

from pgo.models import (
    CPM, Pokemon, Move, MoveSet, Type,
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

    def get_queryset(self):
        return self.model.objects.select_related('pokemon')


class MoveSetDetailView(DetailView):
    model = DetailView


class AttackProficiencyView(TemplateView):
    template_name = 'pgo/attack_proficiency.html'

    def get_context_data(self, **kwargs):
        context = super(AttackProficiencyView, self).get_context_data(**kwargs)

        context['pokemon_data'] = Pokemon.objects.values_list('id', 'name')
        context['max_pokemon_level'] = CPM.objects.latest('level').level
        return context
