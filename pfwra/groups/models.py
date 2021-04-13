from __future__ import unicode_literals

from datetime import datetime

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
from events.models import EventPage


class GroupPageSuburb(Orderable, models.Model):
    page = ParentalKey('groups.GroupPage', on_delete=models.CASCADE, related_name='suburb_set')
    suburb = models.ForeignKey('common.Suburb', on_delete=models.CASCADE, related_name='group_set')

    class Meta(Orderable.Meta):
        verbose_name = "suburb"
        verbose_name_plural = "suburbs"

    panels = [
        SnippetChooserPanel('suburb'),
    ]

    def __str__(self):
        return self.page.title + " -> " + self.suburb.name


class GroupPageTag(TaggedItemBase):
    """
    This model allows us to create a many-to-many relationship between
    the GroupPage object and tags. There's a longer guide on using it at
    http://docs.wagtail.io/en/latest/reference/pages/model_recipes.html#tagging
    """
    content_object = ParentalKey('GroupPage', related_name='tagged_items', on_delete=models.CASCADE)


class GroupPage(Page):
    subtitle = models.CharField("Title in Te reo Māori", max_length=254, blank=True, null=True)
    introduction = models.TextField(
        help_text='Text to describe the group',
        blank=True)
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    logo = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    external_url = models.URLField(blank=True, null=True, help_text="URL of the group, if any")
    body = StreamField(
        BaseStreamBlock(), verbose_name="Page body", blank=True
    )
    tags = ClusterTaggableManager(through=GroupPageTag, blank=True)
    content_panels = Page.content_panels + [
        FieldPanel('subtitle', classname="full"),
        FieldPanel('introduction', classname="full"),
        ImageChooserPanel('image'),
        ImageChooserPanel('logo'),
        FieldPanel('external_url', classname="full"),
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
    parent_page_types = ['GroupIndexPage']

    # Specifies what content types can exist as children of BlogPage.
    # Empty list means that no child content types are allowed.
    subpage_types = ['events.EventPage']

    @property
    def get_tags(self):
        tags = self.tags.all()
        for tag in tags:
            tag.url = '/' + '/'.join(s.strip('/') for s in [
                self.get_parent().url,
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
                self.get_parent().url,
                'suburbs',
                suburb.slug
            ])
            suburbs.append(suburb)
        return suburbs

    @property
    def get_events(self):
        return (EventPage.objects.live().descendant_of(self).
                filter(date_scheduled__gte=datetime.today()).order_by('-date_scheduled'))




class GroupIndexPage(RoutablePageMixin, Page):
    """
    Index page for groups.
    We need to alter the page model's context to return the child page objects,
    the GroupPage objects, so that it works as an index page

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

    # Speficies that only GroupPage objects can live under this index page
    subpage_types = ['GroupPage']
    parent_page_types = ['home.HomePage']
    # # Defines a method to access the children of the page (e.g. GroupPage
    # # objects). On the demo site we use this on the HomePage
    # def children(self):
    #     return self.get_children().specific().live()

    # Overrides the context to list all child items, that are live, by the
    # date that they were published
    # http://docs.wagtail.io/en/latest/getting_started/tutorial.html#overriding-context
    def get_context(self, request):
        context = super(GroupIndexPage, self).get_context(request)
        context['groups'] = self.paginate(request, self.get_groups())
        return context

    def paginate(self, request, groups, *args):
        page = request.GET.get('page')
        paginator = Paginator(groups, 6)
        try:
            pages = paginator.page(page)
        except PageNotAnInteger:
            pages = paginator.page(1)
        except EmptyPage:
            pages = paginator.page(paginator.num_pages)
        return pages

    # This defines a Custom view that utilizes Tags. This view will return all
    # related GroupPages for a given Tag or redirect back to the GroupIndexPage.
    # More information on RoutablePages is at
    # http://docs.wagtail.io/en/latest/reference/contrib/routablepage.html
    @route(r'^tags/$', name='tag_archive')
    @route(r'^tags/([\w-]+)/$', name='tag_archive')
    def tag_archive(self, request, tag=None):

        try:
            tag = Tag.objects.get(slug=tag)
        except Tag.DoesNotExist:
            if tag:
                msg = 'There are no groups tagged with "{}"'.format(tag)
                messages.add_message(request, messages.INFO, msg)
            return redirect(self.url)

        groups = self.get_groups(tag=tag)
        context = {
            'page': self,
            'tag': tag,
            'groups': self.paginate(request, groups)
        }
        return render(request, 'groups/group_index_page.html', context)

    # This defines a Custom view that utilizes Tags. This view will return all
    # related GroupPages for a given Tag or redirect back to the GroupIndexPage.
    # More information on RoutablePages is at
    # http://docs.wagtail.io/en/latest/reference/contrib/routablepage.html
    @route(r'^suburbs/$', name='suburb_archive')
    @route(r'^suburbs/([\w-]+)/$', name='suburb_archive')
    def suburb_archive(self, request, slug=None):

        try:
            suburb = Suburb.objects.get(slug=slug)
        except Suburb.DoesNotExist:
            return redirect(self.url)

        groups = self.get_groups(suburb=suburb)
        context = {
            'page': self,
            'suburb': suburb,
            'groups': self.paginate(request, groups)
        }
        return render(request, 'groups/group_index_page.html', context)

    def serve_preview(self, request, mode_name):
        # Needed for previews to work
        return self.serve(request)

    # Returns the child GroupPage objects for this GroupPageIndex.
    # If a tag is used then it will filter the groups by tag.
    # Same with suburb if no tag present
    def get_groups(self, tag=None, suburb=None):
        groups = GroupPage.objects.live().descendant_of(self).order_by('-title')
        if tag:
            groups = groups.filter(tags=tag)
        elif suburb:
            groups = groups.filter(suburb_set__suburb=suburb)
        return groups

    # Returns the list of Tags for all child groups of this GroupPage.
    def get_child_tags(self):
        tags = []
        for group in self.get_groups():
            # Not tags.append() because we don't want a list of lists
            tags += group.get_tags
        tags = sorted(set(tags))
        return tags

    def get_child_suburbs(self):
        return Suburb.objects.exclude(group_set__isnull=True)