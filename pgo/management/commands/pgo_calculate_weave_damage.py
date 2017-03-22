from __future__ import unicode_literals

from math import floor

from django.db.models import Avg, Max
from django.core.management.base import BaseCommand

from pgo.models import (
    CPM,
    Pokemon,
    MoveSet,
)
LEVELS = (20.0, 25.0, 30.0, 35.0, 40.0)
IV = 15
TIMEOUT = 99000


class Command(BaseCommand):
    help = 'Calculate and store DPS details for all currently listed pokemon.'

    def _calculate_weave_damage(self, attack, quick_move, cinematic_move, stab):
        weave_damage = {}

        for level in LEVELS:
            self.step = 0
            energy = 0
            damage = 0

            while self.step < TIMEOUT:
                base_attack = self._get_base_attack(attack, level)

                if not self._timeout(cinematic_move.duration):
                    if energy >= cinematic_move.energy_delta * - 1:

                        damage += self._calculate_dph(
                            cinematic_move.power, base_attack, self._get_stab(stab[1]))
                        self.step += (cinematic_move.duration + 1000)
                        energy += cinematic_move.energy_delta

                if self._timeout(quick_move.duration):
                    break

                damage += self._calculate_dph(
                    quick_move.power, base_attack, self._get_stab(stab[0]))
                self.step += quick_move.duration
                energy += quick_move.energy_delta

            weave_damage[level] = damage
        return weave_damage

    def _timeout(self, duration):
        return self.step + duration > TIMEOUT

    def _get_base_attack(self, attack, level):
        return float((attack + IV) * CPM.objects.get(level=level).value)

    def _calculate_dph(self, power, attack, stab):
        return floor(0.5 * power * (attack / self.defender_defense) * stab) + 1

    def _get_stab(self, stab):
        return 1.25 if stab else 1.0

    def _is_stab(self, pokemon, move_type):
        return True if move_type in (
            pokemon.primary_type, pokemon.secondary_type) else False

    def _get_moveset(self, pokemon, quick_move, cinematic_move):
        return MoveSet.objects.filter(
            pokemon_id=pokemon.pk,
            key='{} - {}'.format(quick_move, cinematic_move)
        ).first()

    def handle(self, *args, **options):
        avg_def = Pokemon.objects.filter(
            legendary=False).aggregate(avg=Avg('pgo_defense'))
        max_cpm = CPM.objects.aggregate(max=Max('value'))
        self.defender_defense = (avg_def['avg'] + IV) * float(max_cpm['max'])

        for pokemon in Pokemon.objects.all():
            for quick_move in pokemon.quick_moves.all():
                stab = [False, False]
                stab[0] = self._is_stab(pokemon, quick_move.move_type)

                for cinematic_move in pokemon.cinematic_moves.all():
                    stab[1] = self._is_stab(pokemon, cinematic_move.move_type)

                    moveset = self._get_moveset(
                        pokemon, quick_move, cinematic_move)

                    if moveset:
                        moveset.weave_damage = sorted(
                            self._calculate_weave_damage(
                                pokemon.pgo_attack,
                                quick_move,
                                cinematic_move,
                                stab
                            ).items())
                        moveset.save()
