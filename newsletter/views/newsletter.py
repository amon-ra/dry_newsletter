"""Views for dry_newsletter.newsletter Newsletter"""
from django.template import RequestContext
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response

from django.contrib.sites.models import Site
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string as render_file

from dry_newsletter.newsletter.models import Newsletter
from dry_newsletter.newsletter.models import ContactMailingStatus
from dry_newsletter.newsletter.utils import render_string
from dry_newsletter.newsletter.utils.tokens import untokenize

def render_newsletter(request, slug, context):
    """Return a newsletter in HTML format"""
    newsletter = get_object_or_404(Newsletter, slug=slug)
    context.update({'newsletter': newsletter, 'domain': Site.objects.get_current().domain})
    return render_to_response('newsletter/newsletter_detail.html', context, context_instance=RequestContext(request))

@login_required
def view_newsletter_preview(request, slug):
    """View of the newsletter preview"""
    context = {'contact': request.user}
    return render_newsletter(request, slug, context)

def view_newsletter_contact(request, slug, uidb36, token):
    """Visualization of a newsletter by an user"""
    newsletter = get_object_or_404(Newsletter, slug=slug)
    contact = untokenize(uidb36, token)
    ContactMailingStatus.objects.create(newsletter=newsletter,
                                        contact=contact,
                                        status=ContactMailingStatus.OPENED_ON_SITE)
    context = {'contact': contact, 'uidb36': uidb36, 'token': token}
    return render_newsletter(request, slug, context)

def view_newsletter_online_version(request, slug):
    """View the online version"""
    context = {'contact': request.user}
    return render_newsletter(request, slug, context)