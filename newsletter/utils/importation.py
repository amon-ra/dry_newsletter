"""Utils for importation of contacts"""
import csv
from datetime import datetime

from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from dry_newsletter.newsletter.models import Contact
from dry_newsletter.newsletter.models import MailingList


COLUMNS = ['email', 'first_name', 'last_name', 'tags']
csv.register_dialect('semicolon', delimiter=';')
csv.register_dialect('comma', delimiter=',')


def create_contact(contact_dict, workgroups=[]):
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


def create_contacts(contact_dicts, importer_name, workgroups=[]):
    """Create all the contacts to import and
    associated them in a mailing list"""
    inserted = 0
    when = str(datetime.now()).split('.')[0]
    mailing_list = MailingList(
        name=_('Mailing list created by importation at %s') % when,
        description=_('Contacts imported by %s.') % importer_name)
    mailing_list.save()

    for workgroup in workgroups:
        workgroup.mailinglists.add(mailing_list)

    for contact_dict in contact_dicts:
        contact, created = create_contact(contact_dict, workgroups)
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

    return create_contacts(contacts, 'text', workgroups)


def import_dispatcher(source, type_):
    """Select importer and import contacts"""
    if type_ == 'text':
        return text_contacts_import(source)
    elif type_ == 'excel':
        return excel_contacts_import(source)
    return 0

# Mailing list importing

ML_COLUMNS = ['id', 'name']

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
            ml[ML_COLUMNS[i]] = ml_row[i]
        mailing_lists.append(ml)

    return create_mailing_lists(mailing_lists)