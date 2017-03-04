from __future__ import unicode_literals

from django.db import models

from zenofewords.mixins import (
    DefaultModelMixin,
    NameMixin,
    OrderMixin,
)


class Pokemon(DefaultModelMixin, NameMixin):
    number = models.CharField(max_length=5)
    primary_type = models.ForeignKey('pgo.Type',
        related_name='primary_types', blank=True, null=True)
    secondary_type = models.ForeignKey('pgo.Type',
        related_name='secondary_types', blank=True, null=True)
    pgo_attack = models.IntegerField(verbose_name='ATK', blank=True, null=True)
    pgo_defense = models.IntegerField(verbose_name='DEF', blank=True, null=True)
    pgo_stamina = models.IntegerField(verbose_name='STA', blank=True, null=True)

    attack = models.IntegerField(blank=True, null=True)
    special_attack = models.IntegerField(blank=True, null=True)
    defense = models.IntegerField(blank=True, null=True)
    special_defense = models.IntegerField(blank=True, null=True)
    stamina = models.IntegerField(blank=True, null=True)
    speed = models.IntegerField(blank=True, null=True)

    def __unicode__(self):
        return '{0} ({1})'.format(self.name, self.number)

    class Meta:
        verbose_name = 'Pokemon'
        verbose_name_plural = 'Pokemon'
        ordering = ('number',)


class Type(DefaultModelMixin, NameMixin, OrderMixin):

    class Meta:
        ordering = ('slug',)

    def __str__(self):
        return self.name


class TypeAdvantage(models.Model):
    first_type = models.ForeignKey('pgo.Type', related_name='first')
    second_type = models.ForeignKey('pgo.Type', related_name='second')
    relation = models.CharField(max_length=30, blank=True)
    effectivness = models.ForeignKey('pgo.TypeEffectivness')

    def __str__(self):
        return '{0}: {1}'.format(self.relation, self.effectivness)


class TypeEffectivness(NameMixin):
    scalar = models.DecimalField(max_digits=4, decimal_places=2)

    def __str__(self):
        return '{0} ({1})'.format(self.name, self.scalar)


class Move(DefaultModelMixin, NameMixin):
    QK = 'QK'
    CC = 'CC'
    MOVE_CATEGORY = (
        (QK, 'Quick'),
        (CC, 'Cinematic'),
    )
    move_category = models.CharField(max_length=2, choices=MOVE_CATEGORY)
    move_type = models.ForeignKey('pgo.Type', blank=True, null=True)

    power = models.IntegerField(blank=True, default=0)
    energy_delta = models.IntegerField(blank=True, default=0)

    duration = models.IntegerField(blank=True, null=True)
    damage_window_start = models.IntegerField(blank=True, null=True)
    damage_window_end = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name


class CPM(models.Model):
    level = models.DecimalField(max_digits=3, decimal_places=1)
    value = models.DecimalField(max_digits=10, decimal_places=9)

    def __str__(self):
        return 'l{0}: \t{1}'.format(self.level, self.value)

    class Meta:
        verbose_name = 'CP multiplier'
        verbose_name_plural = 'CP multiplier'
        ordering = ('level',)
