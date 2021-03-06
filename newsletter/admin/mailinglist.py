"""ModelAdmin for MailingList"""
from datetime import datetime
import StringIO

from django.contrib import admin
from django.conf.urls.defaults import url
from django.conf.urls.defaults import patterns
from django.utils.encoding import smart_str
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect

from dry_newsletter.newsletter.utils.importation import import_mailing_lists
from dry_newsletter.newsletter.models import Contact
from dry_newsletter.newsletter.models import MailingList
from dry_newsletter.newsletter.utils.excel import ExcelResponse


class MailingListAdmin(admin.ModelAdmin):
    date_hierarchy = 'creation_date'
    list_display = ('id', 'name', 'creation_date', 'subscribers_count', 'unsubscribers_count',)
    list_display_links =('name',)
    list_filter = ('creation_date', 'modification_date')
    search_fields = ('name', 'description',)
    filter_horizontal = ['subscribers', 'unsubscribers']
    fieldsets = ((None, {'fields': ('name', 'description',)}),
                 (None, {'fields': ('subscribers',)}),
                 (None, {'fields': ('unsubscribers',)}),
                 )
    actions = ['merge_mailinglist']
    actions_on_top = False
    actions_on_bottom = True

    def merge_mailinglist(self, request, queryset):
        """Merge multiple mailing list"""
        if queryset.count() == 1:
            self.message_user(request, _('Please select a least 2 mailing list.'))
            return None

        subscribers = {}
        unsubscribers = {}
        for ml in queryset:
            for contact in ml.subscribers.all():
                subscribers[contact] = ''
            for contact in ml.unsubscribers.all():
                unsubscribers[contact] = ''

        when = str(datetime.now()).split('.')[0]
        new_mailing = MailingList(name=_('Merging list at %s') % when, description=_('Mailing list created by merging at %s') % when)
        new_mailing.save()
        new_mailing.subscribers = subscribers.keys()
        new_mailing.unsubscribers = unsubscribers.keys()

        self.message_user(request, _('%s succesfully created by merging.') % new_mailing)
        return HttpResponseRedirect(reverse('admin:newsletter_mailinglist_change', args=[new_mailing.pk]))
    merge_mailinglist.short_description = _('Merge selected mailinglists')

    def exportion_excel(self, request, mailinglist_id):
        """Export subscribers in the mailing in Excel"""
        mailinglist = get_object_or_404(MailingList, pk=mailinglist_id)
        name = 'contacts_%s' % smart_str(mailinglist.name)
        return ExcelResponse(mailinglist.subscribers.all(), name)

    def importation(self, request):
        """Import contacts from csv"""
        opts = self.model._meta

        if request.POST:
            source = request.FILES.get('source') or \
                     StringIO.StringIO(request.POST.get('source', ''))
            inserted = import_mailing_lists(source)
            self.message_user(request, _('%s mailing lists succesfully imported.') % inserted)

        context = {'title': _('Mailing list importation'),
                   'opts': opts,
                   'app_label': opts.app_label}

        return render_to_response('newsletter/mailing_list_import.html', context, RequestContext(request))

    def get_urls(self):
        urls = super(MailingListAdmin, self).get_urls()
        my_urls = patterns('',
                           url(r'^export/excel/(?P<mailinglist_id>\d+)/$',
                               self.admin_site.admin_view(self.exportion_excel),
                               name='newsletter_mailinglist_export_excel'),
                           url(r'^import/$',
                               self.admin_site.admin_view(self.importation),
                               name='newsletter_mailinglist_import'))
        return my_urls + urls
