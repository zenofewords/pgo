import json

from decimal import Decimal, InvalidOperation, getcontext
from math import pow, sqrt, floor

from django.apps import apps
from django.utils.text import slugify
from django.views.generic import (
    DetailView,
    RedirectView,
    TemplateView,
)

from pgo.mixins import (
    ListViewOrderingMixin,
    PresetMixin,
)
from pgo.models import (
    CPM,
    Friendship,
    Move,
    Pokemon,
    PokemonMove,
    Type,
    WeatherCondition,
)
from pgo.utils import get_tier_cpm_map


class BreakpointCalcRedirectView(RedirectView):
    permanent = True
    pattern_name = 'pgo:breakpoint-calc'


class CalculatorInitialDataMixin(TemplateView):
    def get(self, request, *args, **kwargs):
        try:
            self.initial_data = json.dumps(self._process_get_params(request.GET))
        except (TypeError, ValueError, LookupError, InvalidOperation,
                Pokemon.DoesNotExist, Move.DoesNotExist, WeatherCondition.DoesNotExist):
            self.initial_data = {}
        return super(CalculatorInitialDataMixin, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CalculatorInitialDataMixin, self).get_context_data(**kwargs)
        context.update({
            'pokemon_qs': {},
            'attack_iv_range': list(range(15, -1, -1)),
            'weather_condition_data': WeatherCondition.objects.all(),
            'friendship': Friendship.objects.order_by('order'),
            'defender_cpm': get_tier_cpm_map(),
            'initial_data': self.initial_data,
        })
        return context

    def _get_object_id(self, model_name, value):
        try:
            return int(value)
        except ValueError:
            model = apps.get_model('pgo', model_name)
            return model.objects.get(slug=slugify(value)).pk

    def _get_object_slug(self, model_name, value):
        model = apps.get_model('pgo', model_name)
        return model.objects.get(slug=slugify(value)).slug


class BreakpointCalculatorView(CalculatorInitialDataMixin):
    template_name = 'pgo/breakpoint_calc.html'

    def _process_get_params(self, params):
        getcontext().prec = 11

        return {
            'attacker': self._get_object_slug('Pokemon', params.get('attacker')),
            'attacker_level': float(params.get('attacker_level')),
            'attacker_quick_move': self._get_object_id(
                'Move', params.get('attacker_quick_move')),
            'attacker_cinematic_move': self._get_object_id(
                'Move', params.get('attacker_cinematic_move')),
            'attacker_atk_iv': int(params.get('attacker_atk_iv')),
            'weather_condition': self._get_object_id(
                'WeatherCondition', params.get('weather_condition')),
            'friendship_boost': str(params.get('friendship_boost')),
            'defender': self._get_object_slug('Pokemon', params.get('defender')),
            'defender_quick_move': self._get_object_id(
                'Move', params.get('defender_quick_move')),
            'defender_cinematic_move': self._get_object_id(
                'Move', params.get('defender_cinematic_move')),
            'defender_cpm': str(Decimal(params.get('defender_cpm'))),
            'top_counter_order': str(params.get('top_counter_order')),
            'tab': slugify(params.get('tab', 'breakpoints')),
        }


class GoodToGoView(CalculatorInitialDataMixin):
    template_name = 'pgo/good_to_go.html'

    def _process_get_params(self, params):
        return {
            'attacker': self._get_object_slug('Pokemon', params.get('attacker')),
            'attack_iv': int(params.get('attack_iv')),
            'quick_move': self._get_object_id('Move', params.get('quick_move')),
            'cinematic_move': self._get_object_id('Move', params.get('cinematic_move')),
            'weather_condition': self._get_object_id(
                'WeatherCondition', params.get('weather_condition')),
            'friendship_boost': str(params.get('friendship_boost')),
            'tier_3_6_raid_bosses': bool(params.get('tier_3_6_raid_bosses') == 'true'),
            'tier_1_2_raid_bosses': bool(params.get('tier_1_2_raid_bosses') == 'true'),
        }


class PokemonListView(ListViewOrderingMixin):
    template_name = 'pgo/pokemon_list.html'
    queryset = Pokemon.objects.select_related('primary_type', 'secondary_type')
    ordering_fields = (
        'number', 'pgo_attack', 'pgo_defense', 'pgo_stamina', 'stat_product', 'maximum_cp',
    )
    values_list_args = ('slug', 'name',)


class MoveListView(ListViewOrderingMixin):
    template_name = 'pgo/move_list.html'
    queryset = Move.objects.select_related('move_type')
    ordering_fields = (
        'name', 'slug', 'category', 'move_type', 'power', 'energy_delta', 'duration',
        'damage_window_start', 'damage_window_end', 'dps', 'eps',
        'pvp_power', 'pvp_energy_delta', 'pvp_duration', 'dpt', 'ept', 'dpe',
    )
    values_list_args = ('slug', 'name',)

    def get(self, request, *args, **kwargs):
        self.preset = slugify(self.request.GET.get('preset', 'pvp'))
        self.selected_move_type = slugify(self.request.GET.get('selected-move-type', ''))
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.selected_move_type and self.selected_move_type != 'all':
            queryset = queryset.filter(move_type__slug=self.selected_move_type)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'preset': self.preset,
            'selected_move_type': self.selected_move_type,
            'move_types': Type.objects.all(),
        })
        return context


class PokemonDetailView(PresetMixin, DetailView):
    model = Pokemon

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cpm_qs = CPM.objects.filter(
            raid_cpm=False,
            level__in=[1, 15, 20, 25, 30, 35, 40]
        )
        context.update({
            'data': Pokemon.objects.values_list('slug', 'name'),
            'pokemon_stats': [(
                int(x.level),
                floor(x.value * (self.object.pgo_attack + 15)),
                floor(x.value * (self.object.pgo_defense + 15)),
                floor(x.value * (self.object.pgo_stamina + 15)),
                self._calculate_cp(float(x.value)),
            ) for x in cpm_qs.order_by('-level')],
            'pokemon_moves': PokemonMove.objects.filter(
                pokemon_id=self.object.pk
            ).select_related(
                'move__move_type',
            ).order_by(
                '-move__category', '-score',
            ),
        })
        return context

    def _calculate_cp(self, value):
        return floor(
            (self.object.pgo_attack + 15)
            * sqrt(self.object.pgo_defense + 15)
            * sqrt(self.object.pgo_stamina + 15)
            * pow(value, 2) / 10.0
        )


class MoveDetailView(PresetMixin, DetailView):
    model = Move

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        move_type = self.object.move_type
        effectiveness_effective = move_type.strong
        effectiveness_not_effective = move_type.feeble + move_type.puny

        context.update({
            'data': Move.objects.values_list('slug', 'name'),
            'effectiveness_effective': effectiveness_effective,
            'effectiveness_not_effective': effectiveness_not_effective,
            'pokemon_moves': PokemonMove.objects.filter(
                move_id=self.object.pk
            ).select_related(
                'pokemon__primary_type',
                'pokemon__secondary_type',
            ).order_by(
                '-pokemon__maximum_cp',
            ),
        })
        return context
