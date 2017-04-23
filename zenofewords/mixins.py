from __future__ import unicode_literals

from django.conf import settings
from django.db import models


class DefaultModelMixin(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, default=1)
    created = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class SlugMixin(models.Model):
    slug = models.SlugField(max_length=200, blank=True)

    class Meta:
        abstract = True


class NameMixin(SlugMixin):
    name = models.CharField(max_length=50, blank=False, null=True)

    class Meta:
        abstract = True


class OrderMixin(models.Model):
    order = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        abstract = True
