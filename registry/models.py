# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.postgres.fields import CICharField
from django.core.validators import (
    MinValueValidator, MaxValueValidator, RegexValidator,
)
from django.db import models
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from zenofewords.mixins import DefaultModelMixin, NameMixin

TRAINER_NAME_VALIDATION_ERROR = 'Nicknames are 4-15 characters long and consist only of letters and numbers.'


class TeamColor:
    YELLOW = 'yellow'
    BLUE = 'blue'
    RED = 'red'
    GREEN = 'green'

    CHOICES = [
        (YELLOW, 'Yellow'),
        (BLUE, 'Blue'),
        (RED, 'Red'),
        (GREEN, 'Green'),
    ]


class StatMixin(DefaultModelMixin, NameMixin):
    trainer_count = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True


class Country(StatMixin):
    class Meta:
        verbose_name = 'Country'
        verbose_name_plural = 'Countries'

    def __unicode__(self):
        return '{0}'.format(self.name)


class Town(StatMixin):
    country = models.ForeignKey('registry.country')

    def __unicode__(self):
        return '{0}'.format(self.name)


class Team(StatMixin):
    color = models.CharField(
        max_length=10, choices=TeamColor.CHOICES, default=TeamColor.YELLOW)

    def __unicode__(self):
        return '{0}'.format(self.name)


class Trainer(DefaultModelMixin):
    nickname = CICharField(max_length=15, blank=False, null=False, unique=True,
        validators=[RegexValidator(r'^[0-9a-zA-Z]{4,}$', TRAINER_NAME_VALIDATION_ERROR)])
    level = models.PositiveIntegerField(blank=True, null=True,
        validators=[MinValueValidator(20), MaxValueValidator(40)],
        help_text='Level 20 is the minimum level required to be included in the registry.')
    team = models.ForeignKey('registry.team',
        help_text='Select \"Harmony\" if the trainer has never chosen a team.')
    legit = models.BooleanField(default=True,
        help_text='Will never be shown publicly, untick only for confirmed spoofers/botters.')
    recruited = models.BooleanField(default=False,
        help_text='The trainer is included in our groups/chats.')
    retired = models.BooleanField(default=False,
        help_text='The trainer used to play, but they no longer do, or at least not currently.')
    towns = models.ManyToManyField('registry.town', related_name='trainers', blank=False,
        help_text='Where the trainer usually plays.')

    def __unicode__(self):
        return '{0}'.format(self.nickname)

    class Meta:
        ordering = ('nickname',)


@receiver(post_save, sender=Trainer, dispatch_uid='update_team_trainer_count')
def update_team_trainer_count(sender, instance, created, **kwargs):
    if created:
        instance.team.trainer_count += 1
        instance.team.save()
    else:
        for team in Team.objects.all():
            team.trainer_count = Trainer.objects.filter(team__slug=team.slug).count()
            team.save()


@receiver(m2m_changed, sender=Trainer.towns.through, dispatch_uid='update_town_trainer_count')
def update_town_trainer_count(sender, instance, **kwargs):
    for town in Town.objects.all():
        town.trainer_count = Trainer.objects.filter(towns__slug=town.slug).distinct().count()
        town.save()

        town.country.trainer_count = \
            Trainer.objects.filter(towns__country__slug=town.country.slug).distinct().count()
        town.country.save()
