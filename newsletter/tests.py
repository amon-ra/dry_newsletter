"""Unit tests for dry_newsletter.newsletter"""
from datetime import datetime
from datetime import timedelta
from tempfile import NamedTemporaryFile
from smtplib import SMTP

from django.test import TestCase
from django.http import Http404
from django.db import IntegrityError
from django.core.files import File
from django.utils.encoding import smart_str
from django.utils.timezone import utc
from django.contrib.admin.sites import AdminSite

from dry_newsletter.newsletter.mailer import Mailer
from dry_newsletter.newsletter.models import Contact
from dry_newsletter.newsletter.models import MailingList
from dry_newsletter.newsletter.models import SMTPServer
from dry_newsletter.newsletter.models import Newsletter
from dry_newsletter.newsletter.models import ContactMailingStatus
from dry_newsletter.newsletter.utils.tokens import tokenize
from dry_newsletter.newsletter.utils.tokens import untokenize
from dry_newsletter.newsletter.models import ContactMailingStatus

# TEST ALBERTO
class DebuggingTestCase(TestCase):
    """Tests for the Newsletter model"""

    def setUp(self):
        self.server = SMTPServer.objects.create(name='Test SMTP', host='smtp.webfaction.com', user='fineuropsoditic', password='arpe77jaci')
        self.contact_1 = Contact.objects.create(email='albertojacini@gmail.com')
        self.contact_2 = Contact.objects.create(email='albertojacini@hotmail.com')
        self.mailing_list_1 = MailingList.objects.create(name='Fornitori')
        self.mailing_list_2 = MailingList.objects.create(name='Giornalisti')
        self.mailing_list_1.subscribers.add(self.contact_1)
        self.mailing_list_2.subscribers.add(self.contact_1, self.contact_2)
        self.newsletter = Newsletter.objects.create(title='TEST NEWSLETTER TITLE', article_1_text='Test Newsletter article 1 text', slug='newsletter_1', server=self.server)
        self.newsletter.mailing_lists.add(self.mailing_list_1, self.mailing_list_2)
        self.newsletter.status = Newsletter.WAITING
        self.newsletter.save()
        self.mailer = Mailer(self.newsletter, verbose=1)
        self.site = AdminSite()


    def test_sending_mails(self):
        from django.core.management import call_command
        from dry_newsletter.newsletter.admin.newsletter import BaseNewsletterAdmin
        from django.db.models import Q
        from StringIO import StringIO
        import copy
        newsletter_admin = BaseNewsletterAdmin(Newsletter, self.site)
        request = None
        queryset = Newsletter.objects.all()
        newsletters = queryset.filter(Q(status=Newsletter.WAITING) | Q(status=Newsletter.SENDING))
        nls = copy.copy(newsletters)
        print(newsletters)
        print(nls)
        response = StringIO()
        print(response)
        call_command("send_newsletter", stdout=response)
        print('NESWLETTERS:')
        print(newsletters)
        print('COPIES:')
        print(nls)
        print('RESPONSE:')
        response.seek(0)
        print(response.read())
        for newsletter in newsletters:
            print('NEWSLETTER:')
            print(newsletter.title)
        
        
        #content = StringIO()
        #call_command("dumpdata", stdout=content)
        #content.seek(0)
        #print content.read()
        # newsletter_admin.send_newsletter(request, queryset)

        #self.assertEqual(len(self.mailer.expedition_list), 3)
        #self.assertIn(self.contact_1, self.mailer.expedition_list)
        #self.assertIn(self.contact_2, self.mailer.expedition_list, 'Anche il secondo contatto e nella lista')
        #print('{}, {}'.format(self.contact_1.email, self.contact_2.email))


#class ImportNewsletterTestCase(TestCase):
    
#    def setUp(self):
#        self.source("1; Mailing list numero 1")

# TEST EMENCIA


class FakeSMTP(object):
    mails_sent = 0

    def sendmail(self, *ka, **kw):
        self.mails_sent += 1
        return {}

    def quit(*ka, **kw):
        pass


class SMTPServerTestCase(TestCase):
    """Tests for the SMTPServer model"""

    def setUp(self):
        self.server = SMTPServer.objects.create(name='Test SMTP',
                                                host='smtp.domain.com')
        self.server_2 = SMTPServer.objects.create(name='Test SMTP 2',
                                                  host='smtp.domain2.com')
        self.contact = Contact.objects.create(email='test@domain.com')
        self.mailinglist = MailingList.objects.create(name='Test MailingList')
        self.mailinglist.subscribers.add(self.contact)

        self.newsletter = Newsletter.objects.create(title='Test Newsletter',
                                                    article_1_text='Test Newsletter21 text',
                                                    server=self.server, slug='test-nl')
        self.newsletter.mailing_lists.add(self.mailinglist)

        self.newsletter_2 = Newsletter.objects.create(title='Test Newsletter 2',
                                                      article_1_text='Test Newsletter2 text',
                                                      server=self.server, slug='test-nl-2')
        self.newsletter_2.mailing_lists.add(self.mailinglist)

        self.newsletter_3 = Newsletter.objects.create(title='Test Newsletter 3',
                                                      article_1_text='Test Newsletter2 text',
                                                      server=self.server_2, slug='test-nl-3')
        self.newsletter_2.mailing_lists.add(self.mailinglist)

    def test_credits(self):
        # Testing unlimited account
        self.assertEquals(self.server.credits(), 10000)
        # Testing default limit
        self.server.mails_hour = 42
        self.assertEquals(self.server.credits(), 42)

        # Testing credits status, with multiple server case
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contact,
                                            status=ContactMailingStatus.SENT)
        self.assertEquals(self.server.credits(), 41)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contact,
                                            status=ContactMailingStatus.SENT_TEST)
        self.assertEquals(self.server.credits(), 40)
        # Testing with a fake status
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contact,
                                            status=ContactMailingStatus.ERROR)
        self.assertEquals(self.server.credits(), 40)
        # Testing with a second newsletter sharing the server
        ContactMailingStatus.objects.create(newsletter=self.newsletter_2,
                                            contact=self.contact,
                                            status=ContactMailingStatus.SENT)
        self.assertEquals(self.server.credits(), 39)
        # Testing with a third newsletter with another server
        ContactMailingStatus.objects.create(newsletter=self.newsletter_3,
                                            contact=self.contact,
                                            status=ContactMailingStatus.SENT)
        self.assertEquals(self.server.credits(), 39)

    def test_custom_headers(self):
        self.assertEquals(self.server.custom_headers, {})
        self.server.headers = 'key_1: val_1\r\nkey_2   :   val_2'
        self.assertEquals(len(self.server.custom_headers), 2)


class ContactTestCase(TestCase):
    """Tests for the Contact model"""

    def setUp(self):
        self.mailinglist_1 = MailingList.objects.create(name='Test MailingList')
        self.mailinglist_2 = MailingList.objects.create(name='Test MailingList 2')

    def test_unique(self):
        Contact(email='test@domain.com').save()
        self.assertRaises(IntegrityError, Contact(email='test@domain.com').save)

    def test_mail_format(self):
        contact = Contact(email='test@domain.com')
        self.assertEquals(contact.mail_format(), 'test@domain.com')
        contact = Contact(email='test@domain.com', first_name='Toto')
        self.assertEquals(contact.mail_format(), 'test@domain.com')
        contact = Contact(email='test@domain.com', first_name='Toto', last_name='Titi')
        self.assertEquals(contact.mail_format(), 'Titi Toto <test@domain.com>')

    def test_subscriptions(self):
        contact = Contact.objects.create(email='test@domain.com')
        self.assertEquals(len(contact.subscriptions()), 0)

        self.mailinglist_1.subscribers.add(contact)
        self.assertEquals(len(contact.subscriptions()), 1)
        self.mailinglist_2.subscribers.add(contact)
        self.assertEquals(len(contact.subscriptions()), 2)

    def test_unsubscriptions(self):
        contact = Contact.objects.create(email='test@domain.com')
        self.assertEquals(len(contact.unsubscriptions()), 0)

        self.mailinglist_1.unsubscribers.add(contact)
        self.assertEquals(len(contact.unsubscriptions()), 1)
        self.mailinglist_2.unsubscribers.add(contact)
        self.assertEquals(len(contact.unsubscriptions()), 2)


class MailingListTestCase(TestCase):
    """Tests for the MailingList model"""

    def setUp(self):
        self.contact_1 = Contact.objects.create(email='test1@domain.com')
        self.contact_2 = Contact.objects.create(email='test2@domain.com', valid=False)
        self.contact_3 = Contact.objects.create(email='test3@domain.com', subscriber=False)
        self.contact_4 = Contact.objects.create(email='test4@domain.com')

    def test_subscribers_count(self):
        mailinglist = MailingList(name='Test MailingList')
        mailinglist.save()
        self.assertEquals(mailinglist.subscribers_count(), 0)
        mailinglist.subscribers.add(self.contact_1, self.contact_2, self.contact_3)
        self.assertEquals(mailinglist.subscribers_count(), 3)

    def test_unsubscribers_count(self):
        mailinglist = MailingList.objects.create(name='Test MailingList')
        self.assertEquals(mailinglist.unsubscribers_count(), 0)
        mailinglist.unsubscribers.add(self.contact_1, self.contact_2, self.contact_3)
        self.assertEquals(mailinglist.unsubscribers_count(), 3)

    def test_expedition_set(self):
        mailinglist = MailingList.objects.create(name='Test MailingList')
        self.assertEquals(len(mailinglist.expedition_set()), 0)
        mailinglist.subscribers.add(self.contact_1, self.contact_2, self.contact_3)
        self.assertEquals(len(mailinglist.expedition_set()), 1)
        mailinglist.subscribers.add(self.contact_4)
        self.assertEquals(len(mailinglist.expedition_set()), 2)
        mailinglist.unsubscribers.add(self.contact_4)
        self.assertEquals(len(mailinglist.expedition_set()), 1)


class NewsletterTestCase(TestCase):
    """Tests for the Newsletter model"""

    def setUp(self):
        self.server = SMTPServer.objects.create(name='Test SMTP',
                                                host='smtp.domain.com')
        self.contact = Contact.objects.create(email='test@domain.com')
        self.mailinglist = MailingList.objects.create(name='Test MailingList')
        self.newsletter = Newsletter.objects.create(title='Test Newsletter',
                                                    article_1_text='Test Newsletter article text',
                                                    server=self.server)
        self.newsletter.mailing_lists.add(self.mailinglist)

    def test_mails_sent(self):
        self.assertEquals(self.newsletter.mails_sent(), 0)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contact,
                                            status=ContactMailingStatus.SENT)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contact,
                                            status=ContactMailingStatus.SENT_TEST)
        self.assertEquals(self.newsletter.mails_sent(), 1)


class TokenizationTestCase(TestCase):
    """Tests for the tokenization process"""

    def setUp(self):
        self.contact = Contact.objects.create(email='test@domain.com')

    def test_tokenize_untokenize(self):
        uidb36, token = tokenize(self.contact)
        self.assertEquals(untokenize(uidb36, token), self.contact)
        self.assertRaises(Http404, untokenize, 'toto', token)
        self.assertRaises(Http404, untokenize, uidb36, 'toto')


class MailerTestCase(TestCase):
    """Tests for the Mailer object"""

    def setUp(self):
        self.server = SMTPServer.objects.create(name='Test SMTP',
                                                host='smtp.domain.com',
                                                mails_hour=100)
        self.contacts = [Contact.objects.create(email='test1@domain.com'),
                         Contact.objects.create(email='test2@domain.com'),
                         Contact.objects.create(email='test3@domain.com'),
                         Contact.objects.create(email='test4@domain.com')]
        self.mailinglist = MailingList.objects.create(name='Test MailingList')
        self.mailinglist.subscribers.add(*self.contacts)
        self.newsletter = Newsletter.objects.create(title='Test Newsletter',
                                                    article_1_text='Test Newsletter Content',
                                                    slug='test-newsletter',
                                                    server=self.server,
                                                    status=Newsletter.WAITING)
        self.newsletter.mailing_lists.add(self.mailinglist)
        self.newsletter.test_contacts.add(*self.contacts[:2])

    def test_expedition_list(self):
        mailer = Mailer(self.newsletter, test=True)
        self.assertEquals(len(mailer.expedition_list), 2)
        self.server.mails_hour = 1
        self.assertEquals(len(mailer.expedition_list), 1)

        self.server.mails_hour = 100
        mailer = Mailer(self.newsletter)
        self.assertEquals(len(mailer.expedition_list), 4)
        self.server.mails_hour = 3
        self.assertEquals(len(mailer.expedition_list), 3)

        self.server.mails_hour = 100
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[0],
                                            status=ContactMailingStatus.SENT)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[1],
                                            status=ContactMailingStatus.SENT)
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[1],
                                            status=ContactMailingStatus.SENT)
        self.assertEquals(len(mailer.expedition_list), 2)
        self.assertFalse(self.contacts[0] in mailer.expedition_list)

    def test_can_send(self):
        mailer = Mailer(self.newsletter)

        self.assertTrue(mailer.can_send)

        # Checks credits
        self.server.mails_hour = 1
        ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                            contact=self.contacts[0],
                                            status=ContactMailingStatus.SENT)
        mailer = Mailer(self.newsletter)
        self.assertFalse(mailer.can_send)
        self.server.mails_hour = 10
        mailer = Mailer(self.newsletter)
        self.assertTrue(mailer.can_send)

        # Checks statut
        self.newsletter.status = Newsletter.DRAFT
        mailer = Mailer(self.newsletter)
        self.assertFalse(mailer.can_send)
        mailer = Mailer(self.newsletter, test=True)
        self.assertTrue(mailer.can_send)

        # Checks expedition time
        self.newsletter.status = Newsletter.WAITING
        self.newsletter.sending_date = datetime.utcnow().replace(tzinfo=utc) + timedelta(hours=1)
        mailer = Mailer(self.newsletter)
        self.assertFalse(mailer.can_send)
        self.newsletter.sending_date = datetime.utcnow().replace(tzinfo=utc)
        mailer = Mailer(self.newsletter)
        self.assertTrue(mailer.can_send)

    def test_run(self):
        mailer = Mailer(self.newsletter)
        mailer.smtp = FakeSMTP()
        mailer.run()
        self.assertEquals(mailer.smtp.mails_sent, 4)
        self.assertEquals(ContactMailingStatus.objects.filter(
            status=ContactMailingStatus.SENT, newsletter=self.newsletter).count(), 4)

        mailer = Mailer(self.newsletter, test=True)
        mailer.smtp = FakeSMTP()

        mailer.run()
        self.assertEquals(mailer.smtp.mails_sent, 2)
        self.assertEquals(ContactMailingStatus.objects.filter(
            status=ContactMailingStatus.SENT_TEST, newsletter=self.newsletter).count(), 2)

        mailer.smtp = None

    def test_update_newsletter_status(self):
        mailer = Mailer(self.newsletter, test=True)
        self.assertEquals(self.newsletter.status, Newsletter.WAITING)
        mailer.update_newsletter_status()
        self.assertEquals(self.newsletter.status, Newsletter.WAITING)

        mailer = Mailer(self.newsletter)
        self.assertEquals(self.newsletter.status, Newsletter.WAITING)
        mailer.update_newsletter_status()
        self.assertEquals(self.newsletter.status, Newsletter.SENDING)

        for contact in self.contacts:
            ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                                contact=contact,
                                                status=ContactMailingStatus.SENT)
        mailer.update_newsletter_status()
        self.assertEquals(self.newsletter.status, Newsletter.SENT)

    def test_update_newsletter_status_advanced(self):
        self.server.mails_hour = 2
        self.server.save()

        mailer = Mailer(self.newsletter)
        mailer.smtp = FakeSMTP()

        mailer.run()

        self.assertEquals(mailer.smtp.mails_sent, 2)
        self.assertEquals(ContactMailingStatus.objects.filter(
            status=ContactMailingStatus.SENT, newsletter=self.newsletter).count(), 2)
        self.assertEquals(self.newsletter.status, Newsletter.SENDING)

        self.server.mails_hour = 0
        self.server.save()

        mailer = Mailer(self.newsletter)
        mailer.smtp = FakeSMTP()
        mailer.run()

        self.assertEquals(mailer.smtp.mails_sent, 2)
        self.assertEquals(ContactMailingStatus.objects.filter(
            status=ContactMailingStatus.SENT, newsletter=self.newsletter).count(), 4)
        self.assertEquals(self.newsletter.status, Newsletter.SENT)

    def test_recipients_refused(self):
        server = SMTPServer.objects.create(name='Local SMTP', host='smtp.webfaction.com', user='fineuropsoditic', password='arpe77jaci')
        contact = Contact.objects.create(email='thisisaninvalidemail')
        self.newsletter.test_contacts.clear()
        self.newsletter.test_contacts.add(contact)
        self.newsletter.server = server
        self.newsletter.save()

        self.assertEquals(contact.valid, True)
        self.assertEquals(ContactMailingStatus.objects.filter(
            status=ContactMailingStatus.INVALID, newsletter=self.newsletter).count(), 0)

        mailer = Mailer(self.newsletter, test=True)
        mailer.run()

        self.assertEquals(Contact.objects.get(email='thisisaninvalidemail').valid, False)
        self.assertEquals(ContactMailingStatus.objects.filter(
            status=ContactMailingStatus.INVALID, newsletter=self.newsletter).count(), 1)