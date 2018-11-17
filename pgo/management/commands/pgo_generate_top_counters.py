from __future__ import unicode_literals

from operator import itemgetter

from django.core.management.base import BaseCommand

from pgo.models import (
    CPM, Pokemon, RaidBoss, RaidBossStatus, TopCounter, WeatherCondition, Generation,
)
from pgo.utils import (
    calculate_dph, calculate_cycle_dps, determine_move_effectivness, is_move_stab,
)

class Command(BaseCommand):
    help = 'Populate the TopCounter model by generating a list of top counters for each defender.'

    def _execute(self):
        pokemon_qs = Pokemon.objects.all()

        if self.options['attackers']:
            self.attackers = pokemon_qs.filter(slug__in=self.options['attackers'])
        else:
            self.attackers = pokemon_qs.filter(
                pgo_stamina__gte=100,
                pgo_attack__gte=180
            ).order_by('-pgo_attack')[:120]

        self.max_cpm = CPM.gyms.last().value
        weather_conditions = WeatherCondition.objects.all()

        raid_boss_qs = RaidBoss.objects.filter(status=RaidBossStatus.OFFICIAL)
        if self.options['defenders']:
            raid_boss_qs = raid_boss_qs.filter(pokemon__slug__in=self.options['defenders'])

        for weather_condition in weather_conditions:
            boosted_types = weather_condition.types_boosted.values_list('pk', flat=True)

            if self.options['raid_bosses']:
                for raid_boss in raid_boss_qs:
                    self._create_top_counters(
                        raid_boss.pokemon,
                        weather_condition.pk,
                        boosted_types,
                        raid_boss.raid_tier.raid_cpm.value
                    )

            # for pokemon in pokemon_qs:
            #     self._create_top_counters(
            #         pokemon, weather_condition.pk, boosted_types, self.max_cpm)

    def _create_top_counters(self, pokemon, weather_condition_id, boosted_types, cpm):
        for attacker in self.attackers:
            try:
                tc = TopCounter.objects.get(
                    defender_id=pokemon.pk,
                    defender_cpm=cpm,
                    weather_condition_id=weather_condition_id,
                    counter_id=attacker.pk,
                )
            except TopCounter.DoesNotExist as e:
                tc = TopCounter(
                    defender_id=pokemon.pk,
                    defender_cpm=cpm,
                    weather_condition_id=weather_condition_id,
                    counter_id=attacker.pk,
                )

            multiplier = (
                ((attacker.pgo_attack + 15) * self.max_cpm) /
                ((pokemon.pgo_defense + 15) * cpm)
            )
            quick_move_options = self.options['quick_moves']
            pokemon_quick_moves = (
                attacker.quick_moves.filter(slug__in=quick_move_options)
                if quick_move_options else attacker.quick_moves.all()
            )
            cinematic_move_options = self.options['cinematic_moves']
            pokemon_cinematic_moves = (
                attacker.cinematic_moves.filter(slug__in=cinematic_move_options)
                if cinematic_move_options else attacker.cinematic_moves.all()
            )

            moveset_data = []
            for pokemon_quick_move in pokemon_quick_moves:
                for pokemon_cinematic_move in pokemon_cinematic_moves:
                    dps = self._calculate_dps(
                        multiplier, boosted_types, attacker,
                        pokemon, pokemon_quick_move.move, pokemon_cinematic_move.move
                    )
                    moveset_data.append(
                        (dps, pokemon_quick_move.move.name, pokemon_cinematic_move.move.name,))

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
        return calculate_cycle_dps(quick_move, cinematic_move)

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
        parser.add_argument(
            '--raid_bosses',
            dest='raid_bosses',
            default=True,
            help='To skip raid bosses (--raid_bosses='')'
        )

    def handle(self, *args, **options):
        self.options = options
        self._execute()
