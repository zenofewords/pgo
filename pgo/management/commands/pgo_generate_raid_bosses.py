from __future__ import unicode_literals

from django.core.management.base import BaseCommand

from pgo.models import (
    Pokemon,
    RaidBoss,
    RaidTier,
)


class Command(BaseCommand):
    help = '''
        Iterate through pokemon and create RaidBoss objects.

        Creates a raid boss object for each pokemon and for every raid tier.
    '''

    def _generate_raid_bosses(self, pokemon, raid_tiers):
        for raid_tier in raid_tiers:
            RaidBoss.objects.get_or_create(
                pokemon_id=pokemon.id,
                raid_tier_id=raid_tier.id
            )

    def handle(self, *args, **options):
        raid_tiers = RaidTier.objects.all()

        for pokemon in Pokemon.objects.all():
            self._generate_raid_bosses(pokemon, raid_tiers)
