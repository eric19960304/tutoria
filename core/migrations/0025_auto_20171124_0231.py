# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-23 18:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_tutor_ishideprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='isTutoriaOwned',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='profile',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Profile'),
        ),
    ]
