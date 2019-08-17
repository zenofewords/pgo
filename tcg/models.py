from django.db import models

from zenofewords.mixins import DefaultModelMixin


class Deck(DefaultModelMixin):
    pass


class Card(DefaultModelMixin):
    CARD_TYPES = (
        ('POK', 'Pokemon'),
        ('TRA', 'Trainer'),
        ('ENE', 'Energy'),
    )
    deck = models.ForeignKey('tcg.deck', on_delete=models.deletion.CASCADE)
    card_type = models.CharField(max_length=3, choices=CARD_TYPES)
