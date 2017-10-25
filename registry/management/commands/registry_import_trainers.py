from __future__ import unicode_literals

import csv

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

from registry.models import Trainer, Team, Town


class Command(BaseCommand):
    help = 'Import trainers from a .csv file.'

    def add_arguments(self, parser):
        parser.add_argument('path', nargs='?', type=str)

    def handle(self, *args, **options):
        path = '{0}{1}'.format(settings.BASE_DIR, '/registry/resources/trainers.csv')
        file_path = options.get('path') if options.get('path') else path

        with open(file_path, 'rb') as csvfile:
            csv_rows = csv.reader(csvfile, delimiter=b',', quotechar=b'|')

            teams = Team.objects.values_list('pk', 'slug')
            towns = dict((t.slug, t) for t in Town.objects.all())

            for row in list(csv_rows)[1:]:
                t = Trainer()
                t.nickname = row[0]
                t.team_id = teams.get(slug=row[1].lower())[0]
                t.level = row[2]

                try:
                    t.save()
                except IntegrityError:
                    continue

                try:
                    town = towns[row[4].lower()]
                except IndexError:
                    town = towns['zagreb']

                t.towns.add(town)
                t.save()
