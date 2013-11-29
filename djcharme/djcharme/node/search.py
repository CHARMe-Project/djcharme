'''
BSD Licence
Copyright (c) 2012, Science & Technology Facilities Council (STFC)
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice,
this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.
* Neither the name of the Science & Technology Facilities Council (STFC)
nor the names of its contributors may be used to endorse or promote
products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Created on 24 Sep 2013

@author: mnagni
'''
from djcharme.node.actions import generate_graph, ANNO_STABLE
from djcharme.node import _extractSubject
from rdflib.graph import Graph
from djcharme.charme_middleware import CharmeMiddleware
from rdflib.term import URIRef, Variable
from rdflib.namespace import RDF

SEARCH_TITLE = """
PREFIX text: <http://jena.apache.org/text#>
PREFIX dcterm:  <http://purl.org/dc/terms/>
PREFIX oa: <http://www.w3.org/ns/oa#>
PREFIX cito: <http://purl.org/spar/cito/>
SELECT Distinct ?anno 
WHERE {
    ?anno oa:hasBody ?cit .
    ?cit cito:hasCitedEntity ?paper .
    ?paper text:query (dcterm:title '%s' 10) .
}
"""

COUNT_TITLE = """
PREFIX text: <http://jena.apache.org/text#>
PREFIX dcterm:  <http://purl.org/dc/terms/>
PREFIX oa: <http://www.w3.org/ns/oa#>
PREFIX cito: <http://purl.org/spar/cito/>
SELECT Distinct count(?anno) 
WHERE {
    ?anno oa:hasBody ?cit .
    ?cit cito:hasCitedEntity ?paper .
    ?paper text:query (dcterm:title '%s' 10) .
}
"""

COUNT_TRIPLE = """
SELECT count(%s) 
WHERE {
    %s
}
"""

def annotation_resource(anno_uri = None):
    anno_ref = None
    if anno_uri:
        anno_ref = URIRef(anno_uri)
    return (anno_ref, RDF.type, URIRef('http://www.w3.org/ns/oa#Annotation'))

def sparqlize_triple(triple):
    template = '<%s>'
    s = Variable('s').n3()
    p = Variable('p').n3()
    o = Variable('o').n3()
    if triple[0] != None:
        s = template % str(triple[0]) 
    if triple[1] != None:
        p = template % str(triple[1])        
    if triple[2] != None:
        o = template % str(triple[2])
    return '%s %s %s' % (s, p, o)  
        

def annotation_target(target_uri):
    return (None, URIRef('http://www.w3.org/ns/oa#hasTarget'), URIRef(target_uri))

def _del_limit_offset(graph): 
    old_limit = None
    old_offset = None
    if hasattr(graph, 'LIMIT'):
        old_limit = getattr(graph, 'LIMIT')
        del graph.LIMIT
    if hasattr(graph, 'OFFSET'):
        old_offset = getattr(graph, 'OFFSET')
        del graph.OFFSET
    return (old_limit, old_offset)        

def _set_limit_offset(graph, limit_offset):
    if limit_offset[0] != None:
        graph.LIMIT = limit_offset[0] 
    if limit_offset[1] != None:
        graph.OFFSET = limit_offset[1]             

def _populate_annotations(g, triples, depth=3):
    ret = []    
    for row in triples:
        tmp_g = Graph()
        limit_offset = _del_limit_offset(g)          
        for subj in _extractSubject(g, row[0], depth): 
            tmp_g.add(subj)
        ret.append(tmp_g)
        _set_limit_offset(g, limit_offset)        
    return ret

def _do__open_search(query_attr, g, triples):
    depth  = int(query_attr.get('depth', 3))
    limit  = int(query_attr.get('count', 10)) 
    offset = (int(query_attr.get('startPage', 1)) - 1)* limit
    offset = offset + int(query_attr.get('startIndex', 1)) - 1
    g.LIMIT = limit
    g.OFFSET = offset
    ret = _populate_annotations(g, triples, depth)
    del g.LIMIT
    del g.OFFSET
    return ret


class SearchProxy(object):
    def __init__(self, query):
        _query = query        
        self.query_signature = None
        super(SearchProxy, self).__init__(self)

def search_title(title, query_attr):
    '''
        Returns annotations which refer to a given dcterm:title
        - string **title**
            the title to search
        - dict **query_attr**
            dictionary of paramenters            
    ''' 
    graph=str(query_attr.get('status', ANNO_STABLE))
    g = generate_graph(CharmeMiddleware.get_store(), graph)
    triples = g.query(SEARCH_TITLE % (title))    
    results = _do__open_search(query_attr, g, triples)
    enc_count = g.query(COUNT_TITLE % (title))
    count = str(enc_count.bindings[0].values()[0])
    if count == 'None':
        count = 0
    return results, int(count)   

def search_annotationsByStatus(query_attr):
    '''
        Returns annotations which refer to a given dcterm:title
        - dict **query_attr**
            dictionary of paramenters            
    ''' 
    graph=str(query_attr.get('status', ANNO_STABLE))
    g = generate_graph(CharmeMiddleware.get_store(), graph)
    triples = g.triples(annotation_resource())    
    results = _do__open_search(query_attr, g, triples)
    enc_count = g.query(COUNT_TRIPLE % ('?s', sparqlize_triple(annotation_resource())))    
    count = str(enc_count.bindings[0].values()[0])
    if count == 'None':
        count = 0
    return results, int(count)


def search_annotationByTarget(predicate, query_attr):
    '''
        Returns annotations which have hasTarget the given predicate
        - string **predicate**
            the annotation predicate
        - dict **query_attr**
            dictionary of paramenters
    '''
    graph=str(query_attr.get('status', ANNO_STABLE))
    g = generate_graph(CharmeMiddleware.get_store(), graph)
    look_for = annotation_target(predicate)
    triples = g.triples(look_for)
    results = _do__open_search(query_attr, g, triples)
    s = '?s'
    enc_count = g.query(COUNT_TRIPLE % ('?s', sparqlize_triple(look_for)))    
    count = str(enc_count.bindings[0].values()[0])
    if count == 'None':
        count = 0
    return results, int(count)  