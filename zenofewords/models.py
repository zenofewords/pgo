from django.db import models

from zenofewords.mixins import (
    DefaultModelMixin,
    NameMixin,
    OrderMixin,
)


class Navigation(DefaultModelMixin, NameMixin):

    def __str__(self):
        return self.slug


class NavigationItem(DefaultModelMixin, NameMixin, OrderMixin):
    navigation = models.ForeignKey('zenofewords.Navigation', on_delete=models.deletion.CASCADE)

    class Meta:
        ordering = ('order', 'slug', )

    def __str__(self):
        return self.name if self.name else self.slug


class SiteNotificationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(active=True)


class SiteNotification(DefaultModelMixin, NameMixin):
    active = models.BooleanField()
    message = models.CharField(max_length=1024)

    objects = models.Manager()
    active_notifications = SiteNotificationManager()
