from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.timezone import datetime

from zenofewords.mixins import (
    DefaultModelMixin,
    NameMixin,
    OrderMixin,
)


class MoveCategory:
    QK = 'QK'
    CC = 'CC'

    CHOICES = (
        (QK, 'Quick'),
        (CC, 'Cinematic'),
    )


class RaidBossStatus:
    OFFICIAL = 'official'
    SIMULATED = 'simulated'

    CHOICES = (
        (OFFICIAL, 'Official'),
        (SIMULATED, 'Simulated'),
    )


class Generation:
    I = 'I'
    II = 'II'
    III = 'III'
    IV = 'IV'
    V = 'V'
    VI = 'VI'
    VII = 'VII'
    VIII = 'VIII'

    CHOICES = (
        (I, 'I'),
        (II, 'II'),
        (III, 'III'),
        (IV, 'IV'),
        (V, 'V'),
        (VI, 'VI'),
        (VII, 'VII'),
        (VIII, 'VIII'),
    )


class MoveAvailabiltyLegacyType:
    COMMUNIY_DAY = 'CD'
    RAID_DAY = 'RD'
    QUEST_ENCOUNTER = 'QE'
    REMOVED = 'RM'
    ACTIVE = 'AC'

    CHOICES = (
        (COMMUNIY_DAY, 'Community day'),
        (RAID_DAY, 'Raid day'),
        (QUEST_ENCOUNTER, 'Quest encounter'),
        (REMOVED, 'Removed'),
        (ACTIVE, 'Active'),
    )


class PokemonManager(models.Manager):
    def implemented(self):
        return super().get_queryset().filter(implemented=True)


class Pokemon(DefaultModelMixin, NameMixin):
    number = models.CharField(max_length=5)
    primary_type = models.ForeignKey('pgo.Type', related_name='primary_types',
        blank=True, null=True, on_delete=models.deletion.CASCADE)
    secondary_type = models.ForeignKey('pgo.Type', related_name='secondary_types',
        blank=True, null=True, on_delete=models.deletion.CASCADE)
    quick_moves = models.ManyToManyField(
        'pgo.PokemonMove', blank=True, related_name='quick_moves_pokemon')
    cinematic_moves = models.ManyToManyField(
        'pgo.PokemonMove', blank=True, related_name='cinematic_moves_pokemon')

    pgo_attack = models.IntegerField(
        verbose_name='PGo Attack', blank=True, null=True)
    pgo_defense = models.IntegerField(
        verbose_name='PGo Defense', blank=True, null=True)
    pgo_stamina = models.IntegerField(
        verbose_name='PGo Stamina', blank=True, null=True)
    maximum_cp = models.DecimalField(
        verbose_name='Combat Power', max_digits=7, decimal_places=2, blank=True, null=True)
    stat_product = models.IntegerField(blank=True, null=True)
    bulk = models.IntegerField(blank=True, null=True)

    compound_resistance = JSONField(blank=True, null=True)
    compound_weakness = JSONField(blank=True, null=True)

    legendary = models.BooleanField(default=False)
    generation = models.CharField(max_length=5, choices=Generation.CHOICES, blank=True)
    implemented = models.BooleanField(default=True)

    attack = models.IntegerField(blank=True, null=True)
    special_attack = models.IntegerField(blank=True, null=True)
    defense = models.IntegerField(blank=True, null=True)
    special_defense = models.IntegerField(blank=True, null=True)
    stamina = models.IntegerField(blank=True, null=True)
    speed = models.IntegerField(blank=True, null=True)

    objects = PokemonManager()

    class Meta:
        verbose_name = 'Pokemon'
        verbose_name_plural = 'Pokemon'
        ordering = ('number',)

    def __str__(self):
        return '{0} ({1})'.format(self.name, self.number)


class Type(DefaultModelMixin, NameMixin, OrderMixin):
    strong = JSONField(blank=True, null=True)
    feeble = JSONField(blank=True, null=True)
    puny = JSONField(blank=True, null=True)
    resistant = JSONField(blank=True, null=True)
    weak = JSONField(blank=True, null=True)
    immune = JSONField(blank=True, null=True)

    class Meta:
        ordering = ('slug',)

    def __str__(self):
        return self.name


class TypeEffectiveness(models.Model):
    type_offense = models.ForeignKey('pgo.Type', related_name='type_offense', on_delete=models.deletion.CASCADE)
    type_defense = models.ForeignKey('pgo.Type', related_name='type_defense', on_delete=models.deletion.CASCADE)
    relation = models.CharField(max_length=30, blank=True)
    effectiveness = models.ForeignKey('pgo.TypeEffectivenessScalar', on_delete=models.deletion.CASCADE)

    def __str__(self):
        return '{0}: {1}'.format(self.relation, self.effectiveness)


class TypeEffectivenessScalar(NameMixin):
    scalar = models.DecimalField(max_digits=8, decimal_places=6)

    def __str__(self):
        return '{0} ({1})'.format(self.name, self.scalar)


class Move(DefaultModelMixin, NameMixin):
    category = models.CharField(max_length=2, choices=MoveCategory.CHOICES)
    move_type = models.ForeignKey('pgo.Type', blank=True, null=True, on_delete=models.deletion.CASCADE)

    power = models.IntegerField(blank=True, default=0)
    energy_delta = models.IntegerField(blank=True, default=0)

    duration = models.IntegerField(blank=True, null=True)
    damage_window_start = models.IntegerField(blank=True, null=True)
    damage_window_end = models.IntegerField(blank=True, null=True)

    pvp_power = models.IntegerField(blank=True, default=0)
    pvp_energy_delta = models.IntegerField(blank=True, default=0)
    pvp_duration = models.IntegerField(blank=True, default=0)

    dps = models.DecimalField(
        verbose_name='Damage per second', max_digits=3, decimal_places=1, blank=True, null=True)
    eps = models.DecimalField(
        verbose_name='Energy per second', max_digits=3, decimal_places=1, blank=True, null=True)

    dpt = models.DecimalField(
        verbose_name='Damage per turn', max_digits=3, decimal_places=1, blank=True, null=True)
    ept = models.DecimalField(
        verbose_name='Energy per turn', max_digits=3, decimal_places=1, blank=True, null=True)
    dpe = models.DecimalField(
        verbose_name='Damage per energy', max_digits=5, decimal_places=3, blank=True, null=True)

    def __str__(self):
        return self.name


class PokemonMove(DefaultModelMixin):
    pokemon = models.ForeignKey('pgo.Pokemon', on_delete=models.deletion.CASCADE)
    move = models.ForeignKey('pgo.Move', on_delete=models.deletion.CASCADE)

    stab = models.BooleanField(default=False)
    score = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)

    class Meta:
        ordering = ('pokemon', '-score', '-stab',)
        unique_together = ('pokemon', 'move',)

    def __str__(self):
        return '{}\'s {}'.format(self.pokemon, self.move)


class MoveAvailability(models.Model):
    pokemon_move = models.ForeignKey('pgo.PokemonMove', on_delete=models.deletion.CASCADE)
    available_from = models.DateField(default=datetime(2016, 7, 6))
    available_to = models.DateField(blank=True, null=True)
    legacy_status = models.CharField(
        choices=MoveAvailabiltyLegacyType.CHOICES,
        default=MoveAvailabiltyLegacyType.ACTIVE,
        max_length=2)

    class Meta:
        verbose_name = 'Move availability'
        verbose_name_plural = 'Move availability'

    def __str__(self):
        return '{} - {}'.format(self.pokemon_move, self.legacy_status)

    @property
    def is_legacy(self):
        return True if self.available_to else False


class Moveset(DefaultModelMixin):
    pokemon = models.ForeignKey('pgo.Pokemon', blank=True, null=True, on_delete=models.deletion.CASCADE)
    quick_move = models.ForeignKey(
        'pgo.PokemonMove', blank=True, null=True, related_name='quick_moves', on_delete=models.deletion.CASCADE)
    cinematic_move = models.ForeignKey(
        'pgo.PokemonMove', blank=True, null=True, related_name='cinematic_moves', on_delete=models.deletion.CASCADE)
    key = models.CharField(max_length=50, blank=True)

    weave_damage = JSONField(blank=True, null=True)

    class Meta:
        unique_together = ('pokemon', 'quick_move', 'cinematic_move',)

    def __str__(self):
        return '{} {}'.format(self.pokemon.name, self.key)


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
    stardust_cost = models.PositiveIntegerField(blank=True, null=True)
    total_stardust_cost = models.PositiveIntegerField(blank=True, null=True)
    candy_cost = models.PositiveIntegerField(blank=True, null=True)
    total_candy_cost = models.PositiveIntegerField(blank=True, null=True)

    objects = models.Manager()
    gyms = CPMManager()
    raids = RaidCPMManager()

    class Meta:
        verbose_name = 'CP multiplier'
        verbose_name_plural = 'CP multiplier'
        ordering = ('-raid_cpm', 'level',)

    def __str__(self):
        raid = '(raid)' if self.raid_cpm else ''
        return 'l{0}: \t{1} {2}'.format(self.level, self.value, raid)


class RaidTier(OrderMixin):
    raid_cpm = models.ForeignKey('pgo.CPM', verbose_name='Raid CPM', on_delete=models.deletion.CASCADE)
    tier = models.PositiveIntegerField(verbose_name='Tier Level')
    tier_stamina = models.PositiveIntegerField(verbose_name='Tier Stamina')
    battle_duration = models.PositiveIntegerField(default=180)

    class Meta:
        verbose_name = 'Raid Tier'
        verbose_name_plural = 'Raid Tiers'
        ordering = ('-tier',)

    def __str__(self):
        return str(self.tier)


class RaidBoss(models.Model):
    pokemon = models.ForeignKey('pgo.Pokemon', verbose_name='Pokemon', on_delete=models.deletion.CASCADE)
    raid_tier = models.ForeignKey('pgo.RaidTier', verbose_name='Raid Tier', on_delete=models.deletion.CASCADE)
    status = models.CharField(max_length=20, choices=RaidBossStatus.CHOICES, blank=True)

    class Meta:
        verbose_name = 'Raid Boss'
        verbose_name_plural = 'Raid Bosses'
        ordering = ('-raid_tier__tier', 'pokemon__name',)

    def __str__(self):
        return 'T{} raid boss {}'.format(self.raid_tier.tier, self.pokemon.name)


class WeatherCondition(DefaultModelMixin, NameMixin, OrderMixin):
    types_boosted = models.ManyToManyField('pgo.Type', verbose_name='Boosts Type', blank=True)

    class Meta:
        verbose_name = 'Weather Condition'
        verbose_name_plural = 'Weather Conditions'

    def __str__(self):
        return self.name


class Friendship(models.Model):
    level = models.CharField(max_length=9)
    damage_boost = models.DecimalField(max_digits=3, decimal_places=2)

    class Meta:
        verbose_name = 'Friendship'
        verbose_name_plural = 'Friendship'
        ordering = ('damage_boost',)
        unique_together = ('level', 'damage_boost',)

    def __str__(self):
        return self.level
