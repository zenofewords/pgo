from __future__ import unicode_literals

from django.contrib.postgres.fields import JSONField
from django.db import models

from zenofewords.mixins import (
    DefaultModelMixin,
    NameMixin,
    OrderMixin,
)

DEFAULT_ORDER = {
    'Pokemon': ('number',),
    'Move': ('-category', 'name',),
    'Moveset': ('pokemon__name', '-weave_damage',),
}


class Pokemon(DefaultModelMixin, NameMixin):
    number = models.CharField(max_length=5)
    primary_type = models.ForeignKey('pgo.Type',
        related_name='primary_types', blank=True, null=True)
    secondary_type = models.ForeignKey('pgo.Type',
        related_name='secondary_types', blank=True, null=True)
    quick_moves = models.ManyToManyField('pgo.Move', blank=True,
        related_name='quick_moves_pokemon')
    cinematic_moves = models.ManyToManyField('pgo.Move', blank=True,
        related_name='cinematic_moves_pokemon')

    pgo_attack = models.IntegerField(verbose_name='PGo Attack',
        blank=True, null=True)
    pgo_defense = models.IntegerField(verbose_name='PGo Defense',
        blank=True, null=True)
    pgo_stamina = models.IntegerField(verbose_name='PGo Stamina',
        blank=True, null=True)
    maximum_cp = models.DecimalField(verbose_name='Combat Power',
        max_digits=7, decimal_places=2, blank=True, null=True)
    legendary = models.BooleanField(default=False)

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
        ordering = DEFAULT_ORDER['Pokemon']


class Type(DefaultModelMixin, NameMixin, OrderMixin):
    strong = JSONField(blank=True, null=True)
    feeble = JSONField(blank=True, null=True)
    resistant = JSONField(blank=True, null=True)
    weak = JSONField(blank=True, null=True)

    class Meta:
        ordering = ('slug',)

    def __str__(self):
        return self.name


class TypeEffectivness(models.Model):
    type_offense = models.ForeignKey('pgo.Type', related_name='type_offense')
    type_defense = models.ForeignKey('pgo.Type', related_name='type_defense')
    relation = models.CharField(max_length=30, blank=True)
    effectivness = models.ForeignKey('pgo.TypeEffectivnessScalar')

    def __str__(self):
        return '{0}: {1}'.format(self.relation, self.effectivness)


class TypeEffectivnessScalar(NameMixin):
    scalar = models.DecimalField(max_digits=4, decimal_places=3)

    def __str__(self):
        return '{0} ({1})'.format(self.name, self.scalar)


class Move(DefaultModelMixin, NameMixin):
    QK = 'QK'
    CC = 'CC'
    MOVE_CATEGORY = (
        (QK, 'Quick'),
        (CC, 'Cinematic'),
    )
    category = models.CharField(max_length=2, choices=MOVE_CATEGORY)
    move_type = models.ForeignKey('pgo.Type', blank=True, null=True)

    power = models.IntegerField(blank=True, default=0)
    energy_delta = models.IntegerField(blank=True, default=0)

    duration = models.IntegerField(blank=True, null=True)
    damage_window_start = models.IntegerField(blank=True, null=True)
    damage_window_end = models.IntegerField(blank=True, null=True)

    dps = models.DecimalField(verbose_name='DPS',
        max_digits=3, decimal_places=1, blank=True, null=True)
    eps = models.DecimalField(verbose_name='EPS',
        max_digits=3, decimal_places=1, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = DEFAULT_ORDER['Move']


class Moveset(DefaultModelMixin):
    pokemon = models.ForeignKey('pgo.Pokemon', blank=True, null=True)
    key = models.CharField(max_length=50, blank=True)
    legacy = models.BooleanField(default=False)
    weave_damage = JSONField(blank=True, null=True)

    def __str__(self):
        return '{} {}'.format(self.pokemon.name, self.key)

    class Meta:
        ordering = DEFAULT_ORDER['Moveset']
        unique_together = ('pokemon', 'key',)


class CPMManager(models.Manager):
    def get_queryset(self):
        return super(CPMManager, self).get_queryset().filter(raid_cpm=False)


class RaidCPMManager(models.Manager):
    def get_queryset(self):
        return super(RaidCPMManager, self).get_queryset().filter(raid_cpm=True)


class CPM(models.Model):
    level = models.DecimalField(max_digits=3, decimal_places=1)
    value = models.DecimalField(max_digits=10, decimal_places=9)
    raid_cpm = models.BooleanField(default=False)
    raid_tier = models.PositiveIntegerField(blank=True, null=True)

    objects = models.Manager()
    gyms = CPMManager()
    raids = RaidCPMManager()

    def __str__(self):
        raid = '(raid)' if self.raid_cpm else ''
        return 'l{0}: \t{1} {2}'.format(self.level, self.value, raid)

    class Meta:
        verbose_name = 'CP multiplier'
        verbose_name_plural = 'CP multiplier'
        ordering = ('-raid_cpm', 'level',)
        # add un tgtr


class RaidTier(models.Model):
    raid_cpm = models.ForeignKey('pgo.CPM', verbose_name='Raid CPM')
    tier = models.PositiveIntegerField(verbose_name='Tier Level')
    tier_stamina = models.PositiveIntegerField(verbose_name='Tier Stamina')

    def __str__(self):
        return str(self.tier)

    class Meta:
        verbose_name = 'Raid Tier'
        verbose_name_plural = 'Raid Tiers'
        ordering = ('-tier',)


class RaidBoss(models.Model):
    pokemon = models.ForeignKey('pgo.Pokemon', verbose_name='Pokemon')
    raid_tier = models.ForeignKey('pgo.RaidTier', verbose_name='Raid Tier')

    def __str__(self):
        return 'T{} raid boss {}'.format(self.raid_tier.tier, self.pokemon.name)

    class Meta:
        verbose_name = 'Raid Boss'
        verbose_name_plural = 'Raid Bosses'
        ordering = ('-raid_tier__tier', 'pokemon__name')
