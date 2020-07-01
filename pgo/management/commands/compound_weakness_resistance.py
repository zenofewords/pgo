import copy
from decimal import Decimal, getcontext

from django.core.management.base import BaseCommand

from pgo.models import Pokemon

getcontext().prec = 8


class Command(BaseCommand):
    help = 'Compound type weakness and resistance into two fields on the Pokemon object.'

    def _compound_weakness_resistance(self, pokemon):
        primary_type = pokemon.primary_type
        secondary_type = pokemon.secondary_type

        compound_weakness = self._compound_type_effectiveness({
            'primary_type': primary_type.weak,
            'secondary_type': secondary_type.weak if secondary_type else []
        })
        compound_resistance = self._compound_type_effectiveness({
            'primary_type': primary_type.resistant,
            'secondary_type': secondary_type.resistant if secondary_type else []
        })
        compound_resistance = self._compound_type_effectiveness({
            'primary_type': primary_type.immune,
            'secondary_type': secondary_type.immune if secondary_type else []
        }, compound_resistance)

        resistance_placeholder = copy.deepcopy(compound_resistance)
        weakness_placeholder = copy.deepcopy(compound_weakness)
        [self._compound_effectiveness(
            compound_resistance,
            x, y) for x, y in compound_weakness.items() if x in compound_resistance]
        [compound_weakness.pop(x) for x in resistance_placeholder if x in compound_weakness]

        pokemon.compound_resistance = self._filter_neutral_values(
            resistance_placeholder, compound_resistance)
        pokemon.compound_weakness = self._filter_neutral_values(
            weakness_placeholder, compound_weakness)
        pokemon.save()

    def _compound_type_effectiveness(self, type_effectiveness, compound_effectiveness={}):
        compound_effectiveness = compound_effectiveness if compound_effectiveness else {}

        for values in type_effectiveness['primary_type']:
            if values[0] not in compound_effectiveness:
                compound_effectiveness.update({
                    values[0]: Decimal(values[1])
                })
            else:
                compound_effectiveness[values[0]] = (
                    Decimal(compound_effectiveness[values[0]]) * Decimal(values[1])
                )

        for values in type_effectiveness['secondary_type']:
            if values[0] not in compound_effectiveness:
                compound_effectiveness.update({
                    values[0]: Decimal(values[1])
                })
            else:
                compound_effectiveness[values[0]] = (
                    Decimal(compound_effectiveness[values[0]]) * Decimal(values[1])
                )
        return compound_effectiveness

    def _compound_effectiveness(self, data, x, y):
        data[x] = data[x] * y

    def _filter_neutral_values(self, target, source):
        target.clear()
        [target.update({x: str(y)}) for x, y in source.items() if y != Decimal('1.0')]
        return target

    def handle(self, *args, **options):
        for pokemon in Pokemon.objects.all():
            self._compound_weakness_resistance(pokemon)
