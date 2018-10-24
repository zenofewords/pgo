from __future__ import unicode_literals

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
    navigation = models.ForeignKey('zenofewords.Navigation')

    class Meta:
        ordering = ('order', 'slug', )

    def __str__(self):
        return self.name if self.name else self.slug


class SiteNotification(DefaultModelMixin, NameMixin):
    active = models.BooleanField()
    message = models.CharField(max_length=1024)
