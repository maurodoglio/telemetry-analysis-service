# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-23 13:30
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0032_sparkjobrun_ready_at'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sparkjobrun',
            old_name='scheduled_date',
            new_name='scheduled_at',
        ),
    ]
