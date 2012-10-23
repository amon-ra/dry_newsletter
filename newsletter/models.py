"""Models for dry_newsletter.newsletter"""
from smtplib import SMTP
from smtplib import SMTPHeloError
from datetime import datetime
from datetime import timedelta

from django.db import models
from django.utils.encoding import smart_str
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group
from django.utils.encoding import force_unicode

from tagging.fields import TagField
from dry_newsletter.newsletter.managers import ContactManager
from dry_newsletter.newsletter.settings import BASE_PATH
from dry_newsletter.newsletter.settings import MAILER_HARD_LIMIT
from dry_newsletter.newsletter.settings import DEFAULT_HEADER_REPLY
from dry_newsletter.newsletter.settings import DEFAULT_HEADER_SENDER
from dry_newsletter.newsletter.utils.vcard import vcard_contact_export


class SMTPServer(models.Model):
    """Configuration of a SMTP server"""
    name = models.CharField(_('name'), max_length=255)
    host = models.CharField(_('server host'), max_length=255)
    user = models.CharField(_('server user'), max_length=128, blank=True, help_text=_('Leave it empty if the host is public.'))
    password = models.CharField(_('server password'), max_length=128, blank=True, help_text=_('Leave it empty if the host is public.'))
    port = models.IntegerField(_('server port'), default=25)
    tls = models.BooleanField(_('server use TLS'))

    headers = models.TextField(_('custom headers'), blank=True, help_text=_('key1: value1 key2: value2, splitted by return line.\n Useful for passing some tracking headers if your provider allows it.'))
    mails_hour = models.IntegerField(_('mails per hour'), default=0)

    def connect(self):
        """Connect the SMTP Server"""
        smtp = SMTP(smart_str(self.host), int(self.port))
        smtp.ehlo_or_helo_if_needed()
        if self.tls:
            smtp.starttls()
            smtp.ehlo_or_helo_if_needed()

        if self.user or self.password:
            smtp.login(smart_str(self.user), smart_str(self.password))
        return smtp

    def delay(self):
        """compute the delay (in seconds) between mails to ensure mails
        per hour limit is not reached

        :rtype: float
        """
        if not self.mails_hour:
            return 0.0
        else:
            return 3600.0 / self.mails_hour

    def credits(self):
        """Return how many mails the server can send"""
        if not self.mails_hour:
            return MAILER_HARD_LIMIT

        last_hour = datetime.now() - timedelta(hours=1)
        sent_last_hour = ContactMailingStatus.objects.filter(
            models.Q(status=ContactMailingStatus.SENT) |
            models.Q(status=ContactMailingStatus.SENT_TEST),
            newsletter__server=self,
            creation_date__gte=last_hour).count()
        return self.mails_hour - sent_last_hour

    @property
    def custom_headers(self):
        if self.headers:
            headers = {}
            for header in self.headers.splitlines():
                if header:
                    key, value = header.split(':')
                    headers[key.strip()] = value.strip()
            return headers
        return {}

    def __unicode__(self):
        return '%s (%s)' % (self.name, self.host)

    class Meta:
        verbose_name = _('SMTP server')
        verbose_name_plural = _('SMTP servers')




class Contact(models.Model):
    """Contact for emailing"""
    email = models.EmailField(_('email'), unique=True)
    first_name = models.CharField(_('first name'), max_length=50, blank=True)
    last_name = models.CharField(_('last name'), max_length=50, blank=True)

    subscriber = models.BooleanField(_('subscriber'), default=True)
    valid = models.BooleanField(_('valid email'), default=True)
    tester = models.BooleanField(_('contact tester'), default=False)
    tags = TagField(_('tags'))

    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    creation_date = models.DateTimeField(_('creation date'), auto_now_add=True)
    modification_date = models.DateTimeField(_('modification date'), auto_now=True)

    objects = ContactManager()

    def subscriptions(self):
        """Return the user subscriptions"""
        return MailingList.objects.filter(subscribers=self)

    def unsubscriptions(self):
        """Return the user unsubscriptions"""
        return MailingList.objects.filter(unsubscribers=self)

    def vcard_format(self):
        return vcard_contact_export(self)

    def mail_format(self):
        if self.first_name and self.last_name:
            return '%s %s <%s>' % (self.last_name, self.first_name, self.email)
        return self.email
    mail_format.short_description = _('mail format')

    def get_absolute_url(self):
        if self.content_type and self.object_id:
            return self.content_object.get_absolute_url()
        return reverse('admin:newsletter_contact_change', args=(self.pk,))

    def __unicode__(self):
        if self.first_name and self.last_name:
            contact_name = '%s %s' % (self.last_name, self.first_name)
        else:
            contact_name = self.email
        if self.tags:
            return '%s | %s' % (contact_name, self.tags)
        return contact_name

    class Meta:
        ordering = ('last_name',)
        verbose_name = _('contact')
        verbose_name_plural = _('contacts')


class MailingListGroup(models.Model):
    title = models.CharField(_('title'), max_length=255)

    class Meta:
        ordering = ('title',)
        verbose_name_plural = _('category groups')

class MailingList(models.Model):
    """Mailing list"""
    name = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    mailing_list_group = models.ForeignKey(MailingListGroup, verbose_name=_('category group'), blank=True, null=True)

    subscribers = models.ManyToManyField(Contact, verbose_name=_('subscribers'), related_name='mailinglist_subscriber')
    unsubscribers = models.ManyToManyField(Contact, verbose_name=_('unsubscribers'), related_name='mailinglist_unsubscriber', null=True, blank=True)

    creation_date = models.DateTimeField(_('creation date'), auto_now_add=True)
    modification_date = models.DateTimeField(_('modification date'), auto_now=True)

    def subscribers_count(self):
        return self.subscribers.all().count()
    subscribers_count.short_description = _('subscribers')

    def unsubscribers_count(self):
        return self.unsubscribers.all().count()
    unsubscribers_count.short_description = _('unsubscribers')

    def expedition_set(self):
        unsubscribers_id = self.unsubscribers.values_list('id', flat=True)
        return self.subscribers.valid_subscribers().exclude(id__in=unsubscribers_id)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('-creation_date',)
        verbose_name = _('mailing list')
        verbose_name_plural = _('mailing lists')


class Newsletter(models.Model):
    """Newsletter to be sended to contacts"""

    use_html_to_text_converter = _('IMPORTANT! DON\'T PASTE COPYED TEXT DIRECTLY IN THIS FIELD!!! Before pasting use an html to text converter such http://beaker.mailchimp.com/html-to-text or http://www.webtoolhub.com/tn561393-html-to-text-converter.aspx')
    help_text_image = _('Upload a 300px width image. Do not insert white spaces in the image\'s name.')
    def upload_to(self, filename):
        return os.path.join("dry_newsletter", "img", self.slug, filename)

    DRAFT = 0
    WAITING = 1
    SENDING = 2
    SENT = 4
    CANCELED = 5

    STATUS_CHOICES = ((DRAFT, _('draft')),
                      (WAITING, _('waiting sending')),
                      (SENDING, _('sending')),
                      (SENT, _('sent')),
                      (CANCELED, _('canceled')),
                      )

    title = models.CharField(_('title'), max_length=255, help_text=_('You can use the "{{ UNIQUE_KEY }}" variable for unique identifier within the newsletter\'s title.'))
    content = models.TextField(_('content'), help_text=_('Or paste an URL.'), default=_('<body>\n<!-- Edit your newsletter here -->\n</body>'))

    article_1_title = models.CharField(_('Article 1 - Title'), max_length=255, blank=True)
    article_1_subtitle = models.CharField(_('Article 1 - Subtitle'), max_length=255, blank=True)
    article_1_text = models.TextField(_('Article 1 - Text'), help_text=_(use_html_to_text_converter), default=_('<body>\n<!-- Edit your newsletter here -->\n</body>'), blank=True)
    # DA RISOLVERE Alberto: se carico immagine con spazio nel nome, nella mail lo spazio viene escaped con + e quindi non scarica immagine
    article_1_image = models.ImageField(_('Article 1 - Image'), upload_to=upload_to, help_text=help_text_image, blank=True)

    article_2_title = models.CharField(_('Article 2 - Title'), max_length=255, blank=True)
    article_2_subtitle = models.CharField(_('Article 2 - Subtitle'), max_length=255, blank=True)
    article_2_text = models.TextField(_('Article 2 - Text'), help_text=_(use_html_to_text_converter), default=_('<body>\n<!-- Edit your newsletter here -->\n</body>'), blank=True)
    article_2_image = models.ImageField(_('Article 2 - Image'), upload_to=upload_to, help_text=help_text_image, blank=True)
       
    article_3_title = models.CharField(_('Article 3 - Title'), max_length=255, blank=True)
    article_3_subtitle = models.CharField(_('Article 3 - Subtitle'), max_length=255, blank=True)
    article_3_text = models.TextField(_('Article 3 - Text'), help_text=_(use_html_to_text_converter), default=_('<body>\n<!-- Edit your newsletter here -->\n</body>'), blank=True)
    article_3_image = models.ImageField(_('Article 3 - Image'), upload_to=upload_to, help_text=help_text_image, blank=True)

    mailing_lists = models.ManyToManyField(Category, verbose_name=_('mailing list'), related_name=('newsletters'),)
    test_contacts = models.ManyToManyField(Contact, verbose_name=_('test contacts'), blank=True, null=True)
    server = models.ForeignKey(SMTPServer, verbose_name=_('smtp server'), default=1)
    header_sender = models.CharField(_('sender'), max_length=255, default=DEFAULT_HEADER_SENDER)
    header_reply = models.CharField(_('reply to'), max_length=255, default=DEFAULT_HEADER_REPLY)
    status = models.IntegerField(_('status'), choices=STATUS_CHOICES, default=DRAFT)
    sending_date = models.DateTimeField(_('sending date'), default=datetime.now)
    slug = models.SlugField(help_text=_('Used for displaying the newsletter on the site.'), unique=True)
    creation_date = models.DateTimeField(_('creation date'), auto_now_add=True)
    modification_date = models.DateTimeField(_('modification date'), auto_now=True)

    def mails_sent(self):
        return self.contactmailingstatus_set.filter(status=ContactMailingStatus.SENT).count()

    @models.permalink
    def get_absolute_url(self):
        return ('newsletter_newsletter_preview', (self.slug,))

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ('-creation_date',)
        verbose_name = _('newsletter')
        verbose_name_plural = _('newsletters')
        permissions = (('can_change_status', 'Can change status'),)


class ContactMailingStatus(models.Model):
    """Status of the reception"""
    SENT_TEST = -1
    SENT = 0
    ERROR = 1
    INVALID = 2
    OPENED = 4
    OPENED_ON_SITE = 5
    LINK_OPENED = 6
    UNSUBSCRIPTION = 7

    STATUS_CHOICES = ((SENT_TEST, _('sent in test')),
                      (SENT, _('sent')),
                      (ERROR, _('error')),
                      (INVALID, _('invalid email')),
                      (OPENED, _('opened')),
                      (OPENED_ON_SITE, _('opened on site')),
                      (LINK_OPENED, _('link opened')),
                      (UNSUBSCRIPTION, _('unsubscription')),
                      )

    newsletter = models.ForeignKey(Newsletter, verbose_name=_('newsletter'))
    contact = models.ForeignKey(Contact, verbose_name=_('contact'))
    status = models.IntegerField(_('status'), choices=STATUS_CHOICES)

    creation_date = models.DateTimeField(_('creation date'), auto_now_add=True)

    def __unicode__(self):
        return '%s : %s : %s' % (self.newsletter.__unicode__(),
                                 self.contact.__unicode__(),
                                 self.get_status_display())

    class Meta:
        ordering = ('-creation_date',)
        verbose_name = _('contact mailing status')
        verbose_name_plural = _('contact mailing statuses')