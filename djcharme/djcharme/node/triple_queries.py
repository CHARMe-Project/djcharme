'''
BSD Licence
Copyright (c) 2015, Science & Technology Facilities Council (STFC)
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

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


Contents:
This module contains pre-formatted queries of the triple store.

'''
from urllib2 import URLError

from SPARQLWrapper.SPARQLExceptions import EndPointNotFound
from django.conf import settings
from rdflib.graph import Graph

from djcharme.charme_middleware import CharmeMiddleware
from djcharme.exception import StoreConnectionError
from djcharme.node.constants import OA, FOAF


def _collect_all(graph, cache_graph, uri_ref, depth=1):
    if depth is None:
        depth = 1
    for res in graph.triples((uri_ref, None, None)):
        cache_graph.add(res)
        if depth > 1:
            new_depth = depth
            if new_depth > 1:  # decrease the depth by one
                new_depth = new_depth - 1
            _collect_all(graph, cache_graph, res[2], new_depth)


def _format_graph_uri(graph):
    """
    Builds a named graph URIRef using, if exists,
        a settings.SPARQL_QUERY parameter.

    Args:
        graph_name (str): The name of the graph

    Returns:
        str containing graph the uri

    """
    if ('http://' in graph) or ('https://' in graph):
        return graph

    return ('{uri}/{graph}'.
            format(uri=getattr(settings, 'SPARQL_DATA', 'http://dummyhost'),
                   graph=graph))


def generate_graph(store, graph):
    """
    Generate a new Graph for the given store

    Args:
        store (SPARQLUpdateStore): The store to use
        graph_name (str): The name of the graph

    Returns:
        rdflib.graph.Graph for the given store

    """
    return Graph(store=store, identifier=_format_graph_uri(graph))


def extract_subject(graph, subject, depth):
    """
    Extracts from graph and describes, if exists, the specified subject

    Args:
        graph (rdflib.graph.Graph): The graph containing the data
        subject (str) the subject of the triple
        depth (int) the depth to go down into the graph when retrieving data

    Returns:
        rdflib.graph.Graph containing details about the subject

    """
    tmp_g = Graph()
    for res in graph.triples((subject, None, None)):
        tmp_g.add(res)
        if depth is None or depth > 0:
            _collect_all(graph, tmp_g, res[2], depth)
    return tmp_g


def get_organisation_for_anotation(graph, annotation_uri):
    """
    Get the name of the organization via which an annotation was created.

    Args:
        graph (rdflib.graph.Graph): The graph containing the annotation
        annotation_uri (URIRef): The URI of the annotation

    Returns:
        str containing the name of the organization

    """
    statement = (
        'PREFIX oa: <http://www.w3.org/ns/oa#> '
        'PREFIX foaf: <http://xmlns.com/foaf/0.1/> '
        'SELECT Distinct ?organizationName WHERE {{'
        '<{anno}> oa:annotatedBy ?organization . '
        '?organization rdf:type foaf:Organization . '
        '?organization foaf:name ?organizationName  }}'
        .format(anno=annotation_uri))
    triples = graph.query(statement)
    for row in triples:
        # there should only be one organization associated with an annotation
        return (row['organizationName'])
    return None


def get_all_annotations(graph_name):
    """
    Get a graph containing all the annotations, targets and bodies.

    Args:
        graph_name (str): The name of the graph

    Returns:
        rdflib.graph.Graph containing all the annotations, targets and bodies

    """
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
                                   "\n" + str(ex))
    except EndPointNotFound as ex:
        raise StoreConnectionError("Cannot open a connection with triple store"
                                   "\n" + str(ex))
    get_annotation_count(graph_name)
    return tmp_g


def get_annotation_count(graph_name):
    """
    Get a count of annotations for the given graph.

    Args:
        graph_name (str): The name of the graph

    Returns:
        int the count of annotations for the given graph

    """
    graph = generate_graph(CharmeMiddleware.get_store(), graph_name)
    anno = graph.triples((None, None, OA['Annotation']))
    count = 0
    for _ in anno:
        count += 1
    return count


def get_annotation_count_per_organization(graph_name):
    """
    Get a count of annotations for the given graph, with the results broken
    down into count per organization.

    A list of organizations is obtained from the triple store. Then for each
    organization a count of annotations in made.

    Args:
        graph_name (str): The name of the graph

    Returns:
        dict where key: (str) the name of the organization
                   value: (int) the count of annotations for organization in
                          the given graph

    """
    graph = generate_graph(CharmeMiddleware.get_store(), graph_name)

    statement = (
        'PREFIX oa: <{oa}> '
        'PREFIX foaf: <{foaf}> '
        'SELECT DISTINCT ?organizationName WHERE {{'
        '?anno oa:annotatedBy ?organization . '
        '?organization rdf:type foaf:Organization .'
        '?organization foaf:name ?organizationName}}'
        .format(oa=OA, foaf=FOAF))
    triples = graph.query(statement)
    anno_count = {}

    for row in triples:
        anno_count[row['organizationName']] = (
            _get_annotation_count_for_organization(graph,
                                                   row['organizationName']))

    return anno_count


def _get_annotation_count_for_organization(graph, organization_name):
    """
    Get a count of annotations for the given organization.

    Args:
        graph (rdflib.graph.Graph): The graph containing the organizations
        organization_name (str):  The name of the organization

    Returns:
        int the count of annotations for the organization

    """
    statement = (
        'PREFIX oa: <{oa}> '
        'PREFIX foaf: <{foaf}> '
        'SELECT count(DISTINCT ?anno) WHERE {{'
        '?anno oa:annotatedBy ?organization . '
        '?organization rdf:type foaf:Organization .'
        '?organization foaf:name "{organizationName}"}}'
        .format(oa=OA, foaf=FOAF, organizationName=organization_name))
    triples = graph.query(statement)
    for t in triples:
        return t[0]
    return 0


def get_target_types(graph_name):
    """
    Get a list of target types and a count for each type for the given graph.

    Args:
        graph_name (str): The name of the graph

    Returns:
        dict where key: (str) the target type
                   value: (int) the count of target type in the given graph

    """
    graph = generate_graph(CharmeMiddleware.get_store(), graph_name)
    statement = (
        'PREFIX oa: <{oa}> '
        'SELECT DISTINCT ?type WHERE {{'
        '?anno oa:hasTarget ?target . '
        '?target rdf:type ?type  }}'
        .format(oa=OA))
    triples = graph.query(statement)

    type_count = {}
    for row in triples:
        type_count[row['type']] = _get_target_type_count(graph, row['type'])

    return type_count


def _get_target_type_count(graph, target_type):
    """
    Get a count of occurrence of the given target type.

    Args:
        graph (rdflib.graph.Graph): The graph containing the target types
        target_type (str): The target type

    Returns:
        int the count of the occurrences of the given target type

    """
    statement = (
        'PREFIX oa: <{oa}> '
        'SELECT count(?s) WHERE {{'
        '?s oa:hasTarget ?target . '
        '?target rdf:type <{type}> }}'
        .format(oa=OA, type=target_type))
    triples = graph.query(statement)
    for t in triples:
        return t[0]
    return 0


def get_annotation_count_per_target(graph_name):
    """
    Get a list of targets and a count for each target for the given graph.

    Args:
        graph_name (str): The name of the graph

    Returns:
        dict where key: (str) the target
                   value: (int) the count of target in the given graph

    """
    graph = generate_graph(CharmeMiddleware.get_store(), graph_name)
    statement = (
        'PREFIX oa: <{oa}> '
        'SELECT DISTINCT ?target WHERE {{'
        '?anno oa:hasTarget ?target }}'
        .format(oa=OA))
    triples = graph.query(statement)

    target_count = {}
    for row in triples:
        target_count[row['target']] = _get_annotation_count_for_target(
            graph, row['target'])

    return target_count


def _get_annotation_count_for_target(graph, target):
    """
    Get a count of occurrence of the given target.

    Args:
        graph (rdflib.graph.Graph): The graph containing the target types
        target_type (str): The target

    Returns:
        int the count of the occurrences of the given target

    """
    statement = (
        'PREFIX oa: <{oa}> '
        'SELECT count(?s) WHERE {{'
        '?s oa:hasTarget <{target}> }}'
        .format(oa=OA, target=target))
    triples = graph.query(statement)
    for t in triples:
        return t[0]
    return 0


def get_annotation_count_per_user(graph_name):
    """
    Get a count of annotations for the given graph, with the results broken
    down into count per user.

    A list of users is obtained from the triple store. Then for each
    user a count of annotations in made.

    Args:
        graph_name (str): The name of the graph

    Returns:
        dict where key: (str) the name of the user
                   value: (int) the count of annotations for user in
                          the given graph

    """
    graph = generate_graph(CharmeMiddleware.get_store(), graph_name)

    statement = (
        'PREFIX oa: <{oa}> '
        'PREFIX foaf: <{foaf}> '
        'SELECT DISTINCT ?accountName WHERE {{'
        '?anno oa:annotatedBy ?person . '
        '?person rdf:type foaf:Person .'
        '?person foaf:accountName ?accountName}}'
        .format(oa=OA, foaf=FOAF))
    triples = graph.query(statement)
    anno_count = {}

    for row in triples:
        anno_count[row['accountName']] = (
            _get_annotation_count_for_user(graph,
                                           row['accountName']))

    return anno_count


def _get_annotation_count_for_user(graph, user):
    """
    Get a count of annotations for the given user.

    Args:
        graph (rdflib.graph.Graph): The graph containing the users
        user (str):  The name of the user

    Returns:
        int the count of annotations for the user

    """
    statement = (
        'PREFIX oa: <{oa}> '
        'PREFIX foaf: <{foaf}> '
        'SELECT count(DISTINCT ?anno) WHERE {{'
        '?anno oa:annotatedBy ?person . '
        '?person rdf:type foaf:Person .'
        '?person foaf:accountName "{accountName}"}}'
        .format(oa=OA, foaf=FOAF, accountName=user))
    triples = graph.query(statement)
    for t in triples:
        return t[0]
    return 0
