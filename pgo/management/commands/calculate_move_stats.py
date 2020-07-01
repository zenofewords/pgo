from django.core.management.base import BaseCommand

from pgo.models import Move
from pgo.utils import calculate_move_stats


class Command(BaseCommand):
    help = 'Calculate and store DPS/EPS for all currently listed moves.'

    def handle(self, *args, **options):
        for move in Move.objects.all():
            calculate_move_stats(move)
