from __future__ import unicode_literals

from django.core.management.base import BaseCommand

from pgo.models import (
    Move,
)


class Command(BaseCommand):
    help = 'Calculate and store DPS/EPS for all currently listed moves.'

    def _calculate_move_dps(self, move):
        move.DPS = move.power / (move.duration / 1000.0)

    def _calculate_move_eps(self, move):
        move.EPS = move.energy_delta / (move.duration / 1000.0)

    def handle(self, *args, **options):
        for move in Move.objects.all():
            self._calculate_move_dps(move)
            self._calculate_move_eps(move)
            move.save()
