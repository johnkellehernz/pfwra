# Generated by Django 3.0.11 on 2021-03-26 07:55

from django.db import migrations
import wagtail.core.blocks
import wagtail.core.fields
import wagtail.images.blocks


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0006_auto_20210324_2004'),
    ]

    operations = [
        migrations.AlterField(
            model_name='homepage',
            name='featured',
            field=wagtail.core.fields.StreamField([('cards', wagtail.core.blocks.StructBlock([('image', wagtail.images.blocks.ImageChooserBlock(required=False)), ('header', wagtail.core.blocks.CharBlock(label='Header text')), ('text', wagtail.core.blocks.TextBlock(help_text='Write an introduction for the card', required=False)), ('link', wagtail.core.blocks.StructBlock([('text', wagtail.core.blocks.CharBlock(label='Link label', required=False)), ('page', wagtail.core.blocks.PageChooserBlock(help_text='Choose a page to link to', label='Page', required=False)), ('external_url', wagtail.core.blocks.URLBlock(help_text='Or choose an external URL to link to', label='External URL', required=False))], help_text='Link URL and link text (button)', required=False))]))], blank=True, help_text='Featured cards'),
        ),
        migrations.AlterField(
            model_name='homepage',
            name='quotations',
            field=wagtail.core.fields.StreamField([('quotes', wagtail.core.blocks.StructBlock([('title', wagtail.core.blocks.CharBlock(label='Quote title', required=False)), ('text', wagtail.core.blocks.TextBlock(label='Body of quote')), ('author', wagtail.core.blocks.CharBlock(label='Quote title', required=False)), ('link', wagtail.core.blocks.StructBlock([('text', wagtail.core.blocks.CharBlock(label='Link label', required=False)), ('page', wagtail.core.blocks.PageChooserBlock(help_text='Choose a page to link to', label='Page', required=False)), ('external_url', wagtail.core.blocks.URLBlock(help_text='Or choose an external URL to link to', label='External URL', required=False))], required=False))]))], blank=True, help_text='Featured quotes'),
        ),
    ]