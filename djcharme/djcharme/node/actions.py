'''
Created on 12 Apr 2013

@author: mnagni
'''

from rdflib import Graph, URIRef
import logging
from django.conf import settings
from rdflib.namespace import Namespace
import uuid
from djcharme.charme_middleware import CharmeMiddleware
from rdflib.graph import ConjunctiveGraph

LOGGING = logging.getLogger(__name__)
'''
SELECT_ANNOTATION = """
    PREFIX an: <http://charm.eu/data/anno/> 
    SELECT ?s ?p ?o
    WHERE {
        an:%s ?p ?o 
    }
"""

SELECT_ANNOTATIONS = """
PREFIX charm: <http://charm.eu/ch#>
SELECT * WHERE {
    ?s a charm:anno .
    ?s ?p ?o 
}
"""

DESCRIBE_ANNOTATIONS = """
PREFIX charm: <http://charm.eu/ch#>
DESCRIBE ?s
WHERE {
  ?s a charm:anno .
}
"""

DESCRIBE_ANNOTATION = """
    PREFIX an: <http://charm.eu/data/anno/> 
    DESCRIBE an:%s 
"""

CONSTRUCT_ANNOTATION = """
PREFIX an: <http://charm.eu/data/anno/>
prefix oa: <http://www.w3.org/ns/oa#>
prefix charm: <http://charm.eu/ch#> 

CONSTRUCT { an:%s ?p ?o .}

WHERE {
 an:%s ?p ?o .
}
"""
'''
FORMAT_MAP = {'jsonld': 'application/ld+json',
              'xml': 'application/rdf+xml',
              'turtle': 'text/turtle'}



# Create a namespace object for the CHARMe namespace.
CHARM = Namespace("http://charm.eu/ch#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
OA = Namespace("http://www.w3.org/ns/oa#")

ANNO_SUBMITTED = 'submitted'
ANNO_INVALID = 'invalid'
ANNO_STABLE = 'stable'
ANNO_RETIRED = 'retired'

NODE_URI = 'http://localhost/'
ANNO_URI = 'annoID'
BODY_URI = 'bodyID'
CH_NODE = 'chnode'

RESOURCE = 'resource'

LOGGING = logging.getLogger(__name__)

def get_identifier(graph, baseurl = 'http://dummyhost'):
    '''
        Builds a named graph URIRef using, if exists, 
        a settings.SPARQL_QUERY parameter.
        
        * graph: String - the graph name
        * return String
    '''
    return '%s/%s' % (getattr(settings, 'SPARQL_DATA', baseurl), graph)


def generate_graph(store, graph):
    '''
        Generate a new Graph
        * data:String - the document to serialize
        * mimetype:String -  the data's mimetype
        * return:rdflib.Graph - Returns an RDFlib graph containing the given data
    '''
    return Graph(store=store, identifier = get_identifier(graph))

def insert_rdf(data, mimetype, graph = None, store=None):
    '''
        Inserts an RDF/json-ld document into the triplestore
        * data:string a document
        * mimetype:string the document type
        * graph:string the named graph
        * store:rdflib.Store if none use the return of get_store()        
    '''
    if store is None:
        store = CharmeMiddleware.get_store()
    tmp_g = Graph()
    #Necessary as RDFlib does not contain the json-ld lib
    if mimetype == 'application/ld+json':
        tmp_g.parse(data=data, format='json-ld')
    else:        
        tmp_g.parse(data = data, format = mimetype)
    _formatSubmittedAnnotation(tmp_g)
    final_g = generate_graph(store, graph)
    
    for ns in tmp_g.namespaces():
        final_g.store.bind(str(ns[0]), ns[1])
     
    for res in tmp_g:
        final_g.add(res)
        
    return final_g

def _formatResourceURIRef(resource_id):
    '''
        Returns the URIRef associated with the id for this specific node
    '''
    return URIRef('%s%s/%s' % (getattr(settings, 'NODE_URI', NODE_URI), 
                                RESOURCE,
                                resource_id))
        
def _formatNodeURIRef(uriref, anno_uri, body_uri):
    '''
        Rewrite a URIRef according to the node configuration
        * uriref:rdflib.URIRef 
        * anno_uri:String as hexadecimal 
        * body_uri:String as hexadecimal
    ''' 
    if isinstance(uriref, URIRef) and NODE_URI in uriref:
        uriref = URIRef(uriref.replace(NODE_URI,
                               getattr(settings,
                                       'NODE_URI', 
                                       NODE_URI)))

    if isinstance(uriref, URIRef) and CH_NODE in uriref:
        uriref = URIRef(uriref.replace(CH_NODE + ':', 
                                       getattr(settings, 'NODE_URI', NODE_URI)))        
    if isinstance(uriref, URIRef) and ANNO_URI in uriref:
        uriref = URIRef(uriref.replace(ANNO_URI, anno_uri))
    if isinstance(uriref, URIRef) and BODY_URI in uriref:
        uriref = URIRef(uriref.replace(BODY_URI, body_uri))    
    return uriref

def _formatSubmittedAnnotation(graph):
    '''
        Formats the graph according to the node configuration
    '''
    anno_uri = uuid.uuid4().hex
    body_uri = uuid.uuid4().hex
    
    for s,p,o in graph:
            graph.remove((s, p, o))
            s =_formatNodeURIRef(s, anno_uri, body_uri)
            p = _formatNodeURIRef(p, anno_uri, body_uri)
            o = _formatNodeURIRef(o, anno_uri, body_uri)
            graph.add((s, p, o))

def find_resource_by_id(resource_id):
    '''
        Returns the charme resource associated with the given resource_id
        * resource_id:String
        * return: an rdflib.Graph object
    '''
    g = ConjunctiveGraph(store=CharmeMiddleware.get_store())
    tmp_g = Graph()
    for res in g.triples((_formatResourceURIRef(resource_id), None, None)):
        tmp_g.add(res) 
    return tmp_g
#----------------------