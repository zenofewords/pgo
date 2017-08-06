from django.db.models import F

from metrics.models import Stat


def update_stats(app):
    stats = Stat.objects.get(app=app)
    stats.hits = F('hits') + 1
    stats.save()
