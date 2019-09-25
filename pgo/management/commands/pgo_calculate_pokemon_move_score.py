from django.core.management.base import BaseCommand

from pgo.models import (
    PokemonMove,
    Moveset,
)
from pgo.utils import calculate_pokemon_move_score


class Command(BaseCommand):
    help = '''
        Iterate through pokemon movesets and create the PokemonMove objects, then connect them to
        the Moveset object.

        Score moves based on the moveset's weave damage value.
    '''

    def handle(self, *args, **options):
        # reset scores
        PokemonMove.objects.update(score=0)
        for moveset in Moveset.objects.all():
            calculate_pokemon_move_score(moveset)
