# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-05-04 12:25
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('slacktoframe', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Greeting',
        ),
    ]
