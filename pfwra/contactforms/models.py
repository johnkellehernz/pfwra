from django.db import models

from modelcluster.fields import ParentalKey
from wagtail.admin.edit_handlers import (
    FieldPanel, FieldRowPanel,
    InlinePanel, MultiFieldPanel, StreamFieldPanel,
)
from wagtail.core.models import Page
from wagtail.core.fields import StreamField
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.search import index

from common.blocks import BaseStreamBlock


class FormField(AbstractFormField):
    page = ParentalKey('FormPage', on_delete=models.CASCADE, related_name='custom_form_fields')


class FormPage(AbstractEmailForm):
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
        BaseStreamBlock(required=False), verbose_name="Page body", blank=True
    )
    thank_you_text = StreamField(
        BaseStreamBlock(required=False), blank=True
    ) 

    content_panels = AbstractEmailForm.content_panels + [
        FieldPanel('subtitle', classname="full"),
        FieldPanel('introduction', classname="full"),
        InlinePanel('custom_form_fields', label="Form fields"),
        StreamFieldPanel('body'),
        StreamFieldPanel('thank_you_text'),
        ImageChooserPanel('image'),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('from_address', classname="col6"),
                FieldPanel('to_address', classname="col6"),
            ]),
            FieldPanel('subject'),
        ], "Email"),
    ]
    search_fields = Page.search_fields + [
        index.SearchField('introduction'),
        index.SearchField('body'),
    ]
    subpage_types = []
    parent_page_types = ['home.HomePage']

    def get_form_fields(self):
        return self.custom_form_fields.all()