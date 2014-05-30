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

Created on 24 Sep 2013

@author: mnagni
'''
import logging

from rdflib.graph import Graph
from rdflib.namespace import RDF
from rdflib.term import URIRef

from djcharme.charme_middleware import CharmeMiddleware
from djcharme.node import _extract_subject
from djcharme.node.actions import generate_graph, ANNO_STABLE


LOGGING = logging.getLogger(__name__)

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
ORDER BY ?anno
LIMIT %s
%s
"""

SEARCH_TITLE_COUNT = """
PREFIX text: <http://jena.apache.org/text#>
PREFIX dcterm:  <http://purl.org/dc/terms/>
PREFIX oa: <http://www.w3.org/ns/oa#>
PREFIX cito: <http://purl.org/spar/cito/>
SELECT count(DISTINCT ?anno)
WHERE {
    ?anno oa:hasBody ?cit .
    ?cit cito:hasCitedEntity ?paper .
    ?paper text:query (dcterm:title '%s' 10) .
}
"""

SEARCH_TARGET = """
PREFIX oa: <http://www.w3.org/ns/oa#>
SELECT Distinct ?anno
WHERE {
    ?anno oa:hasTarget <%s> .
}
ORDER BY ?anno
LIMIT %s
%s
"""

SEARCH_TARGET_COUNT = """
PREFIX oa: <http://www.w3.org/ns/oa#>
SELECT count(DISTINCT ?anno)
WHERE {
    ?anno oa:hasTarget <%s> .
}
"""

# TODO
SEARCH_DOMAIN = """
PREFIX oa: <http://www.w3.org/ns/oa#>
SELECT Distinct ?anno
WHERE {
    ?anno oa:domainOfInterest <%s> .
}
ORDER BY ?anno
LIMIT %s
%s
"""

# TODO
SEARCH_DOMAIN_COUNT = """
PREFIX oa: <http://www.w3.org/ns/oa#>
SELECT count(DISTINCT ?anno)
WHERE {
    ?anno oa:domainOfInterest <%s> .
}
"""

SEARCH_DATA_TYPE = """
PREFIX oa: <http://www.w3.org/ns/oa#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT Distinct ?anno
WHERE {
    ?anno oa:hasTarget ?target .
    ?target rdf:type <%s> .
}
ORDER BY ?anno
LIMIT %s
%s
"""

SEARCH_DATA_TYPE_COUNT = """
PREFIX oa: <http://www.w3.org/ns/oa#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT count(DISTINCT ?anno)
WHERE {
    ?anno oa:hasTarget ?target .
    ?target rdf:type <%s> .
}
"""

SEARCH_MOTIVATION = """
PREFIX oa: <http://www.w3.org/ns/oa#>
SELECT Distinct ?anno
WHERE {
    ?anno oa:motivatedBy <%s> .
}
ORDER BY ?anno
LIMIT %s
%s
"""

SEARCH_MOTIVATION_COUNT = """
PREFIX oa: <http://www.w3.org/ns/oa#>
SELECT count(DISTINCT ?anno)
WHERE {
    ?anno oa:motivatedBy <%s> .
}
"""

SEARCH_ORGANIZATION = """
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX oa: <http://www.w3.org/ns/oa#>
SELECT Distinct ?anno
WHERE {
    ?anno oa:serializedBy ?agent .
    ?agent foaf:Organization <%s> .
}
ORDER BY ?anno
LIMIT %s
%s
"""

SEARCH_ORGANIZATION_COUNT = """
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX oa: <http://www.w3.org/ns/oa#>
SELECT count(DISTINCT ?anno)
WHERE {
    ?anno oa:serializedBy ?agent .
    ?agent foaf:Organization <%s> .
}
"""

SEARCH_STATUS = """
PREFIX oa: <http://www.w3.org/ns/oa#>
SELECT Distinct ?anno
WHERE {
    ?anno oa:hasTarget ?o .
}
ORDER BY ?anno
LIMIT %s
%s
"""

SEARCH_STATUS_COUNT = """
PREFIX oa: <http://www.w3.org/ns/oa#>
SELECT count(DISTINCT ?anno)
WHERE {
    ?anno oa:hasTarget ?o .
}
"""

def annotation_resource(anno_uri=None):
    """
    Get an annotation subject, predicate, object using the anno_uri as the
    subject.

    Args:
        anno_uri (str): The annotation uri.

    Returns:
        str, str, str. Subject, predicate, object. If anno_uri is None then the
        returned subject will be None.

    """
    anno_ref = None
    if anno_uri:
        anno_ref = URIRef(anno_uri)
    return (anno_ref, RDF.type, URIRef('http://www.w3.org/ns/oa#Annotation'))


def _populate_annotations(graph, triples, depth=3):
    ret = []
    for row in triples:
        tmp_g = Graph()
        for subj in _extract_subject(graph, row[0], depth):
            tmp_g.add(subj)
        ret.append(tmp_g)
    return ret


def _get_count(triples):
    """
    Retrieve the value of a count query from a list of triples.

    Args:
        triples ([triple]): The results from a SELECT count(?) query

    Returns:
        an int of the count
    """
    for triple in triples:
        return int(triple[0])


def _get_limit(query_attr):
    """
    Get the limit for the number of results to return.

    Args:
        query_attr (dict): The query parameters from the users request.

    """
    limit = int(query_attr.get('count'))
    return limit


def _get_offset(query_attr):
    """
    Get the off set of results to return.

    Args:
        query_attr (dict): The query parameters from the users request.

    """
    limit = _get_limit(query_attr)
    LOGGING.debug("Using limit: %s", str(limit))
    offset = (int(query_attr.get('startPage', 1)) - 1) * limit
    offset = offset + int(query_attr.get('startIndex', 1)) - 1
    if offset > 0:
        LOGGING.debug("Using offset: %s", str(offset))
        return "OFFSET " + offset
    else:
        return ""


def _get_graph(query_attr):
    """
    Get the graph based on the value of the attribute 'status'.

    If the users has not set a value for 'status' the use the ANNO_STABLE graph

    Args:
        query_attr (dict): The query parameters from the users request.
    """
    graph_name = str(query_attr.get('status', ANNO_STABLE))
    return generate_graph(CharmeMiddleware.get_store(), graph_name)


def _do__open_search(query_attr, graph, triples):
    depth = int(query_attr.get('depth', 3))
    ret = _populate_annotations(graph, triples, depth)
    return ret


class SearchProxy(object):
    def __init__(self, query):
        _query = query
        self.query_signature = None
        super(SearchProxy, self).__init__(self)


def search_title(title, query_attr):
    """
    Get the annotations which refer to the given dcterm:title.

    Args:
        title (str): The title to search for.
        query_attr (dict): The query parameters from the users request.

    Returns:
        list of triples. The result of the search.

    """
    LOGGING.debug("search_title(%s, query_attr)", str(title))
    graph = _get_graph(query_attr)
    triples = graph.query(SEARCH_TITLE % (title, _get_limit(query_attr),
                                          _get_offset(query_attr)))
    results = _do__open_search(query_attr, graph, triples)
    total_results = _get_count(graph.query(SEARCH_TITLE_COUNT % (title)))
    LOGGING.debug("search_title returning %s triples out of %s",
                  str(len(results)), str(total_results))
    return results, total_results


def search_annotations_by_status(query_attr):
    """
    Get all the annotations with the given status.

    Args:
        query_attr (dict): The query parameters from the users request.

    Returns:
        list of triples. The result of the search.

    """
    LOGGING.debug("search_annotations_by_status(query_attr)")
    graph = _get_graph(query_attr)
    triples = graph.query(SEARCH_STATUS % (_get_limit(query_attr),
                                           _get_offset(query_attr)))
    results = _do__open_search(query_attr, graph, triples)
    total_results = _get_count(graph.query(SEARCH_STATUS_COUNT))
    LOGGING.debug("search_annotations_by_status returning %s triples out of %s",
                  str(len(results)), str(total_results))
    return results, total_results


def search_annotations_by_target(target_uri, query_attr):
    """
    Get the annotations which refer to the given target.

    Args:
        target_uri (str): The target uri to search for.
        query_attr (dict): The query parameters from the users request.

    Returns:
        list of triples. The result of the search.

    """
    LOGGING.debug("search_annotations_by_target(%s, query_attr)",
                  str(target_uri))
    graph = _get_graph(query_attr)
    triples = graph.query(SEARCH_TARGET % (URIRef(target_uri),
                                           _get_limit(query_attr),
                                           _get_offset(query_attr)))
    results = _do__open_search(query_attr, graph, triples)
    total_results = _get_count(graph.query(SEARCH_TARGET_COUNT %
                                           (URIRef(target_uri))))
    LOGGING.debug("search_annotations_by_target returning %s triples out of %s",
                  str(len(results)), str(total_results))
    return results, total_results


def search_by_domain(domain_of_interest, query_attr):
    """
    Get the annotations which refer to the given domain of interest.

    Args:
        domain_of_interest (str): The domain of interest to search for.
        query_attr (dict): The query parameters from the users request.

    Returns:
        list of triples. The result of the search.

    """
    LOGGING.debug("search_by_domain(%s, query_attr)",
                  str(domain_of_interest))
    graph = _get_graph(query_attr)
    triples = graph.query(SEARCH_DOMAIN % (URIRef(domain_of_interest),
                                           _get_limit(query_attr),
                                           _get_offset(query_attr)))
    results = _do__open_search(query_attr, graph, triples)
    total_results = _get_count(graph.query(SEARCH_DOMAIN_COUNT %
                                           (URIRef(domain_of_interest))))
    LOGGING.debug("search_by_domain returning %s triples out of %s",
                  str(len(results)), str(total_results))
    return results, total_results


def search_by_motivation(motivation, query_attr):
    """
    Get the annotations which have the given motivation.

    Args:
        motivation (str): The motivation for the annotation.
        query_attr (dict): The query parameters from the users request.

    Returns:
        list of triples. The result of the search.

    """
    LOGGING.debug("search_by_motivation(%s, query_attr)",
                  str(motivation))
    graph = _get_graph(query_attr)
    triples = graph.query(SEARCH_MOTIVATION % (URIRef(motivation),
                                           _get_limit(query_attr),
                                           _get_offset(query_attr)))
    results = _do__open_search(query_attr, graph, triples)
    total_results = _get_count(graph.query(SEARCH_MOTIVATION_COUNT %
                                           (URIRef(motivation))))
    LOGGING.debug("search_by_motivation returning %s triples out " \
                  "of %s", str(len(results)), str(total_results))
    return results, total_results


def search_by_organization(organization, query_attr):
    """
    Get the annotations which were annotated from the given organization.

    Args:
        organization (str): The organization that the annotation were made from.
        query_attr (dict): The query parameters from the users request.

    Returns:
        list of triples. The result of the search.

    """
    LOGGING.debug("search_by_organization(%s, query_attr)",
                  str(organization))
    graph = _get_graph(query_attr)
    triples = graph.query(SEARCH_ORGANIZATION % (URIRef(organization),
                                           _get_limit(query_attr),
                                           _get_offset(query_attr)))
    results = _do__open_search(query_attr, graph, triples)
    total_results = _get_count(graph.query(SEARCH_ORGANIZATION_COUNT %
                                           (URIRef(organization))))
    LOGGING.debug("search_by_organization returning %s triples " \
                  "out of %s", str(len(results)), str(total_results))
    return results, total_results


def search_targets_by_data_type(target_type, query_attr):
    """
    Get the annotations which refer to the given target type.

    Args:
        target_type (str): The target type to search for.
        query_attr (dict): The query parameters from the users request.

    Returns:
        list of triples. The result of the search.

    """
    LOGGING.debug("search_targets_by_data_type(%s, query_attr)",
                  str(target_type))
    graph = _get_graph(query_attr)
    triples = graph.query(SEARCH_DATA_TYPE % (URIRef(target_type),
                                              _get_limit(query_attr),
                                              _get_offset(query_attr)))
    results = _do__open_search(query_attr, graph, triples)
    total_results = _get_count(graph.query(SEARCH_DATA_TYPE_COUNT %
                                           (URIRef(target_type))))
    LOGGING.debug("search_targets_by_data_type returning %s triples out of %s",
                  str(len(results)), str(total_results))
    return results, total_results
