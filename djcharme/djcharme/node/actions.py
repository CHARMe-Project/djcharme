'''
BSD Licence
Copyright (c) 2014, Science & Technology Facilities Council (STFC)
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice,
        this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
        this list of conditions and the following disclaimer in the
        documentation and/or other materials provided with the distribution.
    * Neither the name of the Science & Technology Facilities Council (STFC)
        nor the names of its contributors may be used to endorse or promote
        products derived from this software without specific prior written
        permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Created on 12 Apr 2013

@author: mnagni
'''
import logging
from urllib2 import URLError
import uuid

from django.conf import settings
from rdflib import Graph, URIRef
from rdflib.graph import ConjunctiveGraph
from rdflib.namespace import Namespace

from djcharme.charme_middleware import CharmeMiddleware
from djcharme.exception import ParseError
from djcharme.exception import StoreConnectionError
from djcharme.node import _extract_subject


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
FORMAT_MAP = {'json-ld': 'application/ld+json',
              'xml': 'application/rdf+xml',
              'rdf': 'application/rdf+xml',
              'turtle': 'text/turtle',
              'ttl': 'text/turtle'}

def rdf_format_from_mime(mimetype):
    for key, value in FORMAT_MAP.iteritems():
        if mimetype == value:
            return key

CH_NS = "http://charm.eu/ch#"
# Create a namespace object for the CHARMe namespace.
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
OA = Namespace("http://www.w3.org/ns/oa#")
CH = Namespace(CH_NS)

ANNO_SUBMITTED = 'submitted'
ANNO_INVALID = 'invalid'
ANNO_STABLE = 'stable'
ANNO_RETIRED = 'retired'

NODE_URI = 'http://localhost/'
ANNO_URI = 'annoID'
BODY_URI = 'bodyID'
CH_NODE = 'chnode'

RESOURCE = 'resource'
DATA = 'data'
PAGE = 'page'


def format_graph_iri(graph, baseurl='http://dummyhost'):
    '''
        Builds a named graph URIRef using, if exists,
        a settings.SPARQL_QUERY parameter.

        - string **graph**
            the graph name
        * return String
    '''
    if 'http://' in graph:
        return graph

    return '%s/%s' % (getattr(settings, 'SPARQL_DATA', baseurl), graph)


def generate_graph(store, graph):
    '''
        Generate a new Graph
        - string **graph**
            the graph name
        * return:rdflib.Graph - Returns an RDFlib graph containing the given
                                data
    '''
    return Graph(store=store, identifier=format_graph_iri(graph))


def insert_rdf(data, mimetype, graph=None, store=None):
    '''
        Inserts an RDF/json-ld document into the triplestore
        - string **data**
            a document
        - string **mimetype**
            the document mimetype
        - string **graph**
            the graph name
        - rdflib.Store **store**
            if none use the return of get_store()
    '''
    if store is None:
        store = CharmeMiddleware.get_store()
    tmp_g = Graph()
    # Necessary as RDFlib does not contain the json-ld lib
    try:
        tmp_g.parse(data=data, format=mimetype)
    except SyntaxError as ex:
        try:
            raise ParseError(str(ex))
        except UnicodeDecodeError:
            raise ParseError(ex.__dict__["_why"])

    _format_submitted_annotation(tmp_g)
    final_g = generate_graph(store, graph)

    for nspace in tmp_g.namespaces():
        final_g.store.bind(str(nspace[0]), nspace[1])

    for res in tmp_g:
        final_g.add(res)

    return final_g


def _format_resource_uri_ref(resource_id):
    '''
        Returns the URIRef associated with the id for this specific node
    '''
    if resource_id.startswith('http:'):
        return URIRef(resource_id)
    return URIRef('%s/%s/%s' % (getattr(settings, 'NODE_URI', NODE_URI),
                                RESOURCE,
                                resource_id))


def _format_node_uri_ref(uriref, anno_uri, body_uri):
    '''
        Rewrite a URIRef according to the node configuration
        * uriref:rdflib.URIRef
        * anno_uri:String as hexadecimal
        * body_uri:String as hexadecimal
    '''
    if isinstance(uriref, URIRef) and NODE_URI in uriref:
        uriref = URIRef(uriref.replace(NODE_URI,
                                       getattr(settings, 'NODE_URI', NODE_URI)
                                       + '/'))

    if isinstance(uriref, URIRef) and CH_NODE in uriref:
        uriref = URIRef(uriref.replace(CH_NODE + ':',
                                       getattr(settings, 'NODE_URI', NODE_URI)
                                       + '/'))
    if isinstance(uriref, URIRef) and ANNO_URI in uriref:
        uriref = URIRef(uriref.replace(ANNO_URI, "%s/%s" %
                                       (RESOURCE, anno_uri)))
    if isinstance(uriref, URIRef) and BODY_URI in uriref:
        uriref = URIRef(uriref.replace(BODY_URI, "%s/%s" %
                                       (RESOURCE, body_uri)))
    return uriref


def _format_submitted_annotation(graph):
    '''
        Formats the graph according to the node configuration
    '''
    anno_uri = uuid.uuid4().hex
    body_uri = uuid.uuid4().hex

    for subject, pred, obj in graph:
        graph.remove((subject, pred, obj))
        subject = _format_node_uri_ref(subject, anno_uri, body_uri)
        pred = _format_node_uri_ref(pred, anno_uri, body_uri)
        obj = _format_node_uri_ref(obj, anno_uri, body_uri)
        graph.add((subject, pred, obj))


def change_annotation_state(resource_id, new_graph):
    '''
        Advance the status of an annotation
        - string **resource_id**
            the resource URL
        - string **new_graph**
            the name of the state where more the annotation
    '''
    old_graph = find_annotation_graph(resource_id)
    old_g = generate_graph(CharmeMiddleware.get_store(), old_graph)
    new_g = generate_graph(CharmeMiddleware.get_store(), new_graph)
    for res in old_g.triples((_format_resource_uri_ref(resource_id), None,
                              None)):
        old_g.remove(res)
        new_g.add(res)
    return new_g


def find_annotation_graph(resource_id):
    triple = (_format_resource_uri_ref(resource_id), None, None)
    for graph in [ANNO_SUBMITTED, ANNO_STABLE, ANNO_RETIRED, ANNO_INVALID]:
        new_g = generate_graph(CharmeMiddleware.get_store(), graph)
        if triple in new_g:
            return graph


def find_resource_by_id(resource_id, depth=None):
    '''
        Returns the charme resource associated with the given resource_id
        * resource_id:String
        * return: an rdflib.Graph object
    '''
    graph = ConjunctiveGraph(store=CharmeMiddleware.get_store())
    uri_ref = _format_resource_uri_ref(resource_id)
    LOGGING.debug("Looking resource %s", str(uri_ref))
    return _extract_subject(graph, uri_ref, depth)


# This code is a workaround until FUSEKI fixes this bug
# https://issues.apache.org/jira/browse/JENA-592
def __query_annotations(graph, default_graph, pred=None, obj=None):
    query = ''
    if obj:
        query = '''
            SELECT ?subject ?pred ?obj WHERE { GRAPH <%s> {?subject ?pred <%s> }}
        ''' % (default_graph, obj)
    if pred:
        query = '''
            SELECT ?subject ?pred ?obj WHERE { GRAPH <%s> {?subject <%s> ?obj }}
        ''' % (default_graph, pred)
    return graph.query(query)


def _collect_annotations(graph_name):
    '''
        Returns a graph containing all the node annotations
        - string **graph_name**
            the graph name
    '''
    graph = generate_graph(CharmeMiddleware.get_store(), graph_name)
    tmp_g = Graph()

    anno = graph.triples((None, None, OA['Annotation']))
    target = graph.triples((None, OA['hasTarget'], None))
    body = graph.triples((None, OA['hasBody'], None))

    try:
        for res in anno:
            tmp_g.add(res)
        for res in target:
            tmp_g.add(res)
        for res in body:
            tmp_g.add(res)
    except URLError as ex:
        raise StoreConnectionError("Cannot open a connection with triple store"
                                   " \n" + str(ex))

    return tmp_g
