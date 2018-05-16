from __future__ import unicode_literals

from decimal import Decimal, InvalidOperation
from math import pow, sqrt
from operator import itemgetter

from django.core.management.base import BaseCommand

from pgo.models import (
    CPM, Pokemon, RaidBoss, TopCounter, WeatherCondition,
)
from pgo.utils import (
    calculate_dph, calculate_weave_damage, determine_move_effectivness, is_move_stab,
)
UNRELEASED_POKEMON = [
    'clamperl',
    'deoxys',
    'gorebyss',
    'huntail',
    'kacleon',
    'nincada',
    'ninjask',
    'shedinja',
    'smeargle',
    'spinda',
]


class Command(BaseCommand):
    help = 'Populate the TopCounter model by generating a list of top counters for each defender.'

    def _execute(self):
        self.attackers = Pokemon.objects.filter(
                pgo_stamina__gte=100,
                pgo_attack__gte=180
            ).exclude(
                slug__in=UNRELEASED_POKEMON
            ).order_by('-pgo_attack')[:120]

        self.max_cpm = CPM.gyms.last().value
        defender_cpm_list = [x.value for x in CPM.raids.distinct('value').order_by('value')][:3]
        defender_cpm_list.append(self.max_cpm)
        weather_conditions = WeatherCondition.objects.filter(slug='partly-cloudy')
        defenders = Pokemon.objects.exclude(slug__in=UNRELEASED_POKEMON)

        # loop to death
        for weather_condition in weather_conditions:
            boosted_types = weather_condition.types_boosted.values_list('pk', flat=True)

            for defender in defenders:
                for cpm in defender_cpm_list:
                    self._create_top_counters(defender, weather_condition.pk, boosted_types, cpm)

    def _create_top_counters(self, defender, weather_condition_id, boosted_types, defender_cpm):
        for attacker in self.attackers:
            try:
                TopCounter.objects.get(
                    defender_id=defender.pk,
                    defender_cpm=defender_cpm,
                    weather_condition_id=weather_condition_id,
                    counter_id=attacker.pk,
                )
                # no update at this time
                continue
            except TopCounter.DoesNotExist as e:
                tc = TopCounter(
                    defender_id=defender.pk,
                    defender_cpm=defender_cpm,
                    weather_condition_id=weather_condition_id,
                    counter_id=attacker.pk,
                )

            multiplier = (
                ((attacker.pgo_attack + 15) * self.max_cpm) /
                ((defender.pgo_defense + 15) * defender_cpm)
            )
            moveset_data = []
            for quick_move in attacker.quick_moves.all():
                for cinematic_move in attacker.cinematic_moves.all():
                    dps, _ = self._calculate_dps(
                        multiplier, boosted_types, attacker, defender, quick_move, cinematic_move)
                    moveset_data.append((dps, quick_move.name, cinematic_move.name,))

            moveset_data.sort(key=itemgetter(0), reverse=True)
            tc.highest_dps = moveset_data[0][0]
            tc.moveset_data = moveset_data
            tc.save()

    def _calculate_dps(
            self, multiplier, boosted_types, attacker, defender, quick_move, cinematic_move):
        quick_move.damage_per_hit = calculate_dph(
            quick_move.power,
            multiplier,
            is_move_stab(quick_move, attacker),
            quick_move.move_type_id in boosted_types,
            determine_move_effectivness(quick_move, defender)
        )
        cinematic_move.damage_per_hit = calculate_dph(
            cinematic_move.power,
            multiplier,
            is_move_stab(cinematic_move, attacker),
            cinematic_move.move_type_id in boosted_types,
            determine_move_effectivness(cinematic_move, defender)
        )
        return calculate_weave_damage(quick_move, cinematic_move)

    def handle(self, *args, **options):
        self._execute()
