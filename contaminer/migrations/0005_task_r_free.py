# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-10-25 07:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contaminer', '0004_auto_20171018_1346'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='r_free',
            field=models.FloatField(default=None, null=True),
        ),
    ]
