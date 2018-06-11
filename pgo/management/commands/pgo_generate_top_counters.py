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
    'jirachi',
    'celebi',
]


class Command(BaseCommand):
    help = 'Populate the TopCounter model by generating a list of top counters for each defender.'

    def _execute(self):
        if self.options['attackers']:
            self.attackers = Pokemon.objects.filter(slug__in=self.options['attackers'])
        else:
            self.attackers = Pokemon.objects.filter(
                    pgo_stamina__gte=100,
                    pgo_attack__gte=180
                ).exclude(
                    slug__in=UNRELEASED_POKEMON
                ).order_by('-pgo_attack')[:120]

        self.max_cpm = CPM.gyms.last().value
        defender_cpm_list = [x.value for x in CPM.raids.distinct('value').order_by('-value')]
        defender_cpm_list.append(self.max_cpm)
        weather_conditions = WeatherCondition.objects.all()

        if self.options['defenders']:
            defenders = Pokemon.objects.filter(slug__in=self.options['defenders'])
        else:
            defenders = Pokemon.objects.exclude(slug__in=UNRELEASED_POKEMON)

        # loop to death
        for cpm in defender_cpm_list:
            for weather_condition in weather_conditions:
                boosted_types = weather_condition.types_boosted.values_list('pk', flat=True)

                for defender in defenders:
                    self._create_top_counters(defender, weather_condition.pk, boosted_types, cpm)

    def _create_top_counters(self, defender, weather_condition_id, boosted_types, defender_cpm):
        for attacker in self.attackers:
            try:
                tc = TopCounter.objects.get(
                    defender_id=defender.pk,
                    defender_cpm=defender_cpm,
                    weather_condition_id=weather_condition_id,
                    counter_id=attacker.pk,
                )
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
            quick_move_options = self.options['quick_moves']
            quick_moves = (
                attacker.quick_moves.filter(slug__in=quick_move_options)
                if quick_move_options else attacker.quick_moves.all()
            )
            cinematic_move_options = self.options['cinematic_moves']
            cinematic_moves = (
                attacker.cinematic_moves.filter(slug__in=cinematic_move_options)
                if cinematic_move_options else attacker.cinematic_moves.all()
            )

            moveset_data = []
            for quick_move in quick_moves:
                for cinematic_move in cinematic_moves:
                    dps = self._calculate_dps(
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

    def add_arguments(self, parser):
        parser.add_argument(
            '--attacker',
            action='append',
            dest='attackers',
            default=[],
            help='Expects a list of attacker slugs (--attacker="slug" --attacker="slug2"',
        )
        parser.add_argument(
            '--defender',
            action='append',
            dest='defenders',
            default=[],
            help='Expects a list of defender slugs',
        )
        parser.add_argument(
            '--quick_move',
            action='append',
            dest='quick_moves',
            default=[],
            help='Expects a list of quick move slugs',
        )
        parser.add_argument(
            '--cinematic_move',
            action='append',
            dest='cinematic_moves',
            default=[],
            help='Expects a list of cinematic move slugs',
        )

    def handle(self, *args, **options):
        self.options = options
        self._execute()
