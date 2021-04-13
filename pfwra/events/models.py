from __future__ import unicode_literals

from django.contrib import messages
from django.db import models
from django.shortcuts import redirect, render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey

from taggit.models import Tag, TaggedItemBase

from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel, StreamFieldPanel, MultiFieldPanel
from wagtail.core.fields import StreamField
from wagtail.core.models import Page, Orderable
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.search import index
from wagtail.snippets.edit_handlers import SnippetChooserPanel

from common.blocks import BaseStreamBlock
from common.models import Suburb


class EventPageSuburb(Orderable, models.Model):
    page = ParentalKey('events.EventPage', on_delete=models.CASCADE, related_name='suburb_set')
    suburb = models.ForeignKey('common.Suburb', on_delete=models.CASCADE, related_name='event_set')

    class Meta(Orderable.Meta):
        verbose_name = "suburb"
        verbose_name_plural = "suburbs"

    panels = [
        SnippetChooserPanel('suburb'),
    ]

    def __str__(self):
        return self.page.title + " -> " + self.suburb.name



class EventPageTag(TaggedItemBase):
    """
    This model allows us to create a many-to-many relationship between
    the eventPage object and tags. There's a longer guide on using it at
    http://docs.wagtail.io/en/latest/reference/pages/model_recipes.html#tagging
    """
    content_object = ParentalKey('EventPage', related_name='tagged_items', on_delete=models.CASCADE)


class EventPage(Page):
    subtitle = models.CharField("Title in Te reo Māori", max_length=254, blank=True, null=True)
    introduction = models.TextField(
        help_text='Text to describe the event',
        blank=True)
    location = models.TextField(
        help_text='Text to describe the event',
        blank=True)
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    date_scheduled = models.DateField(
        "Date event is escheduled for", blank=True, null=True
    )
    starting_time = models.CharField(null=True, blank=True, max_length=254, help_text="starting time. Something like 10am")
    ending_time = models.CharField(null=True, blank=True, max_length=254, help_text="Ending time. Something like 12pm")
    body = StreamField(
        BaseStreamBlock(), verbose_name="Page body", blank=True
    )
    tags = ClusterTaggableManager(through=EventPageTag, blank=True)
    content_panels = Page.content_panels + [
        FieldPanel('subtitle', classname="full"),
        FieldPanel('introduction', classname="full"),
        MultiFieldPanel([
            FieldPanel('location'),
            FieldPanel('date_scheduled'),
            FieldPanel('starting_time'),
            FieldPanel('ending_time'),
            ], heading="Event location and time"),
        ImageChooserPanel('image'),
        StreamFieldPanel('body'),
        MultiFieldPanel([
            FieldPanel('tags'),
            InlinePanel('suburb_set', label="Suburbs")
        ], heading="Suburbs and tags"),
    ]

    search_fields = Page.search_fields + [
        index.SearchField('introduction'),
        index.SearchField('body'),
    ]

    # Specifies parent to BlogPage as being BlogIndexPages
    parent_page_types = ['groups.GroupPage']

    # Specifies what content types can exist as children of BlogPage.
    # Empty list means that no child content types are allowed.
    subpage_types = []

    @property
    def get_tags(self):
        tags = self.tags.all()
        for tag in tags:
            tag.url = '/' + '/'.join(s.strip('/') for s in [
                EventIndexPage.objects.live().first().url,
                'tags',
                tag.slug
            ])
        return tags

    @property
    def get_suburbs(self):
        suburbs = []
        for gps in self.suburb_set.all():
            suburb = gps.suburb
            suburb.url = '/' + '/'.join(s.strip('/') for s in [
                EventIndexPage.objects.live().first().url,
                'suburbs',
                suburb.slug
            ])
            suburbs.append(suburb)
        return suburbs


class EventIndexPage(RoutablePageMixin, Page):
    """
    Index page for events.
    We need to alter the page model's context to return the child page objects,
    the eventPage objects, so that it works as an index page

    RoutablePageMixin is used to allow for a custom sub-URL for the tag views
    defined above.
    """
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

    content_panels = Page.content_panels + [
        FieldPanel('subtitle', classname="full"),
        FieldPanel('introduction', classname="full"),
        ImageChooserPanel('image'),

    ]

    # Speficies that only eventPage objects can live under this index page
    subpage_types = []
    parent_page_types = ['home.HomePage']
    # # Defines a method to access the children of the page (e.g. eventPage
    # # objects). On the demo site we use this on the HomePage
    # def children(self):
    #     return self.get_children().specific().live()

    # Overrides the context to list all child items, that are live, by the
    # date that they were published
    # http://docs.wagtail.io/en/latest/getting_started/tutorial.html#overriding-context
    def get_context(self, request):
        context = super(EventIndexPage, self).get_context(request)
        context['events'] = self.paginate(request, self.get_events())
        return context

    def paginate(self, request, events, *args):
        page = request.GET.get('page')
        paginator = Paginator(events, 6)
        try:
            pages = paginator.page(page)
        except PageNotAnInteger:
            pages = paginator.page(1)
        except EmptyPage:
            pages = paginator.page(paginator.num_pages)
        return pages

    # This defines a Custom view that utilizes Tags. This view will return all
    # related eventPages for a given Tag or redirect back to the eventIndexPage.
    # More information on RoutablePages is at
    # http://docs.wagtail.io/en/latest/reference/contrib/routablepage.html
    @route(r'^tags/$', name='tag_archive')
    @route(r'^tags/([\w-]+)/$', name='tag_archive')
    def tag_archive(self, request, tag=None):

        try:
            tag = Tag.objects.get(slug=tag)
        except Tag.DoesNotExist:
            if tag:
                msg = 'There are no events tagged with "{}"'.format(tag)
                messages.add_message(request, messages.INFO, msg)
            return redirect(self.url)

        events = self.get_events(tag=tag)
        context = {
            'page': self,
            'tag': tag,
            'events': self.paginate(request, events)
        }
        return render(request, 'events/event_index_page.html', context)

    # This defines a Custom view that utilizes Tags. This view will return all
    # related eventPages for a given Tag or redirect back to the eventIndexPage.
    # More information on RoutablePages is at
    # http://docs.wagtail.io/en/latest/reference/contrib/routablepage.html
    @route(r'^suburbs/$', name='suburb_archive')
    @route(r'^suburbs/([\w-]+)/$', name='suburb_archive')
    def suburb_archive(self, request, slug=None):

        try:
            suburb = Suburb.objects.get(slug=slug)
        except Suburb.DoesNotExist:
            return redirect(self.url)

        events = self.get_events(suburb=suburb)
        context = {
            'page': self,
            'suburb': suburb,
            'events': self.paginate(request, events)
        }
        return render(request, 'events/event_index_page.html', context)

    def serve_preview(self, request, mode_name):
        # Needed for previews to work
        return self.serve(request)

    # Returns the child eventPage objects for this eventPageIndex.
    # If a tag is used then it will filter the events by tag.
    # Same with suburb if no tag present
    def get_events(self, tag=None, suburb=None):
        events = EventPage.objects.live().order_by('-date_scheduled')
        if tag:
            events = events.filter(tags=tag)
        elif suburb:
            events = events.filter(suburb_set__suburb=suburb)
        return events

    # Returns the list of Tags for all child events of this eventPage.
    def get_child_tags(self):
        tags = []
        for event in self.get_events():
            # Not tags.append() because we don't want a list of lists
            tags += event.get_tags
        tags = sorted(set(tags))
        return tags

    def get_child_suburbs(self):
        return Suburb.objects.exclude(event_set__isnull=True)