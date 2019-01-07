from __future__ import unicode_literals

import json
from decimal import Decimal, InvalidOperation, getcontext

from django.apps import apps
from django.utils.text import slugify
from django.views.generic import (
    TemplateView, RedirectView,
)

from pgo.mixins import ListViewOrderingMixin
from pgo.models import (
    CPM,
    Friendship,
    Move,
    Pokemon,
    RaidTier,
    WeatherCondition,
)

from zenofewords.models import SiteNotification


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
        defender_cpm_data = (
            list(RaidTier.objects.order_by('order').values_list('tier', 'raid_cpm__value')) +
            list(CPM.objects.filter(level=40, raid_cpm=False).values_list('level', 'value'))
        )

        data = {
            'pokemon_data': Pokemon.objects.values_list('id', 'name', 'pgo_attack', 'pgo_defense'),
            'attack_iv_range': list(range(15, -1, -1)),
            'weather_condition_data': WeatherCondition.objects.values_list('id', 'name'),
            'friendship': Friendship.objects.all(),
            'defender_cpm_data': defender_cpm_data,
            'initial_data': self.initial_data,
            'site_notifications': SiteNotification.objects.all(),
        }
        context.update(data)
        return context

    def _get_object_id(self, model_name, value):
        try:
            return int(value)
        except ValueError:
            model = apps.get_model('pgo', model_name)
            return model.objects.get(slug=slugify(value)).pk


class BreakpointCalculatorView(CalculatorInitialDataMixin):
    template_name = 'pgo/breakpoint_calc.html'

    def _process_get_params(self, params):
        getcontext().prec = 11

        return {
            'attacker': self._get_object_id('Pokemon', params.get('attacker')),
            'attacker_level': float(params.get('attacker_level')),
            'attacker_quick_move': self._get_object_id(
                'Move', params.get('attacker_quick_move')),
            'attacker_cinematic_move': self._get_object_id(
                'Move', params.get('attacker_cinematic_move')),
            'attacker_atk_iv': int(params.get('attacker_atk_iv')),
            'weather_condition': self._get_object_id(
                'WeatherCondition', params.get('weather_condition')),
            'friendship_boost': str(params.get('friendship_boost')),
            'defender': self._get_object_id('Pokemon', params.get('defender')),
            'defender_quick_move': self._get_object_id(
                'Move', params.get('defender_quick_move')),
            'defender_cinematic_move': self._get_object_id(
                'Move', params.get('defender_cinematic_move')),
            'defender_cpm': str(Decimal(params.get('defender_cpm'))),
            'tab': slugify(params.get('tab', 'breakpoints')),
        }


class GoodToGoView(CalculatorInitialDataMixin):
    template_name = 'pgo/good_to_go.html'

    def _process_get_params(self, params):
        return {
            'attacker': self._get_object_id('Pokemon', params.get('attacker')),
            'attack_iv': int(params.get('attack_iv')),
            'quick_move': self._get_object_id('Move', params.get('quick_move')),
            'cinematic_move': self._get_object_id('Move', params.get('cinematic_move')),
            'weather_condition': self._get_object_id(
                'WeatherCondition', params.get('weather_condition')),
            'friendship_boost': str(params.get('friendship_boost')),
            'tier_3_6_raid_bosses': bool(params.get('tier_3_6_raid_bosses') == 'true'),
            'tier_1_2_raid_bosses': bool(params.get('tier_1_2_raid_bosses') == 'true'),
            'relevant_defenders': bool(params.get('relevant_defenders') == 'true'),
        }


class PvPView(TemplateView):
    template_name = 'pgo/pvp.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pokemon_list'] = Pokemon.objects.select_related('primary_type', 'secondary_type')
        return context


class PokemonListView(ListViewOrderingMixin):
    template_name = 'pgo/pokemon_list.html'
    model = Pokemon
    default_ordering = ('number', 'name',)
    ordering_fields = (
        'number', 'slug', 'primary_type', 'secondary_type',
        'pgo_attack', 'pgo_defense', 'pgo_stamina', 'maximum_cp'
    )


class MoveListView(ListViewOrderingMixin):
    template_name = 'pgo/move_list.html'
    model = Move
    default_ordering = '-category'
    ordering_fields = (
        'slug', 'category', 'move_type', 'power', 'energy_delta', 'duration',
        'damage_window_start', 'damage_window_end', 'dps', 'eps',
        'pvp_power', 'pvp_energy_delta', 'pvp_duration', 'dpt', 'ept', 'dpe',
    )
