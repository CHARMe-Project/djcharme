'''
Created on 14 May 2013

@author: mnagni
'''
from djcharme.node.actions import _do_query
from django.http.response import HttpResponseRedirectBase, Http404, HttpResponse
from djcharme import mm_render_to_response

import logging

LOGGING = logging.getLogger(__name__)


def demo(request):   
    LOGGING.info("Demo")
    return HttpResponse()