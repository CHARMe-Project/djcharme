'''
Created on 14 May 2013

@author: mnagni
'''
import json
import logging

from django.contrib import messages
from django.http.response import (HttpResponseRedirectBase, HttpResponse,
                                  HttpResponseNotFound)
from django.views.decorators.csrf import csrf_exempt

from djcharme import mm_render_to_response, mm_render_to_response_error
from djcharme.exception import NotFoundError
from djcharme.exception import ParseError
from djcharme.exception import SecurityError
from djcharme.exception import StoreConnectionError
from djcharme.exception import UserError
from djcharme.node.actions import (OA, FORMAT_MAP, find_annotation_graph,
                                   insert_rdf, ANNO_SUBMITTED, DATA,
                                   _collect_annotations, find_resource_by_id,
                                   change_annotation_state, PAGE)
from djcharme.views import (isDELETE, isPOST, content_type,
                            validate_mime_format, isOPTIONS, http_accept,
                            get_format, check_mime_format, get_depth)


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


    req_format = validate_mime_format(request)

    if req_format is not None:
        LOGGING.debug("Annotations %s",
                      str(__serialize(tmp_g, req_format=req_format)))
        return HttpResponse(__serialize(tmp_g, req_format=req_format))
    elif 'text/html' in http_accept(request):
        states = {}
        LOGGING.debug("Annotations %s", str(tmp_g.serialize()))
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
        ret_format = check_mime_format(ret_format)

    if ret_format is None:
        ret_format = req_format
    return ret_format


def __get_req_format(request):
    '''
        Extracts the request format otherwise return the req_format
    '''
    return check_mime_format(content_type(request))


# Temporary solution as long identify a solution for csrf
# @csrf_protect
@csrf_exempt
def insert(request):
    '''
        Inserts in the triplestore a new annotation under the "ANNO_SUBMITTED"
        graph
    '''
    try:
        return _insert(request)
    except Exception as ex:
        LOGGING.error("insert - unexpected error: %s", str(ex))
        messages.add_message(request, messages.ERROR, str(ex))
        return mm_render_to_response_error(request, '500.html', 500)


def _insert(request):
    '''
        Inserts in the triplestore a new annotation under the "ANNO_SUBMITTED"
        graph
    '''
    req_format = __get_req_format(request)
    ret_format = __get_ret_format(request, req_format)

    if req_format is None:
        messages.add_message(request, messages.ERROR,
                             "Cannot ingest the posted format")
        return mm_render_to_response_error(request, '400.html', 400)

    if isPOST(request) or isOPTIONS(request):
        triples = request.body
        try:
            anno_uri = insert_rdf(triples, req_format, request.user,
                                  request.client, graph=ANNO_SUBMITTED)
        except ParseError as ex:
            LOGGING.debug("insert parsing error: %s", str(ex))
            messages.add_message(request, messages.ERROR, str(ex))
            return mm_render_to_response_error(request, '400.html', 400)
        return HttpResponse(anno_uri, content_type=FORMAT_MAP.get(ret_format))


# Temporary solution as long identify a solution for csrf
# @csrf_protect
@csrf_exempt
def advance_status(request):
    '''
        Advance the status of an annotation
    '''
    try:
        return _advance_status(request)
    except NotFoundError as ex:
        messages.add_message(request, messages.ERROR, str(ex))
        return mm_render_to_response_error(request, '404.html', 404)
    except SecurityError as ex:
        messages.add_message(request, messages.ERROR, str(ex))
        return mm_render_to_response_error(request, '403.html', 403)
    except UserError as ex:
        messages.add_message(request, messages.ERROR, str(ex))
        return mm_render_to_response_error(request, '400.html', 400)
    except Exception as ex:
        LOGGING.error("advance_status - unexpected error: %s", str(ex))
        messages.add_message(request, messages.ERROR, str(ex))
        return mm_render_to_response_error(request, '500.html', 500)


def _advance_status(request):
    '''
        Advance the status of an annotation
    '''
    if isPOST(request) and ('application/ld+json' in content_type(request) or
                            'application/json' in content_type(request)):
        params = json.loads(request.body)
        if not params.has_key('annotation') or not params.has_key('toState'):
            messages.add_message(request, messages.ERROR,
                                 "Missing annotation/state parameters")
            return mm_render_to_response_error(request, '400.html', 400)
        LOGGING.info("advancing %s to state:%s", str(params.get('annotation')),
                     str(params.get('toState')))
        change_annotation_state(params.get('annotation'),
                                params.get('toState'), request)
        return HttpResponse(status=204)
    elif not isPOST(request):
        messages.add_message(request, messages.ERROR,
                             "Message must be a POST")
        return mm_render_to_response_error(request, '405.html', 405)
    else:
        messages.add_message(request, messages.ERROR,
                             "Message must contain application/ld+json")
        return mm_render_to_response_error(request, '400.html', 400)


@csrf_exempt
def process_resource(request, resource_id):
    """
        Process the resource dependent on the mime format.
    """
    try:
        if isDELETE(request):
            return _delete(request, resource_id)
        return _process_resource(request, resource_id)
    except Exception as ex:
        LOGGING.error("process_resource - unexpected error: %s", str(ex))
        messages.add_message(request, messages.ERROR, str(ex))
        return mm_render_to_response_error(request, '500.html', 500)


def _delete(request, resource_id):
    """
        Delete the resource, move it to the 'retired' graph.
    """
    LOGGING.info("advancing %s to state:retired", str(resource_id))
    try:
        change_annotation_state(resource_id, 'retired', request)
    except NotFoundError as ex:
        messages.add_message(request, messages.ERROR, str(ex))
        return mm_render_to_response_error(request, '404.html', 404)
    except SecurityError as ex:
        messages.add_message(request, messages.ERROR, str(ex))
        return mm_render_to_response_error(request, '403.html', 403)
    return HttpResponse(status=204)


def _process_resource(request, resource_id):
    """
        Process the resource dependent on the mime format.
    """
    if validate_mime_format(request) is not None:
        getformat = get_format(request)
        path = "/%s/%s" % (DATA, resource_id)
        if getformat is not None:
            path = "%s/?format=%s" % (path, getformat)
        LOGGING.info("Redirecting to %s", str(path))
        return HttpResponseSeeOther(path)

    if 'text/html' in http_accept(request):
        LOGGING.info("Redirecting to /%s/%s", str(PAGE), str(resource_id))
        return HttpResponseSeeOther('/%s/%s' % (PAGE, resource_id))
    return HttpResponseNotFound()


def process_data(request, resource_id):
    """
        Process the data dependent on the mime format.
    """
    try:
        return _process_data(request, resource_id)
    except Exception as ex:
        LOGGING.error("process_data - unexpected error: %s", str(ex))
        messages.add_message(request, messages.ERROR, str(ex))
        return mm_render_to_response_error(request, '500.html', 500)


def _process_data(request, resource_id):
    """
        Process the data dependent on the mime format.
    """
    if get_format(request) is None and 'text/html' in http_accept(request):
        return process_resource(request, resource_id=resource_id)

    req_format = validate_mime_format(request)
    if req_format is None:
        return process_resource(request, resource_id)

    tmp_g = find_resource_by_id(resource_id, get_depth(request))
    return HttpResponse(tmp_g.serialize(format=req_format),
                        mimetype=FORMAT_MAP.get(req_format))


def process_page(request, resource_id=None):
    """
        Process the page dependent on the mime format.
    """
    try:
        return _process_page(request, resource_id)
    except Exception as ex:
        LOGGING.error("process_page - unexpected error: %s", str(ex))
        messages.add_message(request, messages.ERROR, str(ex))
        return mm_render_to_response_error(request, '500.html', 500)


def _process_page(request, resource_id=None):
    """
        Process the page dependent on the mime format.
    """
    if 'text/html' not in http_accept(request):
        return process_resource(request, resource_id)

    tmp_g = find_resource_by_id(resource_id, get_depth(request))
    context = {'results': tmp_g.serialize()}
    return mm_render_to_response(request, context, 'viewer.html')
