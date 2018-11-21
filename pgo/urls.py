from __future__ import unicode_literals

from django.conf.urls import url

from pgo.views import (
    BreakpointCalculatorView, BreakpointCalcRedirectView, GoodToGoView,
)

app_name = 'pgo'
urlpatterns = (
    url(r'^pgo', BreakpointCalcRedirectView.as_view(), name='breakpoint-calc-redirect'),
    url(r'^breakpoint-calc/$', BreakpointCalculatorView.as_view(), name='breakpoint-calc'),
    url(r'^good-to-go/$', GoodToGoView.as_view(), name='good-to-go'),
    url(r'^$', BreakpointCalculatorView.as_view(), name='breakpoint-calc'),
)
