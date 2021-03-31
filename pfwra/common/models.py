from django.db import models
from django.template.defaultfilters import slugify

from wagtail.core.models import Collection, Page
from wagtail.core.fields import StreamField
from wagtail.snippets.models import register_snippet
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.search import index
from wagtail.admin.edit_handlers import (
    FieldPanel,
    FieldRowPanel,
    MultiFieldPanel,
    PageChooserPanel,
    StreamFieldPanel,
)

from modelcluster.models import ClusterableModel
from modelcluster.fields import ParentalKey

from .blocks import BaseStreamBlock


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


@register_snippet
class Suburb(models.Model):
    name = models.CharField("Suburb name", unique=True, max_length=254)
    slug = models.SlugField(unique=True, blank=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'suburb'
        verbose_name_plural = 'suburbs'

    panels = [
        FieldPanel('name'),
        FieldPanel('slug'),
    ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super(Suburb, self).save(*args, **kwargs)


@register_snippet
class People(models.Model):
    first_name = models.CharField("First name", max_length=254)
    last_name = models.CharField("Last name", max_length=254, null=True, blank=True)
    job_title = models.CharField("Job title", max_length=254, null=True, blank=True)

    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    panels = [
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('first_name', classname="col6"),
                FieldPanel('last_name', classname="col6"),
            ])
        ], "Name"),
        FieldPanel('job_title'),
        ImageChooserPanel('image')
    ]

    search_fields = [
        index.SearchField('first_name'),
        index.SearchField('last_name'),
    ]

    def __str__(self):
        return '{} {}'.format(self.first_name, self.last_name)

    class Meta:
        verbose_name = 'Person'
        verbose_name_plural = 'People'


class StandardPage(Page):
    subtitle = models.CharField("Title in Te reo Māori", max_length=254, blank=True, null=True)
    introduction = models.TextField(
        help_text='Text to describe the page',
        blank=True)
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    body = StreamField(
        BaseStreamBlock(), verbose_name="Page body", blank=True
    )
    content_panels = Page.content_panels + [
        FieldPanel('subtitle', classname="full"),
        FieldPanel('introduction', classname="full"),
        StreamFieldPanel('body'),
        ImageChooserPanel('image'),
    ]