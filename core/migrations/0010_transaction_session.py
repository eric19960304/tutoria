# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-10 18:27
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_review'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='session',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Session'),
        ),
    ]