# Generated by Django 3.0.11 on 2021-03-30 07:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='grouppage',
            name='external_url',
            field=models.URLField(blank=True, help_text='URL of the group, if any', null=True),
        ),
    ]