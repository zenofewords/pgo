from __future__ import unicode_literals

import csv

from django.conf import settings
from django.core.management.base import BaseCommand

from pgo.models import Pokemon


class Command(BaseCommand):
    help = 'Import original pokemon stats from a .csv file.'

    def add_arguments(self, parser):
        parser.add_argument('path', nargs='?', type=str)

    def handle(self, *args, **options):
        path = '{0}{1}'.format(settings.BASE_DIR, '/pgo/resources/stats.csv')
        file_path = options.get('path') if options.get('path') else path

        with open(file_path, 'rb') as csvfile:
            csv_rows = csv.reader(csvfile, delimiter=b',', quotechar=b'|')

            for row in list(csv_rows)[:251]:
                p = Pokemon.objects.get(number=row[0].strip())
                p.stamina = row[4].strip()
                p.attack = row[5].strip()
                p.defense = row[6].strip()
                p.special_attack = row[7].strip()
                p.special_defense = row[8].strip()
                p.speed = row[9].strip()
                p.save()
