"""Default urls for the dry_newsletter.newsletter"""
from django.conf.urls.defaults import url
from django.conf.urls.defaults import include
from django.conf.urls.defaults import patterns

urlpatterns = patterns('',
                       url(r'^mailing/', include('dry_newsletter.newsletter.urls.mailing_list')),
                       url(r'^tracking/', include('dry_newsletter.newsletter.urls.tracking')),
                       url(r'^statistics/', include('dry_newsletter.newsletter.urls.statistics')),
                       url(r'^', include('dry_newsletter.newsletter.urls.newsletter')),
                       )
