'''
Created on 12 Apr 2013

@author: mnagni
'''

from rdflib import Graph, URIRef, plugin
import httplib2
import urllib
from SPARQLWrapper.Wrapper import SPARQLWrapper, JSON, RDF
import json
import logging
from rdflib.plugins.stores.sparqlstore import SPARQLStore, SPARQLUpdateStore
from rdflib.store import Store
from django.conf import settings
from rdflib.namespace import Namespace
import uuid

LOGGING = logging.getLogger(__name__)

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

FORMAT_MAP = {'jsonld': 'application/ld+json',
              'xml': 'application/rdf+xml',
              'turtle': 'text/turtle'}

__store = SPARQLUpdateStore(queryEndpoint = getattr(settings, 'SPARQL_QUERY'),
                            update_endpoint = getattr(settings, 'SPARQL_UPDATE'), postAsEncoded=False)

__store.bind("charm", "http://charm.eu/ch#")
__store.bind("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
__store.bind("oa", "http://www.w3.org/ns/oa#")

# Create a namespace object for the CHARMe namespace.
CHARM = Namespace("http://charm.eu/ch#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
OA = Namespace("http://www.w3.org/ns/oa#")


#Has to be dumped?
__graphstore = SPARQLUpdateStore(queryEndpoint = getattr(settings, 'GRAPH_STORE_R'),
                                  update_endpoint = getattr(settings, 'GRAPH_STORE_RW'), postAsEncoded=False)
__graphstore.bind("charm", "http://charm.eu/ch#")

ANNO_SUBMITTED = 'submitted'
ANNO_INVALID = 'invalid'
ANNO_STABLE = 'stable'
ANNO_RETIRED = 'retired'

NODE_URI = 'nodeURI'
ANNO_URI = 'annoURI'
BODY_URI = 'bodyURI'


def get_store():
    return __store

def get_identifier(graph, baseurl = 'http://dummyhost'):
    '''
        Builds a named graph URIRef using, if exists, 
        a settings.SPARQL_QUERY parameter.
        
        * graph: String - the graph name
        * return String
    '''
    return'%s/%s' % (getattr(settings, 'SPARQL_DATA', baseurl), graph)


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
    if not store:
        store = get_store()
    tmp_g = Graph()
    #Necessary as RDFlib does not contain the json-ld lib
    if mimetype == 'application/ld+json':
        tmp_g.parse(data=data, format='json-ld')
    else:        
        tmp_g.parse(data = data, format = mimetype)
    _formatSubmittedAnnotation(tmp_g)
    for res in tmp_g:
        generate_graph(store, graph).add(res)
        
def _formatNodeURIRef(uriref, anno_uri, body_uri):
    '''
        Rewrite a URIRef according to the node configuration
        * uriref:rdflib.URIRef 
        * anno_uri:String as hexadecimal 
        * body_uri:String as hexadecimal
    ''' 
    if isinstance(uriref, URIRef) and NODE_URI in uriref:
        uriref = uriref.replace(uriref[:uriref.index('nodeURI')], getattr(settings, 'NODE_URI', 'http://localhost'))
        uriref = URIRef(uriref.replace(NODE_URI, '/data'))
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

#----------------------




__mem_store = plugin.get('IOMemory', Store)()

def serialize_to_RDF(data, mimetype):
    '''
    * data:String - the document to serialize
    * mimetype:String -  the data's mimetype
    * return:String - Returns an RDF serialization of the given data/mimetype document
    '''
    return _generate_graph(data, mimetype).serialize()

def _generate_graph(data, mimetype, store = __mem_store):
    '''
        Generate a new Graph
        * data:String - the document to serialize
        * mimetype:String -  the data's mimetype
        * return:rdflib.Graph - Returns an RDFlib graph containing the given data
    '''
    g = Graph(store=store)
    if mimetype == 'application/ld+json':
        g.parse(data=data, format='json-ld')
    else:         
        g.parse(data=data, format=mimetype)
    return g

def get_graphstore():
    return __graphstore



def get_memstore():
    return __mem_store
   
def search_annotations(store=get_memstore(), 
                      initNs={},
              initBindings={},
              queryGraph=None,
              DEBUG=False):
    return store.query(DESCRIBE_ANNOTATIONS, 
                       initNs=initNs,
                       initBindings=initBindings,
                       queryGraph=queryGraph,
                       DEBUG=DEBUG)

def search_annotation(anno_id, store=get_memstore(), 
                      initNs={},
              initBindings={},
              queryGraph=None,
              DEBUG=False):
    return store.query(DESCRIBE_ANNOTATION % anno_id, 
                       initNs=initNs,
                       initBindings=initBindings,
                       queryGraph=queryGraph,
                       DEBUG=DEBUG)
store=get_graphstore()
def remove_annotation(anno_id, query_endpoint, ):
    '''
        Removed a charme annotation from the triplestore
        * anno_id the charme annotation ID
    '''
    results = do_query(DESCRIBE_ANNOTATION % anno_id) 
    print results.serialize()
                
    sparql_wr = SPARQLUpdateStore(queryEndpoint = getattr(settings, 'SPARQL_QUERY'),
                                 update_endpoint = getattr(settings, 'GRAPHSTORE_UPDATE'), context_aware=False)
    for s, p, o in results:
        print s, p, o      
        sparql_wr.remove((s, p, o), None)

def do_query(query, endpoint = getattr(settings, 'SPARQL_QUERY'), graph='stable'):
    sparql_wr = get_graphstore()
    return sparql_wr.query(query, queryGraph=graph)

def get_by_known_namespace():
    g = Graph()
    #g.parse(location=http://dbpedia.org/resource/Elvis_Presley")
    g.parse(location="http://localhost:8080/openrdf-sesame/repositories/firstTest/rdf-graphs/service?default")
    for stmt in g.subject_predicates(URIRef("charm:anno")):
        print stmt

'''
def insert_rdf(data, mimetype, store=get_memstore()): 
    return generate_graph(data, mimetype, store = store)
'''



def delete_rdf(data, endpoint, graph=''):
    return _delete_rdf(endpoint, data, graph=None)

'''
def do_query(query):
    params = { 'query': query }    
    endpoint = SPARQL_QUERY % (urllib.urlencode(params))       
    return get_by_sparql(endpoint)
'''

def do_update(data, defaultGraph):
    return _do_query(data, defaultGraph)

def _do_query(query, mimetype = None, endpoint = None, defaultGraph = None):
    ret_format = None
    if mimetype == 'application/json':
        ret_format = JSON    
    if mimetype == 'application/rdf+xml':
        ret_format = RDF        
    
    results = __do_query(query, ret_format, defaultGraph)
    
    #Is an update
    if mimetype == None:
        return True

    if not results:
        return ""
        
    if hasattr(results, 'read') and results.headers.type == 'application/rdf+json':
        return json.load(results)
    
    if ret_format == RDF:
        res = results.read()
        return res
    return results

def __do_query(query, ret_format = None, defaultGraph = None):
    sparql = SPARQLWrapper(getattr(settings, 'SPARQL_QUERY'), updateEndpoint=getattr(settings, 'GRAPHSTORE_UPDATE'), defaultGraph=defaultGraph)
    sparql.setQuery(query)
    
    if ret_format:
        sparql.setReturnFormat(ret_format)
        return sparql.query().convert()
    else:
        return sparql.query()

    

def get_by_sparql(endpoint):
    """
        Executes a query
    """
    (response, content) = httplib2.Http().request(endpoint, 'GET')
    LOGGING.info("Getting: \n %s \n Response: %s" % (endpoint, response.status))
    return content

def create_graph(endpoint, graph, silent=False):
    action = "CREATE SILENT GRAPH %s" % graph
    return _insert_rdf(endpoint, action, content_type='text/turtle')

def _insert_rdf(endpoint, data, graph=None, content_type='application/rdf+xml'):
    """
        Inserts a turtle file
        * endpoint:String - the SPARQL GraphStore endpointURL
    """     
    (response, content) = httplib2.Http().request(_assemple_endpoint(endpoint, graph), 
                                                  method='PUT', 
                                                  body=data, 
                                                  headers={ 'content-type': content_type })
    LOGGING.info("Inserting: \n %s \n Response: %s" % (data, response.status))
    return response.status     

    
def _delete_rdf(endpoint, data, graph=None):
    """
        Inserts a turtle file
    """ 
    (response, content) = httplib2.Http().request(_assemple_endpoint(endpoint, graph), 
                                                  body=data, 
                                                  method='DELETE',
                                                  headers={ 'content-type': 'application/rdf+xml' })
    LOGGING.info("Deleting graph: \n %s \n Response: %s" % (endpoint, response.status))    

def _assemple_endpoint(endpoint, graph):
    if graph is None:
        return endpoint + "?default"
     
    params = { 'graph': graph }    
    return endpoint + "?" + urllib.urlencode(params)    