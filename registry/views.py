# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic import ListView

from registry.models import (
    Team, Town, Trainer,
)


class TrainerListView(ListView):
    model = Trainer
    paginate_by = 200

    def get(self, request, *args, **kwargs):
        self.trainer_nickname = request.GET.get('trainer_nickname')
        self.sort_key = request.GET.get('sort_key', 'nickname')

        return super(TrainerListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        qs = super(TrainerListView, self).get_queryset()

        if self.trainer_nickname:
            qs = qs.filter(nickname=self.trainer_nickname)

        if self.sort_key.replace('-', '') in ['team', 'nickname', 'level']:
            return qs.prefetch_related('towns').order_by(self.sort_key)
        return qs.prefetch_related('towns')

    def get_context_data(self, **kwargs):
        context = super(TrainerListView, self).get_context_data(**kwargs)

        data = {
            'total_trainer_count': Trainer.objects.count(),
            'teams': Team.objects.all(),
            'trainer_nicknames': Trainer.objects.values_list('nickname', flat=True),
            'trainer_nickname': self.trainer_nickname,
            'sort_key': self.sort_key,
        }
        context.update(data)
        return context


class TeamListView(ListView):
    model = Team


class TownListView(ListView):
    model = Town
