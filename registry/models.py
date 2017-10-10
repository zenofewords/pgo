# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.validators import (
    MinValueValidator, MaxValueValidator, RegexValidator,
)
from django.db import models

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
    nickname = models.CharField(max_length=15, blank=False, null=True,
        validators=[RegexValidator(r'^[0-9a-zA-Z]{4,}$', TRAINER_NAME_VALIDATION_ERROR)])
    level = models.PositiveIntegerField(blank=True, null=True,
        validators=[MinValueValidator(10), MaxValueValidator(40)])
    team = models.ForeignKey('registry.team')
    legit = models.BooleanField(default=True)
    recruited = models.BooleanField(default=False)
    retired = models.BooleanField(default=False)
    town = models.ForeignKey('registry.town', blank=True, null=True)

    def __unicode__(self):
        return '{0}'.format(self.nickname)

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.update_trainer_count()
        return super(Trainer, self).save(*args, **kwargs)

    def update_trainer_count(self):
        self.team.trainer_count += 1
        self.team.save()

        if self.town:
            self.town.trainer_count += 1
            self.town.save()

        if self.town and self.town.country:
            self.town.country.trainer_count += 1
            self.town.country.save()
