'''
Created on 17 May 2013

@author: mnagni
'''

import logging

from djcharme import mm_render_to_response
from djcharme.node.actions import  insert_rdf
from djcharme.views import isPOST


LOGGING = logging.getLogger(__name__)

HTML_NS = "{http://www.w3.org/1999/xhtml}"

'''
def extract_alternative_links(link):
    h = httplib2.Http(".cache")
    resp, content = h.request(link, "GET", headers={'accept':'*/*'} )
    parser = html5lib.HTMLParser(tree=html5lib.getTreeBuilder("lxml"))
    doc = parser.parse(content)
    ret = []
    for el in doc.findall('%shead//%slink' % (HTML_NS, HTML_NS)):
        if hasattr(el, 'attrib') and el.attrib.has_key('rel') \
                and el.attrib['rel'] == "alternate":
            ret.append(el.get('type'))
    print ret
'''


def compose_annotation(request):
    context = {}
    logging.debug(request)

    if request.REQUEST.get('target_link', None):
        context['target_link'] = request.REQUEST.get('target_link')
        return mm_render_to_response(request, context,
                                     'compose_annotation.html')

    if isPOST(request):
        insert_rdf('', request.body, request.user, request.client)
    # target_link = request.REQUEST['target_link']
    # extract_alternative_links(target_link)
    return mm_render_to_response(request, context, 'compose_annotation.html')
