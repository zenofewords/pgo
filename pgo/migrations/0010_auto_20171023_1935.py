# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-10-23 19:35
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pgo', '0009_cpm_total_powerup_cost'),
    ]

    operations = [
        migrations.AddField(
            model_name='type',
            name='immune',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='type',
            name='puny',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]
