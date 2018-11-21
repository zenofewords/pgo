from __future__ import unicode_literals

from operator import itemgetter

from django.core.management.base import BaseCommand

from pgo.models import (
    CPM, Pokemon, RaidBoss, RaidBossStatus, TopCounter, WeatherCondition, Generation,
)
from pgo.utils import (
    calculate_dph, calculate_cycle_dps, determine_move_effectivness, is_move_stab,
)

DEFENDER_LIST = [
    'blissey',
    'lugia',
    'cresselia',
    'giratina-altered',
    'giratina',
    'chansey',
    'regirock',
    'regice',
    'arceus-water',
    'arceus-steel',
    'arceus-rock',
    'arceus-psychic',
    'arceus-poison',
    'arceus-ice',
    'arceus-ground',
    'arceus-grass',
    'arceus-ghost',
    'arceus-flying',
    'arceus-fire',
    'arceus-fighting',
    'arceus-fairy',
    'arceus-electric',
    'arceus-dragon',
    'arceus-dark',
    'arceus-bug',
    'arceus',
    'snorlax',
    'registeel',
    'giratina-origin',
    'suicune',
    'ho-oh',
    'umbreon',
    'steelix',
    'uxie',
    'articuno',
    'lapras',
    'rhyperior',
    'milotic',
    'shaymin-land',
    'shaymin',
    'mew',
    'manaphy',
    'jirachi',
    'celebi',
    'slaking',
    'latias',
    'kyogre',
    'groudon',
    'tyranitar',
    'regigigas',
    'garchomp',
    'relicanth',
    'hippowdon',
    'deoxys-defense',
    'vaporeon',
    'heatran',
    'bastiodon',
    'aggron',
    'lickilicky',
    'metagross',
    'dialga',
    'togekiss',
    'entei',
    'probopass',
    'walrein',
    'miltank',
    'tangrowth',
    'dragonite',
    'palkia',
    'torterra',
    'wobbuffet',
    'raikou',
    'mesprit',
    'latios',
    'gliscor',
    'gyarados',
    'muk-alola',
    'muk',
    'rhydon',
    'tentacruel',
    'swampert',
    'mewtwo',
    'blastoise',
    'slowking',
    'slowbro',
    'cradily',
    'kangaskhan',
    'meganium',
    'zapdos',
    'donphan',
    'hypno',
    'poliwrath',
    'golem-alola',
    'golem',
    'moltres',
    'shaymin-sky',
    'feraligatr',
    'forretress',
    'politoed',
    'skarmory',
    'mantine',
    'lanturn',
    'empoleon',
    'dewgong',
    'altaria',
    'tropius',
    'salamence',
    'rayquaza',
    'venusaur',
    'nidoqueen',
    'swalot',
    'grumpig',
    'leafeon',
    'porygon2',
    'bronzong',
    'claydol',
    'mamoswine',
    'sandslash-alola',
    'magnezone',
    'crobat',
    'kingdra',
    'noctowl',
    'cloyster',
    'clefable',
    'ampharos',
    'torkoal',
    'gastrodon-west-sea',
    'gastrodon-east-sea',
    'gastrodon',
    'drapion',
    'omastar',
    'hariyama',
    'arcanine',
    'azumarill',
    'ninetales-alola',
    'whiscash',
    'darkrai',
    'heracross',
    'bellossom',
    'shuckle',
    'ninetales',
    'munchlax',
    'ludicolo',
    'glaceon',
    'tauros',
    'jumpluff',
    'exeggutor-alola',
    'gardevoir',
    'gallade',
]


class Command(BaseCommand):
    help = 'Populate the TopCounter model by generating a list of top counters for each defender.'

    def _execute(self):
        pokemon_qs = Pokemon.objects.all()
        defenders_qs = Pokemon.objects.include_uninmplemented().filter(slug__in=DEFENDER_LIST)

        if self.options['attackers']:
            self.attackers = pokemon_qs.filter(slug__in=self.options['attackers'])
        else:
            self.attackers = pokemon_qs.filter(
                pgo_stamina__gte=100,
                pgo_attack__gte=180
            ).order_by('-pgo_attack')[:120]

        weather_conditions = WeatherCondition.objects.all()

        raid_boss_qs = RaidBoss.objects.filter(status=RaidBossStatus.OFFICIAL)
        if self.options['defenders']:
            raid_boss_qs = raid_boss_qs.filter(pokemon__slug__in=self.options['defenders'])

        for weather_condition in weather_conditions:
            boosted_types = weather_condition.types_boosted.values_list('pk', flat=True)

            for raid_boss in raid_boss_qs:
                self._create_top_counters(raid_boss.pokemon, weather_condition.pk, boosted_types)

            for pokemon in defenders_qs:
                self._create_top_counters(pokemon, weather_condition.pk, boosted_types)

    def _create_top_counters(self, pokemon, weather_condition_id, boosted_types):
        for attacker in self.attackers:
            tc, created = TopCounter.objects.get_or_create(
                defender_id=pokemon.pk,
                weather_condition_id=weather_condition_id,
                counter_id=attacker.pk,
                defaults={
                    'highest_dps': 0,
                    'moveset_data': {},
                }
            )

            if not created and not self.options['update']:
                return

            multiplier = (attacker.pgo_attack + 15) / (pokemon.pgo_defense + 15)
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
        parser.add_argument(
            '--update',
            dest='update',
            default=False,
            help='Update existing top counters (--update=True)'
        )

    def handle(self, *args, **options):
        self.options = options
        self._execute()
