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


class BlogPageTag(TaggedItemBase):
    """
    This model allows us to create a many-to-many relationship between
    the BlogPage object and tags. There's a longer guide on using it at
    http://docs.wagtail.io/en/latest/reference/pages/model_recipes.html#tagging
    """
    content_object = ParentalKey('BlogPage', related_name='tagged_items', on_delete=models.CASCADE)


class BlogPage(Page):
    author = models.ForeignKey(
        'common.People',
        null=True,
        blank=True,
        related_name='+',
        on_delete=models.SET_NULL
    )
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
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    suburb = models.ForeignKey(
        'common.Suburb',
        null=True,
        blank=True,
        related_name='page_set',
        on_delete=models.SET_NULL
    )
    date_published = models.DateField(
        "Date article published", blank=True, null=True
    )

    content_panels = Page.content_panels + [
        FieldPanel('introduction', classname="full"),
        ImageChooserPanel('image'),
        StreamFieldPanel('body'),
        FieldPanel('date_published'),
        SnippetChooserPanel('author'),
        MultiFieldPanel([
            FieldPanel('tags'),
            SnippetChooserPanel('suburb'),
        ], heading="Suburbs and tags"),
    ]

    search_fields = Page.search_fields + [
        index.SearchField('introduction'),
        index.SearchField('body'),
        index.RelatedFields('tags', [
            index.SearchField('name', partial_match=True, boost=10),
        ]),
        index.RelatedFields('suburb', [
            index.SearchField('name'),
        ]),
    ]

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

    # Specifies parent to BlogPage as being BlogIndexPages
    parent_page_types = ['BlogIndexPage']

    # Specifies what content types can exist as children of BlogPage.
    # Empty list means that no child content types are allowed.
    subpage_types = []


class BlogIndexPage(RoutablePageMixin, Page):
    """
    Index page for blogs.
    We need to alter the page model's context to return the child page objects,
    the BlogPage objects, so that it works as an index page

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
    search_fields = Page.search_fields + [
        index.SearchField('introduction'),
    ]
    # Speficies that only BlogPage objects can live under this index page
    subpage_types = ['BlogPage']
    parent_page_types = ['home.HomePage']
    # # Defines a method to access the children of the page (e.g. BlogPage
    # # objects). On the demo site we use this on the HomePage
    # def children(self):
    #     return self.get_children().specific().live()

    # Overrides the context to list all child items, that are live, by the
    # date that they were published
    # http://docs.wagtail.io/en/latest/getting_started/tutorial.html#overriding-context
    def get_context(self, request):
        context = super(BlogIndexPage, self).get_context(request)
        context['posts'] = self.paginate(request, self.get_posts())
        return context

    def paginate(self, request, posts, *args):
        page = request.GET.get('page')
        paginator = Paginator(posts, 6)
        try:
            pages = paginator.page(page)
        except PageNotAnInteger:
            pages = paginator.page(1)
        except EmptyPage:
            pages = paginator.page(paginator.num_pages)
        return pages

    # This defines a Custom view that utilizes Tags. This view will return all
    # related BlogPages for a given Tag or redirect back to the BlogIndexPage.
    # More information on RoutablePages is at
    # http://docs.wagtail.io/en/latest/reference/contrib/routablepage.html
    @route(r'^tags/$', name='tag_archive')
    @route(r'^tags/([\w-]+)/$', name='tag_archive')
    def tag_archive(self, request, tag=None):

        try:
            tag = Tag.objects.get(slug=tag)
        except Tag.DoesNotExist:
            return redirect(self.url)

        posts = self.get_posts(tag=tag)
        context = {
            'page': self,
            'tag': tag,
            'posts': self.paginate(request, posts)
        }
        return render(request, 'news/blog_index_page.html', context)

    # This defines a Custom view that utilizes Tags. This view will return all
    # related BlogPages for a given Tag or redirect back to the BlogIndexPage.
    # More information on RoutablePages is at
    # http://docs.wagtail.io/en/latest/reference/contrib/routablepage.html
    @route(r'^suburbs/$', name='suburb_archive')
    @route(r'^suburbs/([\w-]+)/$', name='suburb_archive')
    def suburb_archive(self, request, tag=None):

        try:
            suburb = Suburb.objects.get(slug=tag)
        except suburb.DoesNotExist:
            if suburb:
                msg = 'There are no blog posts with the "{}" suburb'.format(suburb)
                messages.add_message(request, messages.INFO, msg)
            return redirect(self.url)

        posts = self.get_posts(suburb=suburb)
        context = {
            'page': self,
            'suburb': suburb,
            'posts': self.paginate(request, posts)
        }
        return render(request, 'news/blog_index_page.html', context)

    def serve_preview(self, request, mode_name):
        # Needed for previews to work
        return self.serve(request)

    # Returns the child BlogPage objects for this BlogPageIndex.
    # If a tag is used then it will filter the posts by tag.
    # Same with suburb if no tag present
    def get_posts(self, tag=None, suburb=None):
        posts = BlogPage.objects.live().descendant_of(self).order_by('-date_published')
        if tag:
            posts = posts.filter(tags=tag)
        elif suburb:
            posts = posts.filter(suburb=suburb)
        return posts

    # Returns the list of Tags for all child posts of this BlogPage.
    def get_child_tags(self):
        tags = []
        for post in self.get_posts():
            # Not tags.append() because we don't want a list of lists
            tags += post.get_tags
        tags = sorted(set(tags))
        return tags

    def get_child_suburbs(self):
        return Suburb.objects.exclude(page_set__isnull=True)
