from __future__ import unicode_literals

import csv
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from pgo.models import Pokemon, PokemonMove, Move, Type


class Command(BaseCommand):
    help = 'Import pokemon from a .csv file.'

    def add_arguments(self, parser):
        parser.add_argument('path', nargs='?', type=str)

    def handle(self, *args, **options):
        path = '{0}{1}'.format(settings.BASE_DIR, '/gen4.csv')
        file_path = options.get('path') if options.get('path') else path

        quick_move = Move.objects.get(slug='tackle')
        cinematic_move = Move.objects.get(slug='struggle')

        with open(file_path) as csvfile:
            reader = csv.reader(csvfile)

            for row in reader:
                slug = slugify(row[1].strip())
                p, _ = Pokemon.objects.get_or_create(slug=slug)

                p.number = row[0].strip()
                p.name = row[1].strip()
                p.slug = slugify(row[1].strip())
                p.primary_type = Type.objects.get(slug=slugify(row[2].strip()))

                secondary_type_slug = slugify(row[3].strip())
                if secondary_type_slug:
                    p.secondary_type = Type.objects.get(slug=secondary_type_slug)
                p.pgo_stamina = int(row[4].strip())
                p.pgo_attack = int(row[5].strip())
                p.pgo_defense = int(row[6].strip())
                p.maximum_cp = Decimal(row[7].strip())

                pokemon_quick_move, _ = PokemonMove.objects.get_or_create(
                    pokemon=p, move=quick_move)
                p.quick_moves.add(pokemon_quick_move)

                pokemon_cinematic_move, _ = PokemonMove.objects.get_or_create(
                    pokemon=p, move=cinematic_move)
                p.cinematic_moves.add(pokemon_cinematic_move)

                p.save()
