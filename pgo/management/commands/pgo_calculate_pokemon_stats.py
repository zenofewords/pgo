from django.core.management.base import BaseCommand

from pgo.models import Pokemon
from pgo.utils import calculate_pokemon_stats


class Command(BaseCommand):
    help = 'Calculate stats for all currently listed pokemon.'

    def handle(self, *args, **options):
        for pokemon in Pokemon.objects.all():
            pokemon = calculate_pokemon_stats(pokemon)
            pokemon.save()
