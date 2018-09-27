from __future__ import unicode_literals

from decimal import Decimal, InvalidOperation
from math import pow, sqrt
from operator import itemgetter

from django.core.management.base import BaseCommand

from pgo.models import (
    CPM, Pokemon, RaidBoss, RaidBossStatus, TopCounter, WeatherCondition,
)
from pgo.utils import (
    calculate_dph, calculate_weave_damage, determine_move_effectivness, is_move_stab,
)
UNRELEASED_POKEMON = [
    'clamperl',
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
        weather_conditions = WeatherCondition.objects.all()

        raid_boss_qs = RaidBoss.objects.filter(status=RaidBossStatus.OFFICIAL)
        if self.options['defenders']:
            raid_boss_qs = raid_boss_qs.filter(pokemon__slug__in=self.options['defenders'])

        # loop to death
        for weather_condition in weather_conditions:
            boosted_types = weather_condition.types_boosted.values_list('pk', flat=True)

            for raid_boss in raid_boss_qs:
                self._create_top_counters(raid_boss, weather_condition.pk, boosted_types)

    def _create_top_counters(self, raid_boss, weather_condition_id, boosted_types):
        for attacker in self.attackers:
            try:
                tc = TopCounter.objects.get(
                    defender_id=raid_boss.pokemon.pk,
                    defender_cpm=raid_boss.raid_tier.raid_cpm.value,
                    weather_condition_id=weather_condition_id,
                    counter_id=attacker.pk,
                )
            except TopCounter.DoesNotExist as e:
                tc = TopCounter(
                    defender_id=raid_boss.pokemon.pk,
                    defender_cpm=raid_boss.raid_tier.raid_cpm.value,
                    weather_condition_id=weather_condition_id,
                    counter_id=attacker.pk,
                )

            multiplier = (
                ((attacker.pgo_attack + 15) * self.max_cpm) /
                ((raid_boss.pokemon.pgo_defense + 15) * raid_boss.raid_tier.raid_cpm.value)
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
                        multiplier, boosted_types, attacker, raid_boss.pokemon, quick_move, cinematic_move)
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
            help='Expects a list of defender slugs (--defender="slug" --defender="slug2"',
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
