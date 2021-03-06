"""Urls for the dry_newsletter.newsletter Newsletter"""
from django.conf.urls.defaults import url
from django.conf.urls.defaults import patterns

urlpatterns = patterns('dry_newsletter.newsletter.views.newsletter',
    url(r'^preview/(?P<slug>[-\w]+)/$', 'view_newsletter_preview', name='newsletter_newsletter_preview'),
    url(r'^online_version/(?P<slug>[-\w]+)/$', 'view_newsletter_online_version', name='newsletter_newsletter_online_version'),
    url(r'^(?P<slug>[-\w]+)/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'view_newsletter_contact', name='newsletter_newsletter_contact'),
)
