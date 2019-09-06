# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-09-29 22:50
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pgo', '0002_auto_20180929_2121'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pokemon',
            name='cinematic_moves',
            field=models.ManyToManyField(blank=True, related_name='cinematic_moves_pokemon', to='pgo.PokemonMove'),
        ),
        migrations.AlterField(
            model_name='pokemon',
            name='quick_moves',
            field=models.ManyToManyField(blank=True, related_name='quick_moves_pokemon', to='pgo.PokemonMove'),
        ),
    ]
