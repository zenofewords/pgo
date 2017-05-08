from __future__ import unicode_literals

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
        context['sort_key'] = '&amp;'.join(self.sort_by)
        return context


class PGoHomeView(TemplateView):
    template_name = 'pgo/pgo_home.html'


class PokemonListView(SortMixin):
    model = Pokemon

    def get_queryset(self):
        queryset = super(PokemonListView, self).get_queryset()
        return queryset.select_related('primary_type', 'secondary_type')


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

    def get_queryset(self):
        queryset = super(MoveListView, self).get_queryset()
        return queryset.select_related('move_type')


class MoveDetailView(DetailView):
    model = Move


class TypeListView(ListView):
    model = Type


class TypeDetailView(DetailView):
    model = Type


class MovesetListView(SortMixin):
    model = Moveset
    template_name = 'pgo/moveset_list.html'
    paginate_by = 300

    def get_queryset(self):
        queryset = super(MovesetListView, self).get_queryset()
        return queryset.select_related('pokemon')


class MovesetDetailView(DetailView):
    model = DetailView


class AttackProficiencyView(TemplateView):
    template_name = 'pgo/attack_proficiency.html'

    def get_context_data(self, **kwargs):
        context = super(AttackProficiencyView, self).get_context_data(**kwargs)

        context['pokemon_data'] = Pokemon.objects.values_list(
            'id', 'name', 'pgo_attack', 'pgo_defense')
        return context
