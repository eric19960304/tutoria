# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-11 17:07
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_remove_reviewtempurl_student'),
    ]

    operations = [
        migrations.AddField(
            model_name='reviewtempurl',
            name='student',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='core.Student'),
            preserve_default=False,
        ),
    ]
