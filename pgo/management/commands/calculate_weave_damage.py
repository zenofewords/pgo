from django.core.management.base import BaseCommand

from pgo.models import Pokemon
from pgo.utils import calculate_weave_damage


class Command(BaseCommand):
    help = 'Calculate and store DPS details for all currently listed pokemon.'

    def handle(self, *args, **options):
        for pokemon in Pokemon.objects.all():
            calculate_weave_damage(pokemon)
