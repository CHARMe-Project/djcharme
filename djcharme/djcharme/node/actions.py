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
from datetime import datetime
import logging
from urllib2 import URLError
import uuid

from SPARQLWrapper.SPARQLExceptions import EndPointNotFound
from django.conf import settings
from django.db.models import ObjectDoesNotExist
from rdflib import Graph, URIRef, Literal
from rdflib.graph import ConjunctiveGraph

from djcharme.charme_middleware import CharmeMiddleware
from djcharme.exception import NotFoundError
from djcharme.exception import ParseError
from djcharme.exception import SecurityError
from djcharme.exception import StoreConnectionError
from djcharme.exception import UserError
from djcharme.node import _extract_subject
from djcharme.node.constants import ANNO_URI, NODE_URI, TARGET_URI, \
    REPLACEMENT_URIS, REPLACEMENT_URIS_MULTIVALUED
from djcharme.node.constants import FOAF, RDF, PROV, OA, CH_NODE
from djcharme.node.constants import FORMAT_MAP, ALLOWED_CREATE_TARGET_TYPE, \
    RESOURCE
from djcharme.node.constants import GRAPH_NAMES, SUBMITTED, INVALID, RETIRED


LOGGING = logging.getLogger(__name__)


def rdf_format_from_mime(mimetype):
    for key, value in FORMAT_MAP.iteritems():
        if mimetype == value:
            return key


def format_graph_iri(graph, baseurl='http://dummyhost'):
    '''
        Builds a named graph URIRef using, if exists,
        a settings.SPARQL_QUERY parameter.

        - string **graph**
            the graph name
        * return String
    '''
    if ('http://' in graph) or ('https://' in graph):
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


def insert_rdf(data, mimetype, user, client, graph=None, store=None):
    '''
        Inserts an RDF/json-ld document into the triplestore
        - string **data**
            a document
        - string **mimetype**
            the document mimetype
        - User **user**
            the User object from a request
        - Client **client**
            the Client object from a request
        - string **graph**
            the graph name
        - rdflib.Store **store**
            if none use the return of get_store()
        * return:str - The URI of the new annotation
    '''
    LOGGING.debug("insert_rdf(data, mimetype, user, graph, store)")
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
    anno_uri = ''
    for res in tmp_g:
        if (res[1] == URIRef(RDF + 'type')
            and res[2] == URIRef(OA + 'Annotation')):
            anno_uri = res[0]
            prov = _get_prov(anno_uri, user, client)[0]
            for triple in prov:
                try:
                    final_g.add(triple)
                except EndPointNotFound as ex:
                    raise StoreConnectionError("Cannot insert triple. "
                                               + str(ex))
                except Exception as ex:
                    raise ParseError("Cannot insert triple. " + str(ex))
        try:
            final_g.add(res)
        except EndPointNotFound as ex:
            raise StoreConnectionError("Cannot insert triple. " + str(ex))
        except Exception as ex:
            raise ParseError("Cannot insert triple. " + str(ex))
    return anno_uri


def modify_rdf(request, mimetype):
    """
    Modify an annotation in the triplestore.

    Args:
        request (WSGIRequest): The http request
        mimetype (str): The document mimetype

    Return:
        a URIRef containing the URI of the modified annotation

    """
    LOGGING.debug("modify_rdf(request, " + str(mimetype) + ")")
    store = CharmeMiddleware.get_store()
    tmp_g = Graph()
    data = request.body
    # Necessary as RDFlib does not contain the json-ld lib
    try:
        tmp_g.parse(data=data, format=mimetype)
    except SyntaxError as ex:
        try:
            raise ParseError(str(ex))
        except UnicodeDecodeError:
            raise ParseError(ex.__dict__["_why"])

    original_uri = _get_annotation_uri_from_graph(tmp_g)
    # replace original uri in tmp graph
    for res in tmp_g:
        if res[0] == original_uri:
            tmp_g.remove(res)
            new_res = (URIRef('%s:%s' % (CH_NODE, ANNO_URI)), res[1], res[2])
            tmp_g.add(new_res)

    activity_uri = URIRef((getattr(settings, 'NODE_URI', NODE_URI)
                  + '/%s/%s' % (RESOURCE, uuid.uuid4().hex)))
    # retire original
    if (change_annotation_state(original_uri, RETIRED, request, activity_uri)
        == None):
        raise UserError(("Current annotation status of %s is final. Data " \
                         "has not been updated." % RETIRED))

    _format_submitted_annotation(tmp_g)
    final_g = generate_graph(store, SUBMITTED)

    for nspace in tmp_g.namespaces():
        final_g.store.bind(str(nspace[0]), nspace[1])
    anno_uri = ''
    for res in tmp_g:
        if (res[1] == URIRef(RDF + 'type')
            and res[2] == URIRef(OA + 'Annotation')):
            anno_uri = res[0]
            prov, annotated_at, person_uri = _get_prov(anno_uri, request.user,
                                                      request.client)
            for triple in prov:
                try:
                    final_g.add(triple)
                except Exception as ex:
                    raise ParseError("Cannot insert triple. " + str(ex))
            modify_prov = _get_modify_prov(anno_uri, original_uri, annotated_at,
                                           activity_uri, person_uri)
            for triple in modify_prov:
                try:
                    final_g.add(triple)
                except EndPointNotFound as ex:
                    raise StoreConnectionError("Cannot insert triple. "
                                               + str(ex))
                except Exception as ex:
                    raise ParseError("Cannot insert triple. " + str(ex))
        try:
            final_g.add(res)
        except EndPointNotFound as ex:
            raise StoreConnectionError("Cannot insert triple. " + str(ex))
        except Exception as ex:
            raise StoreConnectionError("Cannot insert triple. " + str(ex))
    return anno_uri


def _get_annotation_uri_from_graph(graph):
    """
    Get the URI of the annotation from the given graph.

    Args:
        graph (rdflib.graph.Graph): The graph containing the annotation

    Return:
        a URIRef containing the URI of the annotation

    """
    for res in graph:
        if (res[1] == URIRef(RDF + 'type')
            and res[2] == URIRef(OA + 'Annotation')):
            return res[0]


def _get_prov(annotation_uri, user, client):
    """
    Get the provenance data for the annotation.

    Args:
        annotation_uri (URIRef): The URI of the annotation
        user (User): The user details.
        client (client): The Client object from a request

    Returns:
        a list of triples
        a URIRef containing the annotated at time
        a URIRef containing the person URI

    """
    person_uri = URIRef((getattr(settings, 'NODE_URI', NODE_URI)
                  + '/%s/%s' % (RESOURCE, uuid.uuid4().hex)))
    triples = []
    annotated_at = Literal(datetime.utcnow())
    triples.append((annotation_uri, URIRef(OA + 'annotatedAt'), annotated_at))
    triples.append((annotation_uri, URIRef(OA + 'annotatedBy'), person_uri))
    triples.append((person_uri, URIRef(RDF + 'type'),
                    URIRef(FOAF + 'Person')))
    triples.append((person_uri, URIRef(FOAF + 'accountName'),
                    Literal(user.username)))
    if user.last_name != None and len(user.last_name) > 0:
        triples.append((person_uri, URIRef(FOAF + 'familyName'),
                        Literal(user.last_name)))
    if user.first_name != None and len(user.first_name) > 0:
        triples.append((person_uri, URIRef(FOAF + 'givenName'),
                        Literal(user.first_name)))
    try:
        show_email = user.userprofile.show_email
    except ObjectDoesNotExist:
        show_email = False
    if show_email and user.email != None and len(user.email) > 0:
        triples.append((person_uri, URIRef(FOAF + 'mbox'), Literal(user.email)))
    if client.name != None and len(client.name) > 0:
        triples.append((annotation_uri, URIRef(OA + 'annotatedBy'),
                        URIRef(client.url)))
        triples.append((URIRef(client.url), URIRef(RDF + 'type'),
                        URIRef(FOAF + 'Organization')))
        triples.append((URIRef(client.url), URIRef(FOAF + 'name'),
                        Literal(client.name)))

    return (triples, annotated_at, person_uri)


def _get_modify_prov(annotation_uri, original_anno_uri, annotated_at,
                     activity_uri, person_uri):
    """
    Get the provenance data for the annotation.

    Args:
        annotation_uri (URIRef): The URI of the annotation
        original_anno_uri (URIRef): The uri of the original annotation.
        annotated_at (Literal): The time the annotation was created
        activity_uri (URIRef): The URI of the Activity
        person_uri (URIRef): The URI of the person

    Returns:
        a list of triples.

    """
    triples = []
    triples.append((annotation_uri, URIRef(PROV + 'wasGeneratedBy'),
                    activity_uri))
    triples.append((annotation_uri, URIRef(PROV + 'wasRevisionOf'),
                    original_anno_uri))

    triples.append((activity_uri, URIRef(RDF + 'type'),
                    URIRef(PROV + 'Activity')))
    triples.append((activity_uri, URIRef(PROV + 'invalidated'),
                    original_anno_uri))
    triples.append((activity_uri, URIRef(PROV + 'generated'), annotation_uri))

    triples.append((activity_uri, URIRef(PROV + 'wasStartedAt'), annotated_at))
    triples.append((activity_uri, URIRef(PROV + 'wasStartedBy'), person_uri))
    triples.append((activity_uri, URIRef(PROV + 'wasEndedAt'), annotated_at))
    triples.append((activity_uri, URIRef(PROV + 'wasEndedBy'), person_uri))
    return triples


def _format_resource_uri_ref(resource_id):
    '''
        Returns the URIRef associated with the id for this specific node
    '''
    if resource_id.startswith('http:') or resource_id.startswith('https:'):
        return URIRef(resource_id)
    return URIRef('%s/%s/%s' % (getattr(settings, 'NODE_URI', NODE_URI),
                                RESOURCE, resource_id))


def _format_node_uri_ref(uriref, generated_uris):
    '''
        Rewrite a URIRef according to the node configuration
        * uriref:rdflib.URIRef
        * generated_uris:dict of generated URIs
    '''
    if isinstance(uriref, URIRef) and NODE_URI in uriref:
        uriref = URIRef(uriref.replace(NODE_URI,
                                       getattr(settings, 'NODE_URI', NODE_URI)
                                       + '/'))

    if isinstance(uriref, URIRef) and CH_NODE in uriref:
        uriref = URIRef(uriref.replace(CH_NODE + ':',
                                       getattr(settings, 'NODE_URI', NODE_URI)
                                       + '/'))

    if isinstance(uriref, URIRef):
        for key in generated_uris.keys():
            if key in uriref:
                uriref = URIRef(uriref.replace(key, "%s/%s" %
                                               (RESOURCE, generated_uris[key])))
    return uriref


def _format_submitted_annotation(graph):
    '''
        Formats the graph according to the node configuration
    '''
    generated_uris = {}
    for id_ in REPLACEMENT_URIS:
        generated_uris[id_] = uuid.uuid4().hex

    target_id_found = False
    target_id_valid = False
    for subject, pred, obj in graph:
        graph.remove((subject, pred, obj))
        # The use of TARGET_URI is only allowed for specific types
        if ((isinstance(subject, URIRef) and TARGET_URI in subject) or
            (isinstance(obj, URIRef) and TARGET_URI in obj)):
            target_id_found = True
            if (pred == URIRef(RDF + 'type') and
                (obj in ALLOWED_CREATE_TARGET_TYPE)):
                target_id_valid = True
        for value in REPLACEMENT_URIS_MULTIVALUED:
            if value in subject:
                bits = subject.split(CH_NODE + ':')
                if len(bits) > 1:
                    key = bits[1]
                    if key not in generated_uris.keys():
                        generated_uris[key] = uuid.uuid4().hex
            if value in obj:
                bits = subject.split(CH_NODE + ':')
                if len(bits) > 1:
                    key = bits[1]
                    if key not in generated_uris.keys():
                        generated_uris[key] = uuid.uuid4().hex

        subject = _format_node_uri_ref(subject, generated_uris)
        pred = _format_node_uri_ref(pred, generated_uris)
        obj = _format_node_uri_ref(obj, generated_uris)
        graph.add((subject, pred, obj))

    if target_id_found and not target_id_valid:
        types = ""
        for type_ in ALLOWED_CREATE_TARGET_TYPE:
            if types != "":
                types = types + ', '
            types = types + type_
        raise UserError((TARGET_URI + ' may only be used for ' + types +
                         ' target types'))


def change_annotation_state(annotation_uri, new_graph, request,
                            activity_uri=None):
    """
    Advance the status of an annotation.

    Args:
        annotation_uri (URIRef): The URI of the annotation.
        new_graph (str): The name of the graph/state to move the annotation to.
        request (WSGIRequest): The incoming request.
        activity_uri (URIRef): The uri of the Activity

    Returns:
        graph (rdflib.graph.Graph): The new graph containing the updated
        annotation.

    """
    LOGGING.debug("change_annotation_state(%s, %s, request, %s)",
                  annotation_uri, new_graph, activity_uri)
    annotation_uri = _format_resource_uri_ref(annotation_uri)
    _validate_graph_name(new_graph)
    old_graph = find_annotation_graph(annotation_uri)
    if old_graph == None:
        raise NotFoundError(("Annotation %s not found" % annotation_uri))
    if old_graph == new_graph:
        return
    if old_graph == INVALID or old_graph == RETIRED:
        raise UserError(("Current annotation status of %s is final. Status " \
                         "has not been updated." % old_graph))
    old_g = generate_graph(CharmeMiddleware.get_store(), old_graph)
    user = request.user
    if not _is_my_annotation(old_g, annotation_uri, user.username):
        if not _is_moderator(request):
            raise SecurityError(("You do not have the required permission " \
                                 "to update the status of annotation %s" %
                                 annotation_uri))

    new_g = generate_graph(CharmeMiddleware.get_store(), new_graph)
    # Move the people
    for res in _get_people(old_g, annotation_uri):
        old_g.remove(res)
        new_g.add(res)
    # Copy the organization
    for res in _get_organization(old_g, annotation_uri):
        new_g.add(res)
    # Copy the software
    for res in _get_software(old_g, annotation_uri):
        new_g.add(res)
    # Move the annotation
    for res in old_g.triples((annotation_uri, None, None)):
        old_g.remove(res)
        # We are only allowed one annotatedAt per annotation
        if res[1] == URIRef(OA + 'annotatedAt'):
            continue
        new_g.add(res)

    # Add new prov data
    prov = _get_prov(annotation_uri, user, request.client)[0]
    for triple in prov:
        try:
            new_g.add(triple)
        except Exception as ex:
            raise ParseError(str(ex))

    # If provided add activity
    if activity_uri != None:
        new_g.add((annotation_uri, URIRef(PROV + 'wasInvalidatedBy'),
                   activity_uri))

    return new_g


def _validate_graph_name(graph_name):
    """
    Check that the graph name is valid.

    Args:
        graph_name (str): The graph name to validate
    """
    if graph_name in GRAPH_NAMES:
        return
    names = ''
    # prepare error message
    for name in GRAPH_NAMES:
        if names != '':
            names = names + ', '
        names = names + name
    raise UserError(("The status of %s is not valid. It must be one of %s" %
                     (graph_name, names)))


def _is_my_annotation(graph, annotation_uri, username):
    """
    Check to see if this annotation was edited by the user.

    Args:
        graph (rdflib.graph.Graph): The graph containing the annotation.
        annotation_uri (URIRef): The URI of the annotation.
        userername (str): The name of the user to check

    Returns:
        boolean True if the user is listed as an accountName in the annotatedBy
        Person object of the annotation.

    """
    for res in graph.triples((annotation_uri, URIRef(OA + 'annotatedBy'),
                              None)):
        for res2 in graph.triples((res[2], URIRef(FOAF + 'accountName'), None)):
            if str(res2[2]) == username:
                return True
    return False


def _is_moderator(request):
    """
    Check to see if this user is in the moderator group.

    Args:
        request (WSGIRequest): The incoming request.

    Returns:
        boolean True if the user is listed as a member of the moderator group.

    """
    groups = request.user.groups.values_list('name', flat=True)
    return "moderator" in groups


def _get_people(graph, annotation_uri):
    """
    Get the list of people associated with the annotation in the graph.

    Args:
        graph (rdflib.graph.Graph): The graph containing the annotation.
        annotation_uri (URIRef): The URI of the annotation.

    Returns:
        list[tuple] The list of people associated with the annotation.

    """
    people = []
    for res in graph.triples((annotation_uri, URIRef(OA + 'annotatedBy'),
                              None)):
        for res2 in graph.triples((res[2], URIRef(RDF + 'type'),
                                   URIRef(FOAF + 'Person'))):
            for res3 in graph.triples((res2[0], None, None)):
                people.append(res3)
    return people


def _get_organization(graph, annotation_uri):
    """
    Get the list of organizations associated with the annotation in the graph.

    Args:
        graph (rdflib.graph.Graph): The graph containing the annotation.
        annotation_uri (URIRef): The URI of the annotation.

    Returns:
        list[tuple] The list of organizations associated with the annotation.

    """
    organization = []
    for res in graph.triples((annotation_uri, URIRef(OA + 'annotatedBy'),
                              None)):
        for res2 in graph.triples((res[2], URIRef(RDF + 'type'),
                                   URIRef(FOAF + 'Organization'))):
            for res3 in graph.triples((res2[0], None, None)):
                organization.append(res3)
    return organization


def _get_software(graph, annotation_uri):
    """
    Get the list of software associated with the annotation in the graph.

    Args:
        graph (rdflib.graph.Graph): The graph containing the annotation.
        annotation_uri (URIRef): The URI of the annotation.

    Returns:
        list[tuple] The list of software associated with the annotation.

    """
    software = []
    for res in graph.triples((annotation_uri, URIRef(OA + 'serializedBy'),
                              None)):
        for res2 in graph.triples((res[2], URIRef(RDF + 'type'),
                                   URIRef(PROV + 'SoftwareAgent'))):
            for res3 in graph.triples((res2[0], None, None)):
                software.append(res3)
    return software


def find_annotation_graph(resource_id):
    """
    Find the graph that contains the given resource.

    Args:
        resource_id(str): The id of the resource.

    Returns:
        str The name of the graph or None.

    """
    triple = (_format_resource_uri_ref(resource_id), None, None)
    for graph in GRAPH_NAMES:
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
                                   "\n" + str(ex))
    except EndPointNotFound as ex:
        raise StoreConnectionError("Cannot open a connection with triple store"
                                   "\n" + str(ex))
    return tmp_g
