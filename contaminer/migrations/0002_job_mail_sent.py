# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-08-17 13:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contaminer', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='mail_sent',
            field=models.BooleanField(default=False),
        ),
    ]
