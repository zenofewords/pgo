# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

from registry.views import TrainerListView


urlpatterns = (
    url(r'^trainers/$', TrainerListView.as_view(), name='trainers'),
)
