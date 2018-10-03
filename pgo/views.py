from __future__ import unicode_literals

import json
from decimal import Decimal, InvalidOperation, getcontext

from django.apps import apps
from django.utils.text import slugify
from django.views.generic import (
    TemplateView, RedirectView,
)

from pgo.models import (
    CPM, Friendship, Pokemon, Move, RaidTier, WeatherCondition,
)


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
