from __future__ import unicode_literals

from django.conf.urls import url

from pgo.api.routers import pgo_router
from pgo.api.views import AttackProficiencyAPIView


pgo_api_urls = pgo_router.urls
pgo_api_urls.append(
    url(r'^attack-proficiency/$',
        AttackProficiencyAPIView.as_view(), name='attack-proficiency')
)
