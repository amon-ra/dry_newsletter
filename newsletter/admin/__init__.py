"""Admin for dry_newsletter.newsletter"""
from django.contrib import admin
from django.conf import settings

from dry_newsletter.newsletter.models import Contact
from dry_newsletter.newsletter.models import SMTPServer
from dry_newsletter.newsletter.models import Newsletter
from dry_newsletter.newsletter.models import MailingList
from dry_newsletter.newsletter.models import ContactMailingStatus

from dry_newsletter.newsletter.admin.contact import ContactAdmin
from dry_newsletter.newsletter.admin.newsletter import NewsletterAdmin
from dry_newsletter.newsletter.admin.smtpserver import SMTPServerAdmin
from dry_newsletter.newsletter.admin.mailinglist import MailingListAdmin

class CommonMedia:
    js = (
        'https://ajax.googleapis.com/ajax/libs/dojo/1.6.0/dojo/dojo.xd.js',
        '/media/dojo/editor.js',
    )
    css = {
        'all': ('/media/dojo/editor.css',),
    }


admin.site.register(Contact, ContactAdmin)
admin.site.register(SMTPServer, SMTPServerAdmin)
admin.site.register(Newsletter, NewsletterAdmin, Media=CommonMedia)
admin.site.register(MailingList, MailingListAdmin)


if settings.DEBUG:
    admin.site.register(ContactMailingStatus)
