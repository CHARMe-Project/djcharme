__version__ = '0.4.1'


import os

from django.core.context_processors import csrf
from django.core.exceptions import ObjectDoesNotExist
from django.http.response import Http404
from django.shortcuts import render_to_response, render
from django.template.context import RequestContext
from django.contrib.sites.models import Site


LOAD_SAMPLE = 'LOAD_SAMPLE'
HTTP_PROXY = 'HTTP_PROXY'
HTTP_PROXY_PORT = 'HTTP_PROXY_PORT'

MY_SITE = Site.objects.get(pk=settings.SITE_ID)
MY_SITE.domain = settings.SITE_DOMAIN
MY_SITE.name = settings.SITE_NAME
MY_SITE.save()

def get_resource(file_name):
    return os.path.join(__path__[0], 'resources', file_name)


def mm_render_to_response(request, context, page_to_render):
    """
    Exploits a 'render_to_response' action. The advantage of this method
    is to contains a number of operations that are expected to be  called
    for each page rendering, for example passing the application version number

    **Parameters**
        * HttpRequest_ **request**
            a django HttpRequest instance
        * `dict` **context**
            a dictionary where to pass parameter to the rendering function
        * `string` **page_to_render**
            the html page to render
    """
    if context is None or not isinstance(context, dict):
        raise Exception("Cannot render an empty context")

    # context['version'] = assemble_version()
    context.update(csrf(request))
    rcontext = RequestContext(request, context)
    return render_to_response(page_to_render, rcontext)


def mm_render_to_response_error(request, page_to_render, status):
    """
    Exploits a 'render_to_response' action. The advantage of this method
    is to contains a number of operations that are expected to be  called
    for each page rendering, for example passing the application version number

    **Parameters**
        * HttpRequest_ **request**
            a django HttpRequest instance
        * `dict` **context**
            a dictionary where to pass parameter to the rendering function
        * `string` **page_to_render**
            the html page to render
    """
    context = {}
    context.update(csrf(request))
    rcontext = RequestContext(request, context)
    return render(request, page_to_render, context_instance=rcontext,
                  status=status)
