# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-23 13:26
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0029_auto_20170519_1336'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sparkjobrun',
            old_name='run_date',
            new_name='started_at',
        ),
    ]
