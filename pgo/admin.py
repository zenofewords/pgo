from __future__ import unicode_literals

from django.contrib import admin

from pgo.models import (
    CPM,
    Move,
    Pokemon,
    Type,
    TypeAdvantage,
    TypeEffectivness,
)


admin.site.register(CPM)
admin.site.register(Move)
admin.site.register(Pokemon)
admin.site.register(Type)
admin.site.register(TypeAdvantage)
admin.site.register(TypeEffectivness)
