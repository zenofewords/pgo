from __future__ import unicode_literals

from django.conf.urls import url

from pgo.api.routers import pgo_router
from pgo.api.views import (
    AttackProficiencyAPIView,
    AttackProficiencyStatsAPIView,
    AttackProficiencyDetailAPIView,
)


pgo_api_urls = pgo_router.urls
pgo_api_urls.extend((
    url(r'^attack-proficiency/$',
        AttackProficiencyAPIView.as_view(), name='attack-proficiency'),
    url(r'^attack-proficiency-stats/$',
        AttackProficiencyStatsAPIView.as_view(), name='attack-proficiency-stats'),
    url(r'^attack-proficiency-detail/$',
        AttackProficiencyDetailAPIView.as_view(), name='attack-proficiency-detail'),
))
