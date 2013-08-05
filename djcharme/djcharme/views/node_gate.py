'''
Created on 14 May 2013

@author: mnagni
'''
from djcharme.node.actions import CHARM, OA, get_identifier, FORMAT_MAP, \
    ANNO_SUBMITTED, insert_rdf, find_resource_by_id, RESOURCE
    
from django.http.response import HttpResponseRedirectBase, Http404, HttpResponse
from djcharme import mm_render_to_response

import logging
from rdflib.graph import Graph
from djcharme.exception import SerializeError
from djcharme.charme_middleware import CharmeMiddleware
from djcharme.views import isGET, isPOST

LOGGING = logging.getLogger(__name__)

class HttpResponseSeeOther(HttpResponseRedirectBase):
    status_code = 303

def __serialize(graph, req_format = 'application/rdf+xml'):
    '''
        Serializes a graph according to the required format                 
    '''         
    if req_format == 'application/ld+json':
        req_format = 'json-ld'
    return graph.serialize(format=req_format)

def _validateMimeFormat(request):
    req_format = request.META.get('HTTP_ACCEPT', None)
    if req_format:
        for k,v in FORMAT_MAP.iteritems():
            if req_format == v:
                return k
    return None

def _validateFormat(request):
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
            raise SerializeError("Cannot generate the required format %s " % req_format)
    return req_format

def index(request, graph = 'stable'):
    '''
        Returns a tabular view of the stored annotations.
        *request: HTTPRequest - the client request
        *graph: String -  the required named graph
        TDB - In a future implemenation this actions should be supported by an OpenSearch implementation
    '''     
    g = Graph(store=CharmeMiddleware.get_store(), identifier=get_identifier(graph))

    tmp_g = Graph()             
    for res in g.triples((None, None, CHARM['anno'])):
        tmp_g.add(res)
    for res in g.triples((None, OA['hasTarget'], None)):
        tmp_g.add(res)        
    for res in g.triples((None, OA['hasBody'], None)):
        tmp_g.add(res)
                
    req_format = _validateFormat(request)
    
    if req_format:
        LOGGING.debug("Annotations %s" % __serialize(tmp_g, req_format = req_format))
        return HttpResponse(__serialize(tmp_g, req_format = req_format))
            
    LOGGING.debug("Annotations %s" % tmp_g.serialize())          
    context = {'results': tmp_g.serialize()}
    return mm_render_to_response(request, context, 'viewer.html')


def insert(request):
    '''
        Inserts in the triplestore a new annotation under the "ANNO_SUBMITTED" graph
    '''
    req_format = _validateFormat(request)
    
    if request.method == 'POST':
        triples = request.body
        tmp_g = insert_rdf(triples, req_format, graph=ANNO_SUBMITTED) 
        return HttpResponse(__serialize(tmp_g, req_format = req_format))
        
        
def process_resource(request, resource_id):  
    if _validateMimeFormat(request):           
        LOGGING.info("Redirecting to /%s/%s" % (RESOURCE, resource_id))
        return HttpResponseSeeOther('/%s/%s' % (RESOURCE, resource_id))
    if 'text/html' in request.META.get('HTTP_ACCEPT', None):
        LOGGING.info("Redirecting to /page/%s" % resource_id)
        return HttpResponseSeeOther('/page/%s' % resource_id)
    return Http404()
        
def process_data(request, resource_id):
    req_format = _validateMimeFormat(request)
    if req_format is None:
        return process_resource(request, resource_id)
            
    tmp_g = find_resource_by_id(resource_id)           
    return HttpResponse(tmp_g.serialize(format = req_format), 
                            mimetype = request.META.get('HTTP_ACCEPT'))  

def process_page(request, resource_id = None):
    if 'text/html' not in request.META.get('HTTP_ACCEPT', None):
        process_resource(request, resource_id)
        
    tmp_g = find_resource_by_id(resource_id)                 
    context = {'results': tmp_g.serialize()}
    return mm_render_to_response(request, context, 'viewer.html')
