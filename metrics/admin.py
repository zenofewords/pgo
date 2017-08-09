from __future__ import unicode_literals

from django.contrib import admin

from metrics.models import Stat


class StatAdmin(admin.ModelAdmin):
    readonly_fields = ('created',)


admin.site.register(Stat, StatAdmin)
