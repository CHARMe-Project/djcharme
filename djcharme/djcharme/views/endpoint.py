'''
Created on 14 May 2013

@author: mnagni
'''
import httplib
import json
import logging
import urllib

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http.response import (HttpResponseRedirectBase,
                                  HttpResponseNotFound, HttpResponse)
from rdflib.graph import ConjunctiveGraph
from rdflib.term import URIRef

from djcharme import mm_render_to_response, mm_render_to_response_error, \
    settings
from djcharme.charme_middleware import CharmeMiddleware
from djcharme.exception import SerializeError, StoreConnectionError
from djcharme.node.actions import OA, FORMAT_MAP, \
    ANNO_SUBMITTED, insert_rdf, find_resource_by_id, RESOURCE, \
    _collect_annotations, change_annotation_state, find_annotation_graph, \
    generate_graph, rdf_format_from_mime
from djcharme.views import isGET, isPOST, isPUT, isDELETE, \
    isHEAD, isPATCH, http_accept, content_type


LOGGING = logging.getLogger(__name__)


class HttpResponseSeeOther(HttpResponseRedirectBase):
    status_code = 303


def endpoint(request):
    if isGET(request):
        return processGET(request)
    if isPUT(request):
        return processPUT(request)
    if isDELETE(request):
        return processDELETE(request)
    if isPOST(request):
        return processPOST(request)
    if isHEAD(request):
        return processHEAD(request)
    if isPATCH(request):
        return processPATCH(request)


def get_graph_from_request(request):
    graph = request.GET.get('graph', 'default')

    if graph == 'default':
        graph = None
    return graph


def _get_connection():
    '''
        Returns an httplib.HTTPConnection instance pointing to
        settings.FUSEKI_URL
    '''
    return httplib.HTTPConnection(getattr(settings, 'FUSEKI_URL'),
                                  port=getattr(settings, 'FUSEKI_PORT'))


def _submit_get(graph, accept):
    headers = {"Accept": accept}
    params = urllib.urlencode({'graph': graph})
    conn = _get_connection()
    conn.request('GET', getattr(settings, 'GRAPH_STORE_RW_PATH'),
                 params, headers)
    response = conn.getresponse()
    return response


def processGET(request):
    '''
        Returns an httplib.HTTPRequest
    '''
    return processHEAD(request, True)


def processPUT(request):
    graph = get_graph_from_request(request)
    payload = request.body

    conjunctive_graph = None
    query_object = None
    if graph is None:
        conjunctive_graph = ConjunctiveGraph(store=CharmeMiddleware.get_store())
        query_object = '''
            DROP SILENT DEFAULT;
            '''
        query_object = ''
    else:
        conjunctive_graph = ConjunctiveGraph(store=CharmeMiddleware.get_store())
        query_object = '''
            DROP SILENT GRAPH <%s>;
            '''
        query_object = query_object % (graph)
    conjunctive_graph.update(query_object)
    insert_rdf(payload,
               content_type(request),
               request.user,
               graph)

    return HttpResponse(status=204)


def processDELETE(request):
    graph = get_graph_from_request(request)

    conjunctive_graph = None
    query_object = None
    if graph is None:
        conjunctive_graph = ConjunctiveGraph(store=CharmeMiddleware.get_store())
        query_object = '''
            DROP DEFAULT;
            '''
        query_object = ''
    else:
        conjunctive_graph = ConjunctiveGraph(store=CharmeMiddleware.get_store())
        query_object = '''
            DROP GRAPH <%s>;
            '''
        query_object = query_object % (graph)
    conjunctive_graph.update(query_object)

    return HttpResponse(status=204)


def processPOST(request):
    graph = get_graph_from_request(request)
    payload = request.body
    insert_rdf(payload,
               content_type(request),
               request.user,
               graph)

    return HttpResponse(status=204)


def processHEAD(request, return_content=False):
    '''
        Returns an httplib.HTTPRequest
    '''
    graph = get_graph_from_request(request)
    accept = http_accept(request)

    if accept not in FORMAT_MAP.values():
        return HttpResponse(status=406)

    conjunctive_graph = None
    if graph is None:
        conjunctive_graph = ConjunctiveGraph(store=CharmeMiddleware.get_store())
    else:
        conjunctive_graph = generate_graph(CharmeMiddleware.get_store(),
                                           URIRef(graph))

    content = conjunctive_graph.serialize(format=rdf_format_from_mime(accept))

    if return_content:
        return HttpResponse(content=content)
    return HttpResponse()


def processPATCH(request):
    return HttpResponse(status=501)


def __serialize(graph, req_format='application/rdf+xml'):
    '''
        Serializes a graph according to the required format
    '''
    if req_format == 'application/ld+json':
        req_format = 'json-ld'
    return graph.serialize(format=req_format)


def _validate_mime_format(request):
    req_format = request.META.get('HTTP_ACCEPT', None)
    if req_format:
        for k, value in FORMAT_MAP.iteritems():
            if req_format == value:
                return k
    return None


def _validate_format(request):
    '''
        Returns the mimetype of the required format as mapped by rdflib
        return: String - an allowed rdflib mimetype
    '''
    req_format = None
    if isGET(request):
        req_format = FORMAT_MAP.get(request.GET.get('format', None))
    if isPOST(request):
        req_format = request.environ.get('CONTENT_TYPE', None)

    if req_format:
        if req_format not in FORMAT_MAP.values():
            raise SerializeError("Cannot generate the required format %s "
                                 % req_format)
    return req_format


@login_required
def index(request, graph='stable'):
    '''
        Returns a tabular view of the stored annotations.
        *request: HTTPRequest - the client request
        *graph: String -  the required named graph
        TDB - In a future implementation this actions should be supported by an
        OpenSearch implementation
    '''
    tmp_g = None
    try:
        tmp_g = _collect_annotations(graph)
    except StoreConnectionError as ex:
        messages.add_message(request, messages.ERROR, ex)
        return mm_render_to_response_error(request, '503.html', 503)


    req_format = _validate_format(request)

    if req_format:
        LOGGING.debug("Annotations %s", str(__serialize(tmp_g,
                                                     req_format=req_format)))
        return HttpResponse(__serialize(tmp_g, req_format=req_format))

    states = {}
    LOGGING.debug("Annotations %s", str(tmp_g.serialize()))
    for subject, pred, obj in tmp_g.triples((None, None, OA['Annotation'])):
        states[subject] = find_annotation_graph(subject)

    context = {'results': tmp_g.serialize(), 'states': json.dumps(states)}
    return mm_render_to_response(request, context, 'viewer.html')


def insert(request):
    '''
        Inserts in the triplestore a new annotation under the "ANNO_SUBMITTED"
        graph
    '''
    req_format = _validate_format(request)

    if request.method == 'POST':
        triples = request.body
        tmp_g = insert_rdf(triples, req_format, request.user, graph=ANNO_SUBMITTED)
        return HttpResponse(__serialize(tmp_g, req_format=req_format))


def advance_status(request):
    '''
        Advance the status of an annotation
    '''
    if isPOST(request) and 'application/json' in content_type(request):
        params = json.loads(request.body)
        LOGGING.info("advancing %s to state:%s", str(params.get('annotation')),
                     str(params.get('toState')))
        tmp_g = change_annotation_state(params.get('annotation'),
                                        params.get('toState'))

        return HttpResponse(tmp_g.serialize())


def process_resource(request, resource_id):
    if _validate_mime_format(request):
        LOGGING.info("Redirecting to /%s/%s", str(RESOURCE), str(resource_id))
        return HttpResponseSeeOther('/%s/%s' % (RESOURCE, resource_id))
    if 'text/html' in request.META.get('HTTP_ACCEPT', None):
        LOGGING.info("Redirecting to /page/%s", str(resource_id))
        return HttpResponseSeeOther('/page/%s' % resource_id)
    return HttpResponseNotFound()


def process_data(request, resource_id):
    req_format = _validate_mime_format(request)
    if req_format is None:
        return process_resource(request, resource_id)

    tmp_g = find_resource_by_id(resource_id)
    return HttpResponse(tmp_g.serialize(format=req_format),
                        mimetype=request.META.get('HTTP_ACCEPT'))


def process_page(request, resource_id=None):
    if 'text/html' not in request.META.get('HTTP_ACCEPT', None):
        process_resource(request, resource_id)

    tmp_g = find_resource_by_id(resource_id)
    context = {'results': tmp_g.serialize()}
    return mm_render_to_response(request, context, 'viewer.html')
