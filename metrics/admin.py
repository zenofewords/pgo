from __future__ import unicode_literals

from django.contrib import admin

from metrics.models import Stat


admin.site.register(Stat)
