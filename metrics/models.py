# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from zenofewords.mixins import DefaultModelMixin


class Stat(DefaultModelMixin):
    """
    Tracks visitor stats for apps.

    app - stores the application's name
    hits - the count of request made to the app
    """
    app = models.CharField(max_length=200)
    hits = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'Stat'
        verbose_name_plural = 'Stats'
