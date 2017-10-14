# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic import ListView

from registry.models import (
    Team, Trainer,
)


class TrainerListView(ListView):
    model = Trainer


class TeamListView(ListView):
    model = Team
