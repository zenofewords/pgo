from __future__ import unicode_literals

from decimal import Decimal
from math import pow, sqrt

from django.core.management.base import BaseCommand

from pgo.models import (
    CPM,
    Pokemon,
)
cpm = CPM.objects.get(level=Decimal('40.0')).value
IVs = 15


class Command(BaseCommand):
    help = 'Calculate and store CP for all currently listed pokemon.'

    def _calculate_cp(self, pokemon):
        attack = pokemon.pgo_attack + IVs
        defense = pokemon.pgo_defense + IVs
        stamina = pokemon.pgo_stamina + IVs

        pokemon.maximum_cp = (
            attack * sqrt(defense) * sqrt(stamina) * pow(cpm, 2) / 10.0
        )
        pokemon.save()

    def handle(self, *args, **options):
        for pokemon in Pokemon.objects.all():
            self._calculate_cp(pokemon)
