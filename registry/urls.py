# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

from registry.views import (
    TrainerListView, TeamListView,
)


urlpatterns = (
    url(r'^$', TrainerListView.as_view(), name='trainers'),
    url(r'^teams/$', TeamListView.as_view(), name='teams'),
)
