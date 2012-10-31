"""ModelAdmin for Newsletter"""
from HTMLParser import HTMLParseError

from django import forms
from django.db.models import Q
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from dry_newsletter.newsletter.models import Contact
from dry_newsletter.newsletter.models import Newsletter
from dry_newsletter.newsletter.models import MailingList
from dry_newsletter.newsletter.mailer import Mailer

try:
    CAN_USE_PREMAILER = True
    from dry_newsletter.newsletter.utils.premailer import Premailer
    from dry_newsletter.newsletter.utils.premailer import PremailerError
except ImportError:
    CAN_USE_PREMAILER = False

class BaseNewsletterAdmin(admin.ModelAdmin):
    date_hierarchy = 'creation_date'
    list_display = ('title', 'server', 'status', 'sending_date', 'creation_date', 'modification_date',)
    list_filter = ('status', 'sending_date', 'creation_date', 'modification_date')
    search_fields = ('title', 'content', 'header_sender', 'header_reply')
    filter_horizontal = ['test_contacts']
    fieldsets = ((None, {'fields': ('title', 'content',)}),
                 (_('Article 1'), {'fields': ('article_1_title', 'article_1_subtitle', 'article_1_text', 'article_1_image')}),
                 (_('Article 2'), {'fields': ('article_2_title', 'article_2_subtitle', 'article_2_text', 'article_2_image'), 'classes': ('collapse',)}),
                 (_('Article 3'), {'fields': ('article_3_title', 'article_3_subtitle', 'article_3_text', 'article_3_image'), 'classes': ('collapse',)}),
                 (_('Receivers'), {'fields': ('mailing_lists', 'test_contacts',)}),
                 (_('Sending'), {'fields': ('sending_date', 'status',)}),
                 (_('Miscellaneous'), {'fields': ('server', 'header_sender', 'header_reply', 'slug'), 'classes': ('collapse',)}),
                 )
    prepopulated_fields = {'slug': ('title',)}
    actions = ['send_mail_test', 'make_ready_to_send', 'make_cancel_sending']
    actions_on_top = False
    actions_on_bottom = True

    def get_actions(self, request):
        actions = super(BaseNewsletterAdmin, self).get_actions(request)
        if not request.user.has_perm('newsletter.can_change_status'):
            del actions['make_ready_to_send']
            del actions['make_cancel_sending']
        return actions

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == 'status' and not request.user.has_perm('newsletter.can_change_status'):
            kwargs['choices'] = ((Newsletter.DRAFT, _('Default')),)
            return db_field.formfield(**kwargs)
        return super(BaseNewsletterAdmin, self).formfield_for_choice_field(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'test_contacts':
            queryset = Contact.objects.filter(tester=True)
            if not request.user.is_superuser and USE_WORKGROUPS:
                contacts_pk = request_workgroups_contacts_pk(request)
                queryset = queryset.filter(pk__in=contacts_pk)
            kwargs['queryset'] = queryset
        return super(BaseNewsletterAdmin, self).formfield_for_manytomany(
            db_field, request, **kwargs)

    def send_mail_test(self, request, queryset):
        """Send newsletter in test"""
        for newsletter in queryset:
            if newsletter.test_contacts.count():
                mailer = Mailer(newsletter, test=True)
                try:
                    mailer.run()
                except HTMLParseError:
                    self.message_user(request, _('Unable send newsletter, due to errors within HTML.'))
                    continue
                self.message_user(request, _('%s succesfully sent.') % newsletter)
            else:
                self.message_user(request, _('No test contacts assigned for %s.') % newsletter)
    send_mail_test.short_description = _('Send test email')

    def make_ready_to_send(self, request, queryset):
        """Make newsletter ready to send"""
        queryset = queryset.filter(status=Newsletter.DRAFT)
        for newsletter in queryset:
            newsletter.status = Newsletter.WAITING
            newsletter.save()
        self.message_user(request, _('%s newletters are ready to send') % queryset.count())
    make_ready_to_send.short_description = _('Make ready to send')

    def make_cancel_sending(self, request, queryset):
        """Cancel the sending of newsletters"""
        queryset = queryset.filter(Q(status=Newsletter.WAITING) |
                                   Q(status=Newsletter.SENDING))
        for newsletter in queryset:
            newsletter.status = Newsletter.CANCELED
            newsletter.save()
        self.message_user(request, _('%s newletters are cancelled') % queryset.count())
    make_cancel_sending.short_description = _('Cancel the sending')

class NewsletterAdmin(BaseNewsletterAdmin):
    pass
