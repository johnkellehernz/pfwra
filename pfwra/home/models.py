from django.db import models

from wagtail.admin.edit_handlers import (
    FieldPanel,
    InlinePanel,
    MultiFieldPanel,
    PageChooserPanel,
    StreamFieldPanel,
)
from wagtail.core.fields import StreamField
from wagtail.core.models import Page, Orderable
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.snippets.edit_handlers import SnippetChooserPanel

from modelcluster.fields import ParentalKey

from common.blocks import CardBlock, QuoteBlock, BaseStreamBlock


class CounterPageAdvertPlacement(Orderable, models.Model):
    page = ParentalKey('home.HomePage', on_delete=models.CASCADE, related_name='counter_placements')
    counter = models.ForeignKey('common.Counter', on_delete=models.CASCADE, related_name='+')

    class Meta(Orderable.Meta):
        verbose_name = "counter placement"
        verbose_name_plural = "counter placements"

    panels = [
        SnippetChooserPanel('counter'),
    ]

    def __str__(self):
        return self.page.title + " -> " + self.counter.text


class HomePage(Page):
    # Hero section of HomePage
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text='Homepage image'
    )
    hero_text = models.CharField(
        null=True,
        blank=True,
        max_length=255,
        help_text='Write an introduction for the homepage'
    )
    hero_cta = models.CharField(
        null=True,
        blank=True,
        verbose_name='Hero CTA',
        max_length=255,
        help_text='Text to display on Call to Action'
    )
    hero_cta_link = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name='Hero CTA link',
        help_text='Choose a page to link to for the Call to Action'
    )

    featured = StreamField([('cards', CardBlock())], help_text='Featured cards', blank=True)
    quotations = StreamField([('quotes', QuoteBlock())], help_text='Featured quotes', blank=True)
    body = StreamField(BaseStreamBlock(), verbose_name="Page body", blank=True)
    content_panels = Page.content_panels + [
        MultiFieldPanel([
            ImageChooserPanel('image'),
            FieldPanel('hero_text', classname="full"),
            MultiFieldPanel([
                FieldPanel('hero_cta'),
                PageChooserPanel('hero_cta_link'),
            ]),
        ], heading="Hero section"),
        StreamFieldPanel('featured'),
        StreamFieldPanel('quotations'),
        InlinePanel('counter_placements', label="Counters"),
    ]

    subpage_types = ['groups.GroupIndexPage', 'news.BlogIndexPage', 'common.StandardPage']

    def __str__(self):
        return self.title
