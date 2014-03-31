'''
Created on 14 May 2013

@author: mnagni
'''
from djcharme.node.actions import (OA, FORMAT_MAP, find_annotation_graph,
                                   insert_rdf, ANNO_SUBMITTED, DATA,
                                   _collect_annotations, find_resource_by_id,
                                   change_annotation_state, PAGE)
from djcharme import mm_render_to_response, mm_render_to_response_error
from djcharme.exception import StoreConnectionError
from djcharme.views import (isPOST, content_type, validateMimeFormat,
                            isOPTIONS, http_accept, get_format, checkMimeFormat,
                            get_depth)

from django.http.response import HttpResponseRedirectBase, Http404, HttpResponse

from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

import logging
import json

LOGGING = logging.getLogger(__name__)


class HttpResponseSeeOther(HttpResponseRedirectBase):
    '''
        Implements a simple HTTP 303 response
    '''
    status_code = 303


def __serialize(graph, req_format='application/rdf+xml'):
    '''
        Serializes a graph according to the required format
        - rdflib:Graph **graph** the graph to serialize
        - string **req_format** the serialization format
        - **return** the serialized graph
    '''
    if req_format == FORMAT_MAP['json-ld']:
        req_format = 'json-ld'

    return graph.serialize(format=req_format)



def index(request, graph='stable'):
    '''
        Returns a tabular view of the stored annotations.
        - HTTPRequest **request** the client request
        - string **graph**  the required named graph
        TODO: In a future implementation this actions should be supported by an 
        OpenSearch implementation
    '''
    tmp_g = None
    try:
        tmp_g = _collect_annotations(graph)
    except StoreConnectionError as ex:
        messages.add_message(request, messages.ERROR, ex)
        return mm_render_to_response_error(request, '503.html', 503)


    req_format = validateMimeFormat(request)

    if req_format is not None:
        LOGGING.debug("Annotations %s" % 
                      __serialize(tmp_g, req_format=req_format))
        return HttpResponse(__serialize(tmp_g, req_format=req_format))
    elif 'text/html' in http_accept(request):
        states = {}
        LOGGING.debug("Annotations %s" % tmp_g.serialize())
        for subject, pred, obj in tmp_g.triples((None, None, OA['Annotation'])):
            states[subject] = find_annotation_graph(subject)

        context = {'results': tmp_g.serialize(), 'states': json.dumps(states)}
        return mm_render_to_response(request, context, 'viewer.html')

    messages.add_message(request, messages.ERROR, "Format not accepted")
    return mm_render_to_response_error(request, '400.html', 400)


def __get_ret_format(request, req_format):
    '''
        Extracts the return format otherwise return the req_format
    '''
    ret_format = http_accept(request)
    if type(ret_format) == list:
        ret_format = ret_format[0]

    if ret_format is None:
        ret_format = req_format
    else:
        ret_format = checkMimeFormat(ret_format)

    if ret_format is None:
        ret_format = req_format
    return ret_format


def __get_req_format(request):
    '''
        Extracts the request format otherwise return the req_format
    '''
    return checkMimeFormat(content_type(request))

# Temporary solution as long identify a solution for csrf
# @csrf_protect
@csrf_exempt
def insert(request):
    '''
        Inserts in the triplestore a new annotation under the "ANNO_SUBMITTED"
        graph
    '''
    '''
    kwargs = {}
    kwargs['client_id'] = '1-2-3-4-5-6'
    kwargs['response_type'] = 'token'
    kwargs['redirect_uri'] = 'http://localhost:8000/index/submitted'
    return HttpResponseRedirect(reverse('oauth2:authorize'), kwargs=kwargs)
    '''
    req_format = __get_req_format(request)
    ret_format = __get_ret_format(request, req_format)

    if req_format is None:
        messages.add_message(request, messages.ERROR,
                             "Cannot ingest the posted format")
        return mm_render_to_response_error(request, '400.html', 400)

    if isPOST(request) or isOPTIONS(request):
        triples = request.body
        insert_rdf(triples, req_format, graph=ANNO_SUBMITTED)        
        return HttpResponse(None, content_type=FORMAT_MAP.get(ret_format))

# Temporary solution as long identify a solution for csrf
# @csrf_protect
@csrf_exempt
def advance_status(request):
    '''
        Advance the status of an annotation
    '''
    if isPOST(request) and 'application/json' in content_type(request):
        params = json.loads(request.body)
        if not params.has_key('annotation') or not params.has_key('state'):
            messages.add_message(request, messages.ERROR,
                                 "Missing annotation/state parameters")
            return mm_render_to_response_error(request, '400.html', 400)
        LOGGING.info("advancing %s to state:%s" % (params.get('annotation'),
                                                   params.get('toState')))
        tmp_g = change_annotation_state(params.get('annotation'),
                                        params.get('toState'))

        return HttpResponse(tmp_g.serialize())


def process_resource(request, resource_id):
    if validateMimeFormat(request) is not None:
        getformat = get_format(request)
        path = "/%s/%s" % (DATA, resource_id)
        if getformat is not None:
            path = "%s/?format=%s" % (path, getformat)
        LOGGING.info("Redirecting to %s" % path)
        return HttpResponseSeeOther(path)

    if 'text/html' in http_accept(request):
        LOGGING.info("Redirecting to /%s/%s" % (PAGE, resource_id))
        return HttpResponseSeeOther('/%s/%s' % (PAGE, resource_id))
    return Http404()

def process_data(request, resource_id):
    if get_format(request) is None and 'text/html' in http_accept(request):
        return process_resource(request, resource_id=resource_id)

    req_format = validateMimeFormat(request)
    if req_format is None:
        return process_resource(request, resource_id)

    tmp_g = find_resource_by_id(resource_id, get_depth(request))
    return HttpResponse(tmp_g.serialize(format=req_format),
                            mimetype=FORMAT_MAP.get(req_format))

def process_page(request, resource_id=None):
    if 'text/html' not in http_accept(request):
        return process_resource(request, resource_id)

    tmp_g = find_resource_by_id(resource_id, get_depth(request))
    context = {'results': tmp_g.serialize()}
    return mm_render_to_response(request, context, 'viewer.html')
