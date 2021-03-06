# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-11-14 20:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0008_auto_20170806_2059'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='directions',
            field=models.TextField(blank=True, help_text='directions', verbose_name='direction_text'),
        ),
        migrations.AlterField(
            model_name='direction',
            name='recipe',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='old_directions', to='recipe.Recipe', verbose_name='recipe'),
        ),
    ]
