# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-19 13:36
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('keys', '0003_auto_20170116_1512'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sshkey',
            name='created_at',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, editable=False),
        ),
        migrations.AlterField(
            model_name='sshkey',
            name='modified_at',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, editable=False),
        ),
    ]
