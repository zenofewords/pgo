# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic import ListView

from registry.models import Trainer


class TrainerListView(ListView):
    model = Trainer
