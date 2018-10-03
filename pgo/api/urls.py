from __future__ import unicode_literals

from django.conf.urls import url

from pgo.api.routers import pgo_router
from pgo.api.views import BreakpointCalcAPIView, GoodToGoAPIView


pgo_api_urls = pgo_router.urls
pgo_api_urls.extend((
    url(r'^breakpoint-calc/$', BreakpointCalcAPIView.as_view(), name='breakpoint-calc'),
    url(r'^good-to-go/$', GoodToGoAPIView.as_view(), name='good-to-go'),
))
