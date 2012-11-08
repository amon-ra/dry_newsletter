"""Utils for importation of contacts"""
import csv
from datetime import datetime

from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from dry_newsletter.newsletter.models import Contact
from dry_newsletter.newsletter.models import MailingList


COLUMNS = ['email', 'first_name', 'last_name']
csv.register_dialect('semicolon', delimiter=';')


def create_contact(contact_dict):
    """Create a contact and validate the mail"""
    contact_dict['email'] = contact_dict['email'].strip()
    try:
        validate_email(contact_dict['email'])
        contact_dict['valid'] = True
    except ValidationError:
        contact_dict['valid'] = False

    contact, created = Contact.objects.get_or_create(
        email=contact_dict['email'],
        defaults=contact_dict)

    return contact, created


def create_contacts(contact_dicts, importer_name):
    """Create all the contacts to import and
    associated them in a mailing list"""
    inserted = 0
    when = str(datetime.now()).split('.')[0]
    mailing_list = MailingList(
        name=_('Mailing list created by importation at %s') % when,
        description=_('Contacts imported by %s.') % importer_name)
    mailing_list.save()

    for contact_dict in contact_dicts:
        contact, created = create_contact(contact_dict)
        mailing_list.subscribers.add(contact)
        inserted += int(created)

    return inserted

def text_contacts_import(stream):
    """Import contact from a plaintext file, like CSV"""
    contacts = []
    contact_reader = csv.reader(stream, dialect='semicolon')

    for contact_row in contact_reader:
        contact = {}
        for i in range(len(contact_row)):
            contact[COLUMNS[i]] = contact_row[i]
        contacts.append(contact)

    return create_contacts(contacts, 'text')

def import_dispatcher(source, type_):
    """Select importer and import contacts"""
    if type_ == 'text':
        return text_contacts_import(source)
    elif type_ == 'text_mailup_format':
        return mailup_contacts_import(source)
    return 0

# Mailing list importing

MAILING_LIST_COLUMNS = ['id', 'name']

def create_mailing_list(ml_dict):
    """Create a mailing list"""
    mailing_list, created = MailingList.objects.get_or_create(id=ml_dict['id'], name=ml_dict['name'],)
    return mailing_list, created

def create_mailing_lists(ml_dicts):
    """Create all the mailing lists to import"""
    inserted = 0

    for ml_dict in ml_dicts:
        mailing_list, created = create_mailing_list(ml_dict)
        inserted += int(created)
    return inserted

def import_mailing_lists(stream):
    """Import contact from a plaintext file, like CSV"""
    mailing_lists = []
    ml_reader = csv.reader(stream, dialect='comma')

    for ml_row in ml_reader:
        ml = {}
        for i in range(len(ml_row)):
            ml[MAILING_LIST_COLUMNS[i]] = ml_row[i]
        mailing_lists.append(ml)

    return create_mailing_lists(mailing_lists)

# Contacts importing from mailup.com

MAILUP_CONTACTS_COLUMNS = ['email', 'first_name', 'last_name', 'mailing_lists']

def mailup_create_contact(contact_dict):
    """Create a contact and validate the mail"""
    if 'mailing_lists' in contact_dict:
        mailing_lists = contact_dict.pop('mailing_lists')
    contact_dict['email'] = contact_dict['email'].strip()
    try:
        validate_email(contact_dict['email'])
        contact_dict['valid'] = True
    except ValidationError:
        contact_dict['valid'] = False

    contact, created = Contact.objects.get_or_create(email=contact_dict['email'], first_name=contact_dict['first_name'], last_name=contact_dict['last_name'])

    try:
        for ml in mailing_lists:
            mailing_list = MailingList.objects.get(id=ml)
            mailing_list.subscribers.add(contact)
    except:
        pass

    return contact, created

def mailup_create_contacts(contact_dicts):
    """Create all the contacts to import and
    associated them in a mailing list"""
    inserted = 0

    for contact_dict in contact_dicts:
        contact, created = mailup_create_contact(contact_dict)
        inserted += int(created)

    return inserted

def mailup_contacts_import(stream):
    """Import contact from a plaintext file, in the mailup format: 'email@email.com; First_name; Last_name;1,5,8'. Where 1,5,8 are the ids of the mailing lists to which the contact subscribes"""
    contacts = []
    contact_reader = csv.reader(stream, dialect='semicolon')

    for contact_row in contact_reader:
        contact = {}
        for i in range(len(contact_row)):
            contact[MAILUP_CONTACTS_COLUMNS[i]] = contact_row[i]
        
        if len(contact_row) == 4 :
            contact[MAILUP_CONTACTS_COLUMNS[3]] = [ int(i) for i in contact_row[3].split(',') ]
        else contact[MAILUP_CONTACTS_COLUMNS[3]] = [2] # Newsletter con id 2, lista default

        contacts.append(contact)

    return mailup_create_contacts(contacts)