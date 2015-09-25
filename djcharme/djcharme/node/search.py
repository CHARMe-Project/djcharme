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
import re
import string
from urlparse import urlparse

from rdflib.graph import Graph
from rdflib.namespace import RDF
from rdflib.term import Literal
from rdflib.term import URIRef

from djcharme.charme_middleware import CharmeMiddleware
from djcharme.node.triple_queries import extract_subject
from djcharme.node.actions import generate_graph
from djcharme.node.constants import STABLE


LOGGING = logging.getLogger(__name__)

PREFIX = """
PREFIX text: <http://jena.apache.org/text#>
PREFIX dcterm:  <http://purl.org/dc/terms/>
PREFIX oa: <http://www.w3.org/ns/oa#>
PREFIX cito: <http://purl.org/spar/cito/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX cnt: <http://www.w3.org/2011/content#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>"""

ANNOTATIONS_SELECT = """
SELECT Distinct ?anno ?annotatedAt"""

ANNOTATIONS_SELECT_COUNT = """
SELECT count(DISTINCT ?anno)"""

ANNOTATIONS_ORDER = """
ORDER BY DESC(?annotatedAt)"""

ANNOTATIONS_FOR_BODY_TYPE = """
?anno oa:annotatedAt ?annotatedAt .
?anno oa:hasBody ?body .
?body rdf:type ?bodyType ."""

ANNOTATIONS_FOR_CITING_TYPE = """
?anno oa:annotatedAt ?annotatedAt .
?anno cito:hasCitingEntity ?citingEntity .
?citingEntity rdf:type ?citingType ."""

ANNOTATIONS_FOR_COMMENT = """
?body text:query (cnt:chars '%s' 100) .
?anno oa:hasBody ?body ;
      oa:annotatedAt ?annotatedAt ."""

ANNOTATIONS_FOR_CREATOR_FAMILY_NAME = """
?anno oa:annotatedAt ?annotatedAt .
?anno oa:annotatedBy ?person .
?person foaf:familyName ?creatorFamilyName"""

ANNOTATIONS_FOR_CREATOR_GIVEN_NAME = """
?anno oa:annotatedAt ?annotatedAt .
?anno oa:annotatedBy ?person .
?person foaf:givenName ?creatorGivenName"""
      
ANNOTATIONS_FOR_DATA_TYPE = """
?anno oa:annotatedAt ?annotatedAt .
?anno oa:hasTarget ?target .
?target rdf:type ?dataType .
OPTIONAL {?target oa:item ?item .
?item rdf:type ?itemType}"""

ANNOTATIONS_FOR_DOMAIN = """
?anno oa:annotatedAt ?annotatedAt .
?anno oa:hasBody ?domainOfInterest .
?domainOfInterest rdf:type oa:SemanticTag ."""

ANNOTATIONS_FOR_MOTIVATION = """
?anno oa:annotatedAt ?annotatedAt .
?anno oa:motivatedBy ?motivation"""

ANNOTATIONS_FOR_ORGANIZATION = """
?anno oa:annotatedAt ?annotatedAt .
?anno oa:annotatedBy ?organization .
?organization rdf:type foaf:Organization .
?organization foaf:name ?organizationName ."""

ANNOTATIONS_FOR_REGION = """
"""  # TODO

ANNOTATIONS_FOR_STATUS = """
?anno oa:annotatedAt ?annotatedAt .
?anno oa:hasTarget ?target ."""

ANNOTATIONS_FOR_TARGET = """
?anno oa:annotatedAt ?annotatedAt .
?anno oa:hasTarget ?target .
OPTIONAL {?target oa:item ?item}"""

ANNOTATIONS_FOR_TITLE = """
?paper text:query (dcterm:title '%s' 100) .
?anno cito:hasCitingEntity ?paper ;
      oa:annotatedAt ?annotatedAt ."""

ANNOTATIONS_FOR_USER = """
?anno oa:annotatedAt ?annotatedAt .
?anno oa:annotatedBy ?person .
?person foaf:accountName ?userName"""

ANNOTATION_CLAUSES = {'bodyType':ANNOTATIONS_FOR_BODY_TYPE,
                      'citingType':ANNOTATIONS_FOR_CITING_TYPE,
                      'comment':ANNOTATIONS_FOR_COMMENT,
                      'creatorFamilyName':ANNOTATIONS_FOR_CREATOR_FAMILY_NAME,
                      'creatorGivenName':ANNOTATIONS_FOR_CREATOR_GIVEN_NAME,
                      'dataType':ANNOTATIONS_FOR_DATA_TYPE,
                      'domainOfInterest':ANNOTATIONS_FOR_DOMAIN,
                      'motivation':ANNOTATIONS_FOR_MOTIVATION,
                      'organization':ANNOTATIONS_FOR_ORGANIZATION,
                      'region':ANNOTATIONS_FOR_REGION,
                      'status':ANNOTATIONS_FOR_STATUS,
                      'target':ANNOTATIONS_FOR_TARGET,
                      'title':ANNOTATIONS_FOR_TITLE,
                      'userName':ANNOTATIONS_FOR_USER}


def get_multi_value_parameter_names():
    """
    Get the list parameter names that can be used in an open searches and can
    have multiple occurrences.

    Returns:
        a list of parameter names

    """
    parameter_names = ANNOTATION_CLAUSES.keys()
    parameter_names.remove('status')
    return parameter_names


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


def _do__open_search(query_attr, graph, triples):
    depth = int(query_attr.get('depth', 3))
    ret = _populate_annotations(graph, triples, depth)
    return ret


def _populate_annotations(graph, triples, depth=3):
    ret = []
    for row in triples:
        tmp_g = Graph()
        for subj in extract_subject(graph, row[0], depth):
            tmp_g.add(subj)
        ret.append(tmp_g)
    return ret


def _populate_graph(graph, triples):
    tmp_g = Graph()
    for row in triples:
        for subj in _extract_subject_form_graph(graph, row[0]):
            tmp_g.add(subj)
    return tmp_g


def _extract_subject_form_graph(graph, subject):
    tmp_g = Graph()
    for res in graph.triples((subject, None, None)):
        tmp_g.add(res)
    return tmp_g


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
    LOGGING.debug("Using limit: %s", limit)
    offset = (int(query_attr.get('startPage', 1)) - 1) * limit
    offset = offset + int(query_attr.get('startIndex', 1)) - 1
    if offset > 0:
        LOGGING.debug("Using offset: %s", offset)
        return " OFFSET " + str(offset)
    else:
        return ""


def _get_graph(query_attr):
    """
    Get the graph based on the value of the attribute 'status'.

    If the users has not set a value for 'status' the use the STABLE graph

    Args:
        query_attr (dict): The query parameters from the users request.
    """
    graph_name = str(query_attr.get('status', STABLE))
    return generate_graph(CharmeMiddleware.get_store(), graph_name)


class SearchProxy(object):
    def __init__(self, query):
        _query = query
        self.query_signature = None
        super(SearchProxy, self).__init__(self)


def get_suggestions(parameter_names, query_attr):
    """
    Get the values for the given parameter names.


    Args:
        parameter_names (str): The parameter names to search for. This should be
            a space separated list or an '*'. For a list of available parameter
            names use get_parameter_names().
        query_attr (dict): The query parameters from the users request.

    Returns:
        list of dict. Key words:
            graph - A graph containing the results
            count - The count of available results
            searchTerm - The parameter name that was searched for

    """
    LOGGING.debug("get_suggestions(%s, query_attr)", parameter_names)
    graph = _get_graph(query_attr)
    limit = _get_limit(query_attr)
    offset = _get_offset(query_attr)
    results = []
    total_results = 0
    parameter_name_list = (re.sub('[' + string.punctuation + ']', '',
                                  parameter_names).split())
    if parameter_names == "*":
        parameter_name_list = ["*"]
    where_clause = ''
    for parameter_name in ANNOTATION_CLAUSES.keys():
        where_clause = (where_clause +
                        _get_where_for_parameter_name(query_attr,
                                                      parameter_name))
    for parameter_name in parameter_name_list:
        if parameter_name == "bodyType" or parameter_name == "*":
            result, count = _get_body_types(graph, "bodyType", where_clause,
                                            limit, offset)
            results.append(result)
            total_results = total_results + count
        if parameter_name == "citingType" or parameter_name == "*":
            result, count = _get_citing_types(graph, "citingType", where_clause,
                                            limit, offset)
            results.append(result)
            total_results = total_results + count
        if parameter_name == "dataType" or parameter_name == "*":
            result, count = _get_data_types(graph, "dataType", where_clause,
                                            limit, offset)
            results.append(result)
            total_results = total_results + count
        if parameter_name == "domainOfInterest" or parameter_name == "*":
            result, count = _get_domains_of_interest(graph, "domainOfInterest",
                                                     where_clause, limit,
                                                     offset)
            results.append(result)
            total_results = total_results + count
        if parameter_name == "motivation" or parameter_name == "*":
            result, count = _get_motivations(graph, "motivation", where_clause,
                                             limit, offset)
            results.append(result)
            total_results = total_results + count
        if parameter_name == "organization" or parameter_name == "*":
            result, count = _get_organizations(graph, "organization",
                                               where_clause, limit, offset)
            results.append(result)
            total_results = total_results + count
    return results, total_results


def _get_body_types(graph, parameter_name, where_clause, limit, offset):
    statement = (PREFIX +
    """
    SELECT Distinct ?bodyType
    WHERE {
    {%s}
    ?anno oa:hasBody ?body .
    ?body rdf:type ?bodyType .
    }
    ORDER BY ?bodyType
    LIMIT %s
    %s""" % (where_clause, limit, offset))
    count_statement = (PREFIX +
    """
    SELECT  count (Distinct ?bodyType)
    WHERE {
    {%s}
    ?anno oa:hasBody ?body .
    ?body rdf:type ?bodyType .
    }""") % where_clause
    return _do_query(graph, parameter_name, statement, count_statement,
                     "http://www.w3.org/2004/02/skos/core#prefLabel")


def _get_citing_types(graph, parameter_name, where_clause, limit, offset):
    statement = (PREFIX +
    """
    SELECT Distinct ?citingType
    WHERE {
    {%s}
    ?anno oa:annotatedAt ?annotatedAt .
    ?anno cito:hasCitingEntity ?citingEntity .
    ?citingEntity rdf:type ?citingType .
    }
    ORDER BY ?citingType
    LIMIT %s
    %s""" % (where_clause, limit, offset))
    count_statement = (PREFIX +
    """
    SELECT  count (Distinct ?citingType)
    WHERE {
    {%s}
    ?anno oa:annotatedAt ?annotatedAt .
    ?anno cito:hasCitingEntity ?citingEntity .
    ?citingEntity rdf:type ?citingType .
    }""") % where_clause
    return _do_query(graph, parameter_name, statement, count_statement,
                     "http://www.w3.org/2004/02/skos/core#prefLabel")


def _get_data_types(graph, parameter_name, where_clause, limit, offset):
    statement = (PREFIX +
    """
    SELECT Distinct ?dataType
    WHERE {
    {%s}
    ?anno oa:hasTarget ?target .
    ?target rdf:type ?dataType .
    FILTER (?dataType != oa:Composite)
    }
    """ % (where_clause))
    result1, count = _do_query(graph, parameter_name, statement, None,
                     "http://www.w3.org/2004/02/skos/core#prefLabel")

    statement = (PREFIX +
    """
    SELECT Distinct ?itemType
    WHERE {
    {%s}
    ?anno oa:hasTarget ?target .
    ?target oa:item ?item .
    ?item rdf:type ?itemType .
    }
    ORDER BY ?itemType
    """ % (where_clause))
    result2, count = _do_query(graph, parameter_name, statement, None,
                     "http://www.w3.org/2004/02/skos/core#prefLabel")

    result = {'searchTerm': parameter_name}
    # Combine the graphs
    tmp_graph = result1['graph']
    for res in result2['graph']:
        tmp_graph.add(res)

    count = len(tmp_graph)
    result['count'] = count

    # filter on limit and offset
    statement = (PREFIX +
    """
    SELECT ?s ?p ?o
    WHERE {
    ?s ?p ?o
    }
    ORDER BY ?s
    LIMIT %s
    %s""" % (limit, offset))
    triples = tmp_graph.query(statement)
    result['graph'] = Graph()
    for res in triples:
        result['graph'].add(res)
    LOGGING.debug("_get_data_types returning %s triples out of %s for %s",
                  len(result['graph']), result['count'], parameter_name)
    return result, count


def _get_domains_of_interest(graph, parameter_name, where_clause, limit,
                             offset):
    statement = (PREFIX +
    """
    SELECT DISTINCT ?body ?domainOfInterest
    WHERE {
    {%s}
    ?anno oa:hasBody ?body .
    ?body rdf:type oa:SemanticTag .
    ?body skos:prefLabel ?domainOfInterest .
    }
    ORDER BY ?domainOfInterest
    LIMIT %s
    %s""" % (where_clause, limit, offset))
    count_statement = (PREFIX +
    """
    SELECT count (Distinct ?domainOfInterest)
    WHERE {
    {%s}
    ?anno oa:hasBody ?body .
    ?body rdf:type oa:SemanticTag .
    ?body skos:prefLabel ?domainOfInterest .
    }""") % where_clause
    return _do_query(graph, parameter_name, statement, count_statement,
                     "http://www.w3.org/2004/02/skos/core#prefLabel")


def _get_motivations(graph, parameter_name, where_clause, limit, offset):
    statement = (PREFIX +
    """
    SELECT Distinct ?motivation
    WHERE {
    {%s}
    ?anno oa:motivatedBy ?motivation .
    }
    ORDER BY ?motivation
    LIMIT %s
    %s""" % (where_clause, limit, offset))
    count_statement = (PREFIX +
    """
    SELECT count (Distinct ?motivation)
    WHERE {
    {%s}
    ?anno oa:motivatedBy ?motivation .
    }""") % where_clause
    return _do_query(graph, parameter_name, statement, count_statement,
                     "http://www.w3.org/2004/02/skos/core#prefLabel")


def _get_organizations(graph, parameter_name, where_clause, limit, offset):
    statement = (PREFIX +
    """
    SELECT DISTINCT ?organization ?name
    WHERE {
    {%s}
    ?anno oa:annotatedBy ?organization .
    ?organization rdf:type foaf:Organization .
    ?organization foaf:name ?name .
    }
    ORDER BY ?name
    LIMIT %s
    %s""" % (where_clause, limit, offset))
    count_statement = (PREFIX +
    """
    SELECT count (Distinct ?name)
    WHERE {
    {%s}
    ?anno oa:annotatedBy ?organization .
    ?organization rdf:type foaf:Organization .
    ?organization foaf:name ?name .
    }""") % where_clause
    return _do_query(graph, parameter_name, statement, count_statement,
                     "http://xmlns.com/foaf/0.1/name")


def _do_query(graph, parameter_name, statement, count_statement,
              labelType):
    LOGGING.debug("_do_query %s", statement)
    result = {'searchTerm': parameter_name}
    if count_statement != None:
        result['count'] = _get_count(graph.query(count_statement))
    else:
        result['count'] = -1
    triples = graph.query(statement)
    result['graph'] = Graph()
    url = urlparse(labelType)
    obj = ''
    for row in triples:
        if len(row) > 1:
            obj = row[1]
        else:
            url = urlparse(row[0])
            obj = ''
            if url.fragment != '':
                obj = url.fragment
            elif url.path != None:
                path = str(url.path)
                bits = path.split('/')
                obj = bits[(len(bits) - 1)]
            else:
                obj = row[0]
        result['graph'].add((URIRef(row[0]), URIRef(labelType), Literal(obj)))
    LOGGING.debug("_do_query returning %s triples out of %s for %s",
                  len(result['graph']), result['count'], parameter_name)
    return result, result['count']


def get_search_results(query_attr):
    """
    Get the annotations which refer to the given parameters.

    Args:
        query_attr (dict): The query parameters from the users request.

    Returns:
        list of graphs. The result of the search.

    """
    LOGGING.debug("get_search_results(query_attr)")
    where_clause = _get_where_clause(query_attr)

    statement = PREFIX + ANNOTATIONS_SELECT + where_clause + ANNOTATIONS_ORDER
    if _get_limit(query_attr) > 0:
        statement = statement + ' LIMIT ' + str(_get_limit(query_attr))
    if _get_offset(query_attr) != None:
        statement = statement + _get_offset(query_attr)

    statement_count = PREFIX + ANNOTATIONS_SELECT_COUNT + where_clause
    graph = _get_graph(query_attr)
    triples = graph.query(statement)
    results = _do__open_search(query_attr, graph, triples)
    total_results = _get_count(graph.query(statement_count))
    LOGGING.debug("get_search_results returning %s triples out of %s",
                  len(results), total_results)
    return results, total_results


def _get_where_clause(query_attr):
    """
    Get the where clause based on the values in query_attr.

    Args:
        query_attr (dict): The query parameters from the users request.

    Returns:
        str The where clause.

    """
    where_clause = ''
    for parameter_name in ANNOTATION_CLAUSES.keys():
        where_clause = (where_clause +
                        _get_where_for_parameter_name(query_attr,
                                                      parameter_name))
    # special case for status
    if len(where_clause) == 0:
        where_clause = where_clause = '{' + ANNOTATION_CLAUSES['status'] + '}'
    where_clause = ' WHERE {' + where_clause + '}'
    return where_clause


def _get_where_for_parameter_name(query_attr, parameter_name):
    """
    Add the where clause and filter for the given parameter name.

    Args:
        query_attr (dict): The query parameters from the users request.
        parameter_name (str): The name of the parameter.

    Returns:
        str The where clause.
    """
    values = query_attr.get(parameter_name)
    if values == None or len(values) < 1 or parameter_name == 'status':
        return  ''
    if parameter_name == 'title' or parameter_name == 'comment':
        return '{' + (ANNOTATION_CLAUSES[parameter_name] % values) + '}'

    # TODO remove split when I can work out to handle the parameter being
    # returned as a list.
    values = values.split()
    where_clause = '{' + ANNOTATION_CLAUSES[parameter_name] + ' FILTER ('
    first_term = True
    for value in values:
        if first_term:
            first_term = False
        else:
            where_clause = where_clause + ' || '
        where_clause = where_clause + '?' + parameter_name + "="
        if (parameter_name == 'userName' or parameter_name == 'creatorFamilyName'
            or parameter_name == 'creatorGivenName'):
            where_clause = where_clause + "'" + value + "'"
        else:
            where_clause = where_clause + "<" + URIRef(value) + '>'
        # special case for composite
        if parameter_name == 'target':
            where_clause = where_clause + ' || '
            where_clause = where_clause + '?' + "item="
            where_clause = where_clause + "<" + URIRef(value) + '>'
        # special case for composite
        if parameter_name == 'dataType':
            where_clause = where_clause + ' || '
            where_clause = where_clause + '?' + "itemType="
            where_clause = where_clause + "<" + URIRef(value) + '>'
    where_clause = where_clause + ')} '

    return where_clause


