from django.core.management.base import BaseCommand

from pgo.models import Pokemon, RaidBoss, RaidTier


class Command(BaseCommand):
    help = 'Add all legendary and mythical pokemon to tier 5 Good to Go bosses.'

    def handle(self, *args, **options):
        tier_5 = RaidTier.objects.get(tier=5)

        for pokemon in Pokemon.objects.filter(legendary=True):
            RaidBoss.objects.get_or_create(
                pokemon__slug=pokemon.slug,
                raid_tier__tier=5,
                defaults={
                    'pokemon': pokemon,
                    'raid_tier': tier_5,
                }
            )
