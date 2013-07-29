'''
Created on 14 May 2013

@author: mnagni
'''
from djcharme.node.actions import do_query, _do_query, DESCRIBE_ANNOTATIONS,\
    DESCRIBE_ANNOTATION, CONSTRUCT_ANNOTATION, get_store, search_annotations,\
    CHARM, OA, RDF, get_identifier, FORMAT_MAP
    
from django.http.response import HttpResponseRedirectBase, Http404, HttpResponse
from djcharme import mm_render_to_response

import logging
from rdflib.graph import Graph
from rdflib.term import URIRef, BNode
import rdflib
from djcharme.exception import SerializeError

LOGGING = logging.getLogger(__name__)

class HttpResponseSeeOther(HttpResponseRedirectBase):
    status_code = 303

def __serialize(graph, format = 'application/rdf+xml'):
    '''
        Serializes a graph according to the required format                 
    '''         
    if format == 'application/ld+json':
        format = 'json-ld'
    return graph.serialize(format='json-ld')

def index(request, graph):
    '''
        Returns a tabular view of the stored annotations.
        *request: HTTPRequest - the client request
        *graph: String -  the required named graph
        TDB - In a future implemenation this actions should be supported by an OpenSearch implementation
    '''     
    g = Graph(store=get_store(), identifier=get_identifier(graph))

    tmp_g = Graph()             
    for res in g.triples((None, None, CHARM['anno'])):
        tmp_g.add(res)
    for res in g.triples((None, OA['hasTarget'], None)):
        tmp_g.add(res)        
    for res in g.triples((None, OA['hasBody'], None)):
        tmp_g.add(res)
                
    req_format = FORMAT_MAP.get(request.GET.get('format', None))
    
    if req_format:
        if req_format not in FORMAT_MAP.values():
            raise SerializeError("Cannot generate the required format %s " % req_format)
        return HttpResponse(__serialize(tmp_g, format = req_format))
            
    LOGGING.debug("Annotations %s" % tmp_g.serialize())      
    context = {'results': tmp_g.serialize()}
    return mm_render_to_response(request, context, 'viewer.html')   
#------------------------------------------



def accept_request(request, mime, format={}):
    '''
        Verifies if the a given mime-type is into the http request "accept" 
    '''
    if not request.META.get('HTTP_ACCEPT', None):
        return False
    acc = format
    if not acc:
        acc = [a.split(';')[0] for a in request.META['HTTP_ACCEPT'].split(',')]
    return mime in acc



def process_data(request, item):
    mainmime = 'application/rdf+xml' 
    #if not accept_request(request, mainmime):
    #    return process_resource(request, item)
    GET_DATA = CONSTRUCT_ANNOTATION % (item, item)
    LOGGING.info("Requesting %s" % GET_DATA)
    results = _do_query(GET_DATA, mainmime)   
    return HttpResponse(results, 
                            mimetype = mainmime)        
    
def process_page(request, item = None):
    mainmime = 'text/html'
    if not accept_request(request, mainmime):
        return process_resource(request, item)
    results = None
    g = Graph(store=get_store(), identifier='stable')
    if item == None:
        results = search_annotations(store=get_store(), queryGraph=g)
    else:
        results = do_query(DESCRIBE_ANNOTATION % item).serialize()            
    
    ret = results.graph.serialize()
    context = {'results': ret}
    return mm_render_to_response(request, context, 'viewer.html')

#def process_page(request, item = None):
#    return _process_page(request, item)

def process_resource(request, item=None): 
    if accept_request(request, 'application/rdf+xml'):        
        LOGGING.info("Redirecting to /data/%s" % item)
        return HttpResponseSeeOther('/data/%s' % item)
    if accept_request(request, 'text/html'):
        LOGGING.info("Redirecting to /page/%s" % item)
        return HttpResponseSeeOther('/page/%s' % item)
    return Http404()