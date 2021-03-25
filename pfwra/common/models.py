from django.db import models

from wagtail.admin.edit_handlers import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.images.edit_handlers import ImageChooserPanel


@register_snippet
class Counter(models.Model):
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    count = models.IntegerField(null=True, blank=True)
    text = models.CharField(
        null=True,
        blank=True,
        max_length=255,
        help_text='Text to display on the counter'
    )

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('count'),
        FieldPanel('text'),
    ]

    def __str__(self):
        return '%d %s' % (self.count, self.text) 