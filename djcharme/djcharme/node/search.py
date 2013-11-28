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
from rdflib.term import URIRef
from rdflib.namespace import RDF
from rdflib.plugins.stores import sparqlstore

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

def annotation_resource(anno_uri = None):
    anno_ref = None
    if anno_uri:
        anno_ref = URIRef(anno_uri)
    return (anno_ref, RDF.type, URIRef('http://www.w3.org/ns/oa#Annotation'))

def annotation_target(target_uri):
    return (None, URIRef('http://www.w3.org/ns/oa#hasTarget'), URIRef(target_uri))

def _populate_annotations(g, triples, depth=3):
    ret = []    
    for row in triples:
        tmp_g = Graph()
        for subj in _extractSubject(g, row[0], depth): 
            tmp_g.add(subj)
        ret.append(tmp_g)
    return ret

def search_title(title, graph=ANNO_STABLE, depth=3, limit = None):
    '''
        Returns annotations which refer to a given dcterm:title
        - string **title**
            the title to search
        - string **graph**
            the triplestore repository where to look into
        - integer **depth**
            how deep should the subject's properties be described            
    ''' 
    g = generate_graph(CharmeMiddleware.get_store(), graph)    
    g.LIMIT = limit
    triples = g.query(SEARCH_TITLE % (title))
    del g.LIMIT
    return _populate_annotations(g, triples, depth=3)

def search_annotationsByStatus(graph=ANNO_STABLE, depth=3, limit = None):
    '''
        Returns annotations which refer to a given dcterm:title
        - string **graph**
            the triplestore repository where to look into
        - integer **depth**
            how deep should the subject's properties be described            
    ''' 
    g = generate_graph(CharmeMiddleware.get_store(), graph)    
    g.LIMIT = limit
    triples = g.triples(annotation_resource())
    del g.LIMIT
    return _populate_annotations(g, triples, depth=3)

def search_annotationByTarget(predicate, graph=ANNO_STABLE, depth=3, limit = None):
    '''
        Returns annotations which have hasTarget the given predicate
        - string **predicate**
            the annotation predicate
        - string **graph**
            the triplestore repository where to look into
        - integer **depth**
            how deep should the subject's properties be described
    '''
    g = generate_graph(CharmeMiddleware.get_store(), graph)    
    g.LIMIT = limit
    triples = g.triples(annotation_target(predicate))
    del g.LIMIT
    return _populate_annotations(g, triples, depth=3)