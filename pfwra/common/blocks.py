from wagtail.core.blocks import (
  CharBlock, ChoiceBlock, PageChooserBlock, RichTextBlock, StructValue, StructBlock, StreamBlock, TextBlock, URLBlock)
from wagtail.images.blocks import ImageChooserBlock
from wagtail.embeds.blocks import EmbedBlock


class LinkStructValue(StructValue):
    def url(self):
        external_url = self.get('external_url')
        page = self.get('page')
        if external_url:
            return external_url
        elif page:
            return page.url


class QuickLinkBlock(StructBlock):
    text = CharBlock(
        label="Link label",
        required=False,
    )
    page = PageChooserBlock(
        label="Page",
        required=False,
        help_text='Choose a page to link to'
    )
    external_url = URLBlock(
        label="External URL",
        required=False,
        help_text='Or choose an external URL to link to'
    )

    class Meta:
        icon = 'site'
        value_class = LinkStructValue


class CardBlock(StructBlock):
    image = ImageChooserBlock(required=False)
    header = CharBlock(label="Header text")
    text = TextBlock(
        required=False,
        help_text='Write an introduction for the card',
    )
    link = QuickLinkBlock(required=False, help_text='Link URL and link text (button)')

    class Meta:
        template = 'common/blocks/card.html'
        icon = 'form'


class QuoteBlock(StructBlock):
    title = CharBlock(label="Quote title", required=False)
    text = TextBlock(label="Body of quote")
    author = CharBlock(label="Quote title", required=False)
    link = QuickLinkBlock(required=False)

    class Meta:
        template = 'common/blocks/quote.html'
        icon = 'openquote'


class ImageBlock(StructBlock):
    """
    Custom `StructBlock` for utilizing images with associated caption and
    attribution data
    """
    image = ImageChooserBlock(required=True)
    caption = CharBlock(required=False)
    attribution = CharBlock(required=False)

    class Meta:
        icon = 'image'
        template = "common/blocks/image.html"


class HeadingBlock(StructBlock):
    """
    Custom `StructBlock` that allows the user to select h2 - h4 sizes for headers
    """
    heading_text = CharBlock(classname="title", required=True)
    size = ChoiceBlock(choices=[
        ('', 'Select a header size'),
        ('h2', 'H2'),
        ('h3', 'H3'),
        ('h4', 'H4')
    ], blank=True, required=False)

    class Meta:
        icon = "title"
        template = "common/blocks/heading.html"


class BlockQuote(StructBlock):
    """
    Custom `StructBlock` that allows the user to attribute a quote to the author
    """
    text = TextBlock()
    attribute_name = CharBlock(
        blank=True, required=False, label='e.g. Mary Berry')

    class Meta:
        icon = "fa-quote-left"
        template = "common/blocks/blockquote.html"


class BaseStreamBlock(StreamBlock):
    """
    Define the custom blocks that `StreamField` will utilize
    """
    heading_block = HeadingBlock()
    paragraph_block = RichTextBlock(
        icon="fa-paragraph",
        template="common/blocks/paragraph.html"
    )
    image_block = ImageBlock()
    block_quote = BlockQuote()
    embed_block = EmbedBlock(
        help_text='Insert an embed URL e.g https://www.youtube.com/embed/SGJFWirQ3ks',
        icon="fa-s15",
        template="common/blocks/embed.html")
