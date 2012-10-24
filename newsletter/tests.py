"""Unit tests for emencia.django.newsletter"""
from datetime import datetime
from datetime import timedelta
from tempfile import NamedTemporaryFile
from smtplib import SMTP

from django.test import TestCase
from django.http import Http404
from django.db import IntegrityError
from django.core.files import File
from django.utils.encoding import smart_str

from dry_newsletter.newsletter.mailer import Mailer
from dry_newsletter.newsletter.models import Contact
from dry_newsletter.newsletter.models import MailingList
from dry_newsletter.newsletter.models import SMTPServer
from dry_newsletter.newsletter.models import Newsletter

from dry_newsletter.newsletter.utils.tokens import tokenize
from dry_newsletter.newsletter.utils.tokens import untokenize

class FakeSMTP(object):
    mails_sent = 0

    def sendmail(self, *ka, **kw):
        self.mails_sent += 1
        return {}

    def quit(*ka, **kw):
        pass

class ExpeditionListTestCase(TestCase):
    """Tests for the Newsletter model"""

    def setUp(self):
        self.server = SMTPServer.objects.create(name='Test SMTP', host='smtp.webfaction.com', user='fineuropsoditic', password='arpe77jaci')
        self.contact_1 = Contact.objects.create(email='albertojacini@gmail.com')
        self.contact_2 = Contact.objects.create(email='albertojacini@hotmail.com')
        self.mailing_list_1 = MailingList.objects.create(name='Fornitori')
        self.mailing_list_2 = MailingList.objects.create(name='Giornalisti')
        self.mailing_list_1.subscribers.add(self.contact_1)
        self.mailing_list_2.subscribers.add(self.contact_1, self.contact_2)
        self.newsletter = Newsletter.objects.create(title='Test Newsletter', content='Test Newsletter Content', server=self.server)
        self.newsletter.mailing_lists.add(self.mailing_list_1)
        # self.newsletter.status = 2
        self.newsletter.save()
        self.mailer = Mailer(self.newsletter, verbose=1)

    def test_expedition_list(self):
        #print len(self.mailer.expedition_list)
        for c in self.mailer.expedition_list:
            for a in c:
                print(a.email)
        #self.assertEqual(len(self.mailer.expedition_list), 3)
        #self.assertIn(self.contact_1, self.mailer.expedition_list)
        #self.assertIn(self.contact_2, self.mailer.expedition_list, 'Anche il secondo contatto e nella lista')
        #print('{}, {}'.format(self.contact_1.email, self.contact_2.email))

class MailerTestCase(TestCase):
    """Tests for the Mailer object"""

    def setUp(self):
        self.server = SMTPServer.objects.create(name='Test SMTP', host='smtp.webfaction.com', user='fineuropsoditic', password='arpe77jaci', mails_hour=100)
        self.contacts = [Contact.objects.create(email='test1@domain.com'),
                         Contact.objects.create(email='test2@domain.com'),
                         Contact.objects.create(email='test3@domain.com'),
                         Contact.objects.create(email='test4@domain.com')]
        self.MailingList = MailingList.objects.create(title='Test MailingList')
        for c in self.contacts:
            c.categories.add(self.MailingList)
        self.newsletter = Newsletter.objects.create(title='Test Newsletter',
                                                    content='Test Newsletter Content',
                                                    slug='test-newsletter',
                                                    server=self.server)
        self.newsletter.categories.add(self.MailingList)


class SMTPServerTestCase(TestCase):
    """Tests for the SMTPServer model"""

    def setUp(self):
        self.server = SMTPServer.objects.create(name='Test SMTP', host='smtp.webfaction.com', user='fineuropsoditic', password='arpe77jaci')
        self.server_2 = SMTPServer.objects.create(name='Test SMTP 2', host='smtp.gmail.com', user='albertojacini@gmail.com', password='03g10m77')
        self.contact = Contact.objects.create(email='albertojacini@hotmail.com')
        self.mailing_list = MailingList.objects.create(title='Test MailingList')
        self.contact.categories.add(self.MailingList)
        self.newsletter = Newsletter.objects.create(title='Test Newsletter', content='Test Newsletter Content', server=self.server, slug='test-nl')
        self.newsletter.categories.add(self.MailingList)
        self.newsletter.status = Newsletter.SENDING

        
    def test_run(self):
        mailer = Mailer(self.newsletter)
        mailer.run()
        self.assertEqual(self.newsletter.status, Newsletter.SENT)