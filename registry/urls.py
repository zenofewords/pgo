# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

from registry.views import (
    TeamListView, TownListView, TrainerListView,
)


urlpatterns = (
    url(r'^$', TrainerListView.as_view(), name='trainers'),
    url(r'^teams/$', TeamListView.as_view(), name='teams'),
    url(r'^towns/$', TownListView.as_view(), name='towns'),
)
