# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-11 20:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_session_iscouponused'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tutor',
            name='hourly_rate',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
