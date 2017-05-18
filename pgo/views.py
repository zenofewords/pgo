from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import (
    DetailView, ListView, TemplateView,
)

from pgo.models import (
    Pokemon, Move, Moveset, Type, DEFAULT_ORDER
)


class SortMixin(ListView):
    def get(self, request, *args, **kwargs):
        sort_by = request.GET.get('sort_by')
        sort_key = request.GET.get('sort_key')

        if sort_by:
            if sort_key == sort_by:
                self.sort_by = ('-{}'.format(sort_by),)
            else:
                self.sort_by = (sort_by,)
        else:
            self.sort_by = self._get_default_order()
        return super(SortMixin, self).get(request, args, kwargs)

    def _get_default_order(self):
        return DEFAULT_ORDER[self.model.__name__]

    def get_queryset(self):
        if self.sort_by:
            return self.model.objects.order_by(*self.sort_by)
        return self.model.objects

    def get_context_data(self, **kwargs):
        context = super(SortMixin, self).get_context_data(**kwargs)
        context['sort_key'] = '&'.join(self.sort_by)
        return context


class PGoHomeView(TemplateView):
    template_name = 'pgo/pgo_home.html'


class PokemonListView(SortMixin):
    model = Pokemon
    paginate_by = 151

    def dispatch(self, request, *args, **kwargs):
        pokemon_id = int(request.GET.get('pokemon_id', 0))
        if pokemon_id != 0:
            pokemon_slug = get_object_or_404(Pokemon, pk=pokemon_id).slug
            return redirect(reverse('pgo:pokemon-detail', kwargs={'slug': pokemon_slug}))

        self.type_id = int(request.GET.get('type_id', 0))
        return super(PokemonListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super(PokemonListView, self).get_queryset()
        if self.type_id != 0:
            qs = qs.filter(primary_type_id=self.type_id)

        return qs.select_related('primary_type', 'secondary_type')

    def get_context_data(self, **kwargs):
        context = super(PokemonListView, self).get_context_data(**kwargs)
        data = {
            'pokemon_data': self.model.objects.values_list('id', 'name'),
            'types': Type.objects.values_list('id', 'name'),
            'type_id': self.type_id,
        }
        context.update(data)
        return context


class PokemonDetailView(DetailView):
    model = Pokemon

    def get_queryset(self):
        return self.model.objects.select_related(
            'primary_type', 'secondary_type').prefetch_related(
            'quick_moves', 'cinematic_moves')

    def get_context_data(self, **kwargs):
        context = super(PokemonDetailView, self).get_context_data(**kwargs)

        context['movesets'] = Moveset.objects.filter(pokemon=self.object)
        return context


class MoveListView(SortMixin):
    model = Move

    def get(self, request, *args, **kwargs):
        self.move_id = int(request.GET.get('move_id', 0))

        return super(MoveListView, self).get(request, args, kwargs)

    def get_queryset(self):
        qs = super(MoveListView, self).get_queryset()

        if self.move_id != 0:
            qs = qs.filter(id=self.move_id)
        return qs.select_related('move_type')

    def get_context_data(self, **kwargs):
        context = super(MoveListView, self).get_context_data(**kwargs)
        data = {
            'move_data': self.model.objects.values_list('id', 'name'),
            'move_id': self.move_id,
        }
        context.update(data)
        return context


class MoveDetailView(DetailView):
    model = Move


class TypeListView(ListView):
    model = Type


class TypeDetailView(DetailView):
    model = Type


class MovesetListView(SortMixin):
    model = Moveset
    template_name = 'pgo/moveset_list.html'
    paginate_by = 200

    def get(self, request, *args, **kwargs):
        self.pokemon_id = int(request.GET.get('pokemon_id', 0))
        self.moveset_filter = request.GET.get('moveset-filter')

        return super(MovesetListView, self).get(request, args, kwargs)

    def get_queryset(self):
        qs = super(
            MovesetListView, self).get_queryset().select_related('pokemon')

        if self.pokemon_id != 0:
            qs = qs.filter(pokemon_id=self.pokemon_id)
        if self.moveset_filter:
            qs = qs.filter(key__icontains=self.moveset_filter)
        return qs

    def get_context_data(self, **kwargs):
        context = super(MovesetListView, self).get_context_data(**kwargs)
        data = {
            'pokemon_data': Pokemon.objects.values_list('id', 'name'),
            'pokemon_id': self.pokemon_id,
            'moveset_filter': self.moveset_filter,
        }
        context.update(data)
        return context


class MovesetDetailView(DetailView):
    model = DetailView


class AttackProficiencyView(TemplateView):
    template_name = 'pgo/attack_proficiency.html'

    def get_context_data(self, **kwargs):
        context = super(AttackProficiencyView, self).get_context_data(**kwargs)

        context['pokemon_data'] = Pokemon.objects.values_list(
            'id', 'name', 'pgo_attack', 'pgo_defense')
        return context
