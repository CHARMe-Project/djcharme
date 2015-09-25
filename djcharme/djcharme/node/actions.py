'''
BSD Licence
Copyright (c) 2015, Science & Technology Facilities Council (STFC)
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
import base64
from datetime import datetime
import logging
from urllib2 import URLError
import uuid

from SPARQLWrapper.SPARQLExceptions import EndPointNotFound
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import ObjectDoesNotExist
from rdflib import BNode
from rdflib import Graph, URIRef, Literal
from rdflib.graph import ConjunctiveGraph

from djcharme.charme_middleware import CharmeMiddleware
from djcharme.exception import NotFoundError
from djcharme.exception import ParseError
from djcharme.exception import SecurityError
from djcharme.exception import StoreConnectionError
from djcharme.exception import UserError
from djcharme.node.constants import ANNO_URI, LOCALHOST_URI, TARGET_URI, \
    REPLACEMENT_URIS, REPLACEMENT_URIS_MULTIVALUED
from djcharme.node.constants import FOAF, RDF, PROV, OA, CH_NODE
from djcharme.node.constants import FORMAT_MAP, ALLOWED_CREATE_TARGET_TYPE, \
    RESOURCE
from djcharme.node.constants import GRAPH_NAMES, SUBMITTED, INVALID, RETIRED
from djcharme.node.model_queries import get_admin_email_addresses, \
    get_followers, get_organization_for_client, is_moderator, \
    is_organization_admin
from djcharme.node.triple_queries import extract_subject


LOGGING = logging.getLogger(__name__)
CREATED = 'created'

def rdf_format_from_mime(mimetype):
    """
    Get the RDF type based on the mime type.

    Args:
        mimetype (str): The mime type

    Return:
        a string containing the RDF type associated with the mime type.

    """
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


def get_vocab():
    """
        Returns a graph containing all the vocab triples
    """
    return generate_graph(CharmeMiddleware.get_store(), "vocab")


def report_to_moderator(request, resource_id):
    """
    Report this annotation to the moderator of the site where it was created.

    Args:
        request (WSGIRequest): The incoming request.
        resource_id(str): The id of the resource.

    """
    LOGGING.debug("report_to_moderator(request, %s)", resource_id)
    annotation_uri = format_resource_uri_ref(resource_id)
    graph_name = find_annotation_graph(annotation_uri)
    if graph_name == None:
        raise NotFoundError(("Annotation %s not found" % annotation_uri))
    graph = generate_graph(CharmeMiddleware.get_store(), graph_name)
    organizations = _get_organization(graph, annotation_uri)
    for res in organizations:
        if res[1] == (URIRef(FOAF + 'name')):
            organization_name = res[2]
            break
    email_addresses = get_admin_email_addresses(organization_name)

    # create message
    message = ('You are receiving this email as you are registered as an ' \
               'admin for %s by the CHARMe site %s\n\nThe annotation\n%s\n' \
               'has been flagged for moderation by ' % 
               (organization_name, getattr(settings, 'NODE_URI'),
                annotation_uri))
    if request.user.first_name != "":
        message = "%s%s " % (message, request.user.first_name)
    if request.user.last_name != "":
        message = "%s%s" % (message, request.user.last_name)
    if request.user.first_name == "" and request.user.last_name == "":
        message = "%suser: %s" % (message, request.user.username)
    if request.user.email != "":
        message = "%s, email: %s " % (message, request.user.email)

    # add reason for flagging annotation
    if request.body != "":
        message = "%s\n\nThe following reason was given:\n%s\n" % (message,
                                                                   request.body)

    # add signature
    message = '%s\n\nRegards\nThe CHARMe site team\n' % (message)

    # send mails
    from_address = getattr(settings, 'DEFAULT_FROM_EMAIL')
    for address in email_addresses:
        send_mail('An annotation has been flagged for moderation',
                  message, from_address, [address])
    return


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
    LOGGING.debug("insert_rdf(%s, %s, %s, client, graph, store)", data,
                  mimetype, user)
    try:
        return _insert_rdf(data, mimetype, user, client, graph, store)
    except ParseError as ex:
        raise ParseError(str(ex))
    except EndPointNotFound as ex:
        LOGGING.error("EndPointNotFound error while inserting triple. %s", ex)
        raise StoreConnectionError("Cannot insert triple. " + str(ex))


def _insert_rdf(data, mimetype, user, client, graph, store):
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
    if store is None:
        store = CharmeMiddleware.get_store()
    tmp_g = Graph()
    # Necessary as RDFlib does not contain the json-ld lib
    try:
        tmp_g.parse(data=data, format=mimetype)
    except SyntaxError as ex:
        try:
            LOGGING.info("Syntax error while parsing triple. %s", ex)
            raise ParseError(str(ex))
        except UnicodeDecodeError:
            raise ParseError(ex.__dict__["_why"])
    _format_submitted_annotation(tmp_g)
    final_g = generate_graph(store, graph)

    for nspace in tmp_g.namespaces():
        final_g.store.bind(str(nspace[0]), nspace[1])
    timestamp = Literal(datetime.utcnow())

    # add the person
    person_uri, triples = _create_person(user)
    for triple in triples:
        _add(final_g, triple)

    # add the rest
    anno_uri = ''
    targets = []
    for res in tmp_g:
        if (res[1] == URIRef(RDF + 'type')
            and res[2] == URIRef(OA + 'Annotation')):
            anno_uri = res[0]
            prov = _get_prov(anno_uri, person_uri, client, timestamp)
            for triple in prov:
                _add(final_g, triple)
        if res[1] == URIRef(OA + 'hasTarget'):
            targets.append(res[2])
        _add(final_g, res)
    if targets:
        _mail_followers(anno_uri, targets, CREATED)
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
    LOGGING.debug("modify_rdf(request, %s)", mimetype)
    try:
        return _modify_rdf(request, mimetype)
    except UserError as ex:
        raise UserError(str(ex))
    except ParseError as ex:
        raise ParseError(str(ex))
    except EndPointNotFound as ex:
        LOGGING.error("EndPointNotFound error while modifying triple. %s", ex)
        raise StoreConnectionError("Cannot insert triple. " + str(ex))


def _modify_rdf(request, mimetype):
    """
    Modify an annotation in the triplestore.

    Args:
        request (WSGIRequest): The http request
        mimetype (str): The document mimetype

    Return:
        a URIRef containing the URI of the modified annotation

    """
    modification_time = Literal(datetime.utcnow())
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

    activity_uri = URIRef((getattr(settings, 'NODE_URI', LOCALHOST_URI)
                  + '/%s/%s' % (RESOURCE, uuid.uuid4().hex)))
    # retire original
    if (_change_annotation_state(original_uri, RETIRED, request, activity_uri,
                                 modification_time) == None):
        raise UserError(("Current annotation status of %s is final. Data " \
                         "has not been updated." % RETIRED))

    _format_submitted_annotation(tmp_g)
    final_g = generate_graph(store, SUBMITTED)

    for nspace in tmp_g.namespaces():
        final_g.store.bind(str(nspace[0]), nspace[1])

    # add the person
    person_uri, triples = _create_person(request.user)
    for triple in triples:
        _add(final_g, triple)

    # add the rest
    anno_uri = ''
    targets = []
    for res in tmp_g:
        if (res[1] == URIRef(RDF + 'type')
            and res[2] == URIRef(OA + 'Annotation')):
            anno_uri = res[0]
            prov = _get_prov(anno_uri, person_uri, request.client,
                             modification_time)
            for triple in prov:
                _add(final_g, triple)
            modify_activity = _get_modify_activity(anno_uri, original_uri,
                                                   modification_time,
                                                   activity_uri, person_uri)
            for triple in modify_activity:
                _add(final_g, triple)
        if res[1] == URIRef(OA + 'hasTarget'):
            targets.append(res[2])
        _add(final_g, res)
    if targets:
        _mail_followers(anno_uri, targets, CREATED, original_uri)
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


def _get_prov(annotation_uri, person_uri, client, timestamp):
    """
    Get the provenance data for the annotation.

    Args:
        annotation_uri (URIRef): The URI of the annotation
        person_uri (URIRef): The URI of a person
        client (client): The Client object from a request
        timestamp (Literal(datetime)) The time the annotation was updated
    Returns:
        a list of triples

    """
    triples = []
    triples.append((annotation_uri, URIRef(OA + 'annotatedAt'),
                    timestamp))
    triples.append((annotation_uri, URIRef(OA + 'annotatedBy'), person_uri))
    organization = get_organization_for_client(client)
    if organization != None:
        triples.append((annotation_uri, URIRef(OA + 'annotatedBy'),
                        URIRef(client.url)))
        triples.append((URIRef(client.url), URIRef(RDF + 'type'),
                        URIRef(FOAF + 'Organization')))
        triples.append((URIRef(client.url), URIRef(FOAF + 'name'),
                        Literal(organization)))

    return triples


def _create_person(user):
    """
    Create a persons triples.

    Args:
        user (User): The user details.
    Returns:
        a URIRef containing the person URI
        a list of triples

    """
    person_uri = URIRef((getattr(settings, 'NODE_URI', LOCALHOST_URI)
                  + '/%s/%s' % (RESOURCE, uuid.uuid4().hex)))
    triples = []
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

    return (person_uri, triples)



def _get_modify_activity(annotation_uri, original_anno_uri, timestamp,
                     activity_uri, person_uri):
    """
    Get the triples for a modify activity.

    Args:
        annotation_uri (URIRef): The URI of the annotation
        original_anno_uri (URIRef): The uri of the original annotation.
        timestamp (Literal): The time of the activity
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

    triples.append((activity_uri, URIRef(PROV + 'wasStartedAt'), timestamp))
    triples.append((activity_uri, URIRef(PROV + 'wasStartedBy'), person_uri))
    triples.append((activity_uri, URIRef(PROV + 'wasEndedAt'), timestamp))
    triples.append((activity_uri, URIRef(PROV + 'wasEndedBy'), person_uri))
    return triples


def _get_deleted_activity(annotation_uri, timestamp, activity_uri, person_uri):
    """
    Get the triples for a delete activity.

    Args:
        annotation_uri (URIRef): The uri of the annotation.
        timestamp (Literal): The time of the activity
        activity_uri (URIRef): The URI of the Activity
        person_uri (URIRef): The URI of the person

    Returns:
        a list of triples.

    """
    triples = []
    triples.append((activity_uri, URIRef(RDF + 'type'),
                    URIRef(PROV + 'Activity')))
    triples.append((activity_uri, URIRef(PROV + 'invalidated'),
                    URIRef(annotation_uri)))
    triples.append((activity_uri, URIRef(PROV + 'wasStartedAt'), timestamp))
    triples.append((activity_uri, URIRef(PROV + 'wasStartedBy'), person_uri))
    triples.append((activity_uri, URIRef(PROV + 'wasEndedAt'), timestamp))
    triples.append((activity_uri, URIRef(PROV + 'wasEndedBy'), person_uri))
    return triples


def format_resource_uri_ref(resource_id):
    '''
        Returns the URIRef associated with the id for this specific node
    '''
    if resource_id.startswith('http:') or resource_id.startswith('https:'):
        return URIRef(resource_id)
    return URIRef('%s/%s/%s' % (getattr(settings, 'NODE_URI', LOCALHOST_URI),
                                RESOURCE, resource_id))


def _format_node_uri_ref(uriref, generated_uris):
    '''
        Rewrite a URIRef according to the node configuration
        * uriref:rdflib.URIRef
        * generated_uris:dict of generated URIs
    '''
    if isinstance(uriref, URIRef) and LOCALHOST_URI in uriref:
        uriref = URIRef(uriref.replace(LOCALHOST_URI,
                                       getattr(settings, 'NODE_URI', LOCALHOST_URI)
                                       + '/'))

    if isinstance(uriref, URIRef) and CH_NODE in uriref:
        uriref = URIRef(uriref.replace(CH_NODE + ':',
                                       getattr(settings, 'NODE_URI', LOCALHOST_URI)
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
    graph = _validate_submitted_annotation(graph)
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
                bits = obj.split(CH_NODE + ':')
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


def _validate_submitted_annotation(graph):
    """
    Validate the graph.

    Args:
        graph (rdflib.graph.Graph): The graph containing an annotation.

    Returns:
        graph (rdflib.graph.Graph): The validated graph.
    """
    local_resource = getattr(settings, 'NODE_URI', LOCALHOST_URI) + '/'
    for subject, _, _ in graph:
        if local_resource in subject:
            LOGGING.info("UserError Found %s in the subject of submitted " \
                         "annotation)", subject)
            raise UserError(str(subject) + " is not allowed as the subject " \
                            "of a triple")
    return graph


def change_annotation_state(annotation_uri, new_graph, request):
    """
    Advance the status of an annotation.

    Args:
        annotation_uri (URIRef): The URI of the annotation.
        new_graph (str): The name of the graph/state to move the annotation to.
        request (WSGIRequest): The incoming request.

    Returns:
        graph (rdflib.graph.Graph): The new graph containing the updated
        annotation.

    """
    LOGGING.debug("change_annotation_state(%s, %s, request)",
                  annotation_uri, new_graph)
    annotation_uri = format_resource_uri_ref(annotation_uri)
    activity_uri = URIRef((getattr(settings, 'NODE_URI', LOCALHOST_URI)
                           + '/%s/%s' % (RESOURCE, uuid.uuid4().hex)))
    timestamp = Literal(datetime.utcnow())
    new_g = _change_annotation_state(annotation_uri, new_graph, request,
                                     activity_uri, timestamp, True)
    if new_g == None:
        return

    # add the person
    person_uri, triples = _create_person(request.user)
    for triple in triples:
        try:
            _add(new_g, triple)
        except EndPointNotFound as ex:
            raise StoreConnectionError("Cannot insert triple. " + str(ex))

    # If we are retiring include extra metadata
    if new_graph == INVALID or new_graph == RETIRED:
        deleted_prov = _get_deleted_activity(annotation_uri, timestamp,
                                         activity_uri, person_uri)
        for triple in deleted_prov:
            _add(new_g, triple)

    # TODO add extra prov for change to submitted
    # TODO add extra prov for change to stable
    return new_g


def _change_annotation_state(annotation_uri, new_graph, request, activity_uri,
                             timestamp, delete_body_target=False):
    """
    Advance the status of an annotation.

    Args:
        annotation_uri (URIRef): The URI of the annotation.
        new_graph (str): The name of the graph/state to move the annotation to.
        request (WSGIRequest): The incoming request.
        activity_uri (URIRef): The uri of the Activity
        timestamp (Literal): The time of the change
        delete_body_target (boolean): Physically delete the target if the
        annotation is moved to the retired or invalid graph

    Returns:
        graph (rdflib.graph.Graph): The new graph containing the updated
        annotation.

    """
    # lets do some initial validation
    annotation_uri = format_resource_uri_ref(annotation_uri)
    validate_graph_name(new_graph)
    old_graph = find_annotation_graph(annotation_uri)
    if old_graph == None:
        raise NotFoundError(("Annotation %s not found" % annotation_uri))
    if old_graph == new_graph:
        return None
    if old_graph == INVALID or old_graph == RETIRED:
        raise UserError(("Current annotation status of %s is final. Status " \
                         "has not been updated." % old_graph))
    if new_graph == INVALID or new_graph == RETIRED:
        # we must do this before we move the annotation
        if delete_body_target:
            _delete_target(annotation_uri, old_graph, request)
            _delete_body(annotation_uri, old_graph, request)
    new_g = _move_annotation(annotation_uri, new_graph, old_graph, request,
                             timestamp)
    if new_graph == INVALID or new_graph == RETIRED:
        _add(new_g, (annotation_uri, URIRef(PROV + 'wasInvalidatedBy'),
                     activity_uri))
    return new_g


def validate_graph_name(graph_name):
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


def _move_annotation(annotation_uri, new_graph, old_graph, request, timestamp):
    """
    Move an annotation from one graph to another.

    Args:
        annotation_uri (URIRef): The URI of the annotation.
        new_graph (str): The name of the graph to move the annotation to.
        old_graph (str): The name of the graph to move the annotation from.
        request (WSGIRequest): The incoming request.
        timestamp (Literal): The time of the move

    Returns:
        graph (rdflib.graph.Graph): The new graph containing the updated
        annotation.

    """
    # First check permissions
    old_g = generate_graph(CharmeMiddleware.get_store(), old_graph)
    if not is_update_allowed(old_g, annotation_uri, request):
        raise SecurityError(("You do not have the required permission to " \
                             "update the status of annotation %s" % 
                             annotation_uri))

    new_g = generate_graph(CharmeMiddleware.get_store(), new_graph)
    # Move the people
    for res in _get_people(old_g, annotation_uri):
        _remove(old_g, res)
        _add(new_g, res)
    # Copy the organization
    for res in _get_organization(old_g, annotation_uri):
        _add(new_g, res)
    # Copy the software
    for res in _get_software(old_g, annotation_uri):
        _add(new_g, res)
    # Move the annotation
    targets = []
    for res in old_g.triples((annotation_uri, None, None)):
        _remove(old_g, res)
        # We are only allowed one annotatedAt per annotation
        if res[1] == URIRef(OA + 'annotatedAt'):
            continue
        if res[1] == URIRef(OA + 'hasTarget'):
            targets.append(res[2])
        _add(new_g, res)
    # Add new annotatedAt
    _add(new_g, ((annotation_uri, URIRef(OA + 'annotatedAt'), timestamp)))
    
    if targets:
        if new_graph == RETIRED:
            message = "marked as deleted"
        else:
            message = "marked as %s" % new_graph

        _mail_followers(annotation_uri, targets, message)

    return new_g


def _delete_body(annotation_uri, graph_name, request):
    """
    Delete the bodies associated with an annotation if they are no longer
    referenced and they have external URIs.

    Args:
        annotation_uri (URIRef): The URI of the annotation.
        graph_name (str): The name of the graph to move the annotation from.
        request (WSGIRequest): The incoming request.

    """
    # First check permissions
    graph = generate_graph(CharmeMiddleware.get_store(), graph_name)
    if not is_update_allowed(graph, annotation_uri, request):
        raise SecurityError(("You do not have the required permission to " \
                             "update the status of annotation %s" % 
                             annotation_uri))

    # Find all of the targets
    for res in graph.triples((annotation_uri, OA['hasBody'], None)):
        # If this is the only reference to the body then delete it
        count = 0
        for _ in graph.triples((None, None, res[2])):
            count = count + 1
        if count > 1:
            continue
        node_uri = getattr(settings, 'NODE_URI', LOCALHOST_URI)
        for body in  graph.triples((res[2], None, None)):
            if node_uri in body[0]:
                continue
            LOGGING.debug("permanently deleting body %s", body)
            _remove(graph, body)


def _delete_target(annotation_uri, graph_name, request):
    """
    Delete the targets associated with an annotation if they are no longer
    referenced and they have external URIs.

    Args:
        annotation_uri (URIRef): The URI of the annotation.
        graph_name (str): The name of the graph to move the annotation from.
        request (WSGIRequest): The incoming request.

    """
    # First check permissions
    graph = generate_graph(CharmeMiddleware.get_store(), graph_name)
    if not is_update_allowed(graph, annotation_uri, request):
        raise SecurityError(("You do not have the required permission to " \
                             "update the status of annotation %s" % 
                             annotation_uri))

    # Find all of the targets
    for res in graph.triples((annotation_uri, OA['hasTarget'], None)):
        # If this is the only reference to the target then delete it
        count = 0
        for _ in graph.triples((None, None, res[2])):
            count = count + 1
        if count > 1:
            continue
        node_uri = getattr(settings, 'NODE_URI', LOCALHOST_URI)
        for target in  graph.triples((res[2], None, None)):
            if node_uri in target[0]:
                continue
            LOGGING.debug("permanently deleting target %s", target)
            _remove(graph, target)


def is_update_allowed(graph, annotation_uri, request):
    """
    Check if this user is allowed to update this annotation.

    Args:
        graph (rdflib.graph.Graph): The graph containing the annotation.
        annotation_uri (URIRef): The URI of the annotation.
        request (WSGIRequest): The incoming request.

    Returns:
        boolean True if the user is allowed to update this annotation.

    """
    if _is_my_annotation(graph, annotation_uri, request.user.username):
        return True
    try:
        if is_organization_admin(request.client, request.user, annotation_uri):
            return True
    except AttributeError:
        # there is no request.client
        pass
    if is_moderator(request.user):
        return True

    return False


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
                LOGGING.debug("User %s is the owner of this annotation %s",
                              username, annotation_uri)
                return True
    return False


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


def _mail_followers(annotation_uri, targets, message_part, original_uri=None):
    """
    Mail the followers of the targets and annotation.

    Args:
        annotation_uri (str): The URI of the annotation.
        targets (list(str)): The list of URIs of targets.
        message_part (str): The action on the annotation.
        original_uri (str): The URI of the original annotation, may be None.

    """
    followers = get_followers(targets)
    from_address = getattr(settings, 'DEFAULT_FROM_EMAIL')
    subject = 'An annotation has been %s' % message_part

    for follower in followers:
        # create message
        message = ('You are receiving this email as you are registered as ' \
                   'following %s by the CHARMe site %s\n\nThe annotation ' \
                   '%s, which references %s, has been %s.\n\nYou can ' \
                   'update your notification settings by logging on to %s' \
                   '\n\nRegards\nThe CHARMe site team\n' % 
                   (follower.resource, getattr(settings, 'NODE_URI'),
                    annotation_uri, follower.resource, message_part,
                    getattr(settings, 'NODE_URI')))
        if original_uri:
            message = ('%s This is a modification of the annotation %s' % 
                       (message, original_uri))
        message = ('%s\n\nYou can update your notification settings by ' \
                   'logging on to %s\n\nRegards\nThe CHARMe site team\n' % 
                   (message, getattr(settings, 'NODE_URI')))        
        # send mails
        try:
            send_mail(subject, message, from_address, [follower.user.email])
        except Exception as ex:
            LOGGING.error("An error occurred when emailing user %s, %s" % 
                          (follower.user, ex))
    
    if message_part == CREATED:
        # The annotation is being created so there will be no followers
        return
    followers = get_followers([annotation_uri])
    for follower in followers:
        # create message
        message = ('You are receiving this email as you are registered as ' \
                   'following %s by the CHARMe site %s\n\nThis annotation ' \
                   'has been %s.You can update your notification settings ' \
                   'by logging on to %s\n\nRegards\nThe CHARMe site team\n' \
                   % (follower.resource, getattr(settings, 'NODE_URI'),
                      annotation_uri, follower.resource, message_part,
                      getattr(settings, 'NODE_URI')))
        # send mails
        try:
            send_mail(subject, message, from_address, [follower.user.email])
        except Exception as ex:
            LOGGING.error("An error occurred when emailing user %s, %s" % 
                          (follower.user, ex))
    return


def find_annotation_graph(resource_id):
    """
    Find the graph that contains the given resource.

    Args:
        resource_id(str): The id of the resource.

    Returns:
        str The name of the graph or None.

    """
    triple = (format_resource_uri_ref(resource_id), None, None)
    for graph in GRAPH_NAMES:
        new_g = generate_graph(CharmeMiddleware.get_store(), graph)
        if triple in new_g:
            return graph


def find_resource_by_id(resource_id, depth=1):
    '''
        Returns the charme resource associated with the given resource_id
        * resource_id:String
        * return: an rdflib.Graph object
    '''
    graph = ConjunctiveGraph(store=CharmeMiddleware.get_store())
    uri_ref = format_resource_uri_ref(resource_id)
    LOGGING.debug("Looking for resource %s", uri_ref)
    return extract_subject(graph, uri_ref, depth)


def resource_exists(resource_id):
    """
    Check that the resource exists in the triple store.

    Args:
        resource_id(str): The id of the resource.

    Returns:
        True if the resource exists.

    """
    graph = find_resource_by_id(resource_id)
    if len(graph) > 0:
        return True
    return False


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


def collect_annotations(graph_name):
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


def _add(graph, spo):
    """
    Add a triple to the graph.

    """
    if getattr(settings, 'STRABON', False):
        _add_strabon(spo, graph)
    else:
        graph.add(spo)


def _add_strabon(spo, context=None):
    """
    Add a triple to the store of triples.

    This is an upated version of the add method from sparqlstore for use with
    strabon.

    """
    from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
    sparqlstore = SPARQLUpdateStore(queryEndpoint=getattr(settings,
                                                          'SPARQL_QUERY'),
                                    update_endpoint=getattr(settings,
                                                            'SPARQL_UPDATE'),
                                    postAsEncoded=False)
    sparqlstore.bind("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
    sparqlstore.bind("oa", "http://www.w3.org/ns/oa#")
    sparqlstore.bind("chnode", getattr(settings, 'NODE_URI',
                                       'http://localhost'))

    sparqlstore.headers["Content-type"] = "application/x-www-form-urlencoded"
    credentials = "%s:%s" % (getattr(settings, 'SPARQL_USERNAME'),
                                     getattr(settings, 'SPARQL_PASSWORD'))
    credentials64 = base64.encodestring(credentials.encode('utf-8'))
    sparqlstore.headers["Authorization"] = ("Basic %s" % credentials64)

    if not sparqlstore.connection:
        raise "UpdateEndpoint is not set - call 'open'"

    (subject, predicate, obj) = spo
    if (isinstance(subject, BNode) or
        isinstance(predicate, BNode) or
        isinstance(obj, BNode)):
        raise Exception("SPARQLStore does not support Bnodes! See " \
                        "http://www.w3.org/TR/sparql11-query/#BGPsparqlBNodes")

    triple = "%s %s %s " % (subject.n3(), predicate.n3(), obj.n3())
    if context is not None:
        q = "INSERT DATA { GRAPH %s { %s } } }}" % (
            context.identifier.n3(), triple)
    else:
        q = "INSERT DATA { %s } }}" % triple
    q = 'view=HTML&format=HTML&handle=plain&submit=Update&query=%s' % q
    r = sparqlstore._do_update(q)
    content = r.read()  # we expect no content
    if r.status not in (200, 204):
        sparqlstore.close()
        raise Exception("Could not update: %d %s\n%s" % (
            r.status, r.reason, content))
    sparqlstore.close()


def _remove(graph, spo):
    """
    Remove a triple from the graph.

    """
#     graph.remove(spo)
    if getattr(settings, 'STRABON', False):
        _remove_strabon(spo, graph)
    else:
        graph.remove(spo)


def _remove_strabon(spo, context):
    """
    Remove a triple from the store.

    This is an upated version of the remove method from sparqlstore for use with
    strabon.

    """
    from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
    from rdflib import Variable
    sparqlstore = SPARQLUpdateStore(queryEndpoint=getattr(settings,
                                                          'SPARQL_QUERY'),
                                    update_endpoint=getattr(settings,
                                                            'SPARQL_UPDATE'),
                                    postAsEncoded=False)
    sparqlstore.bind("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
    sparqlstore.bind("oa", "http://www.w3.org/ns/oa#")
    sparqlstore.bind("chnode", getattr(settings, 'NODE_URI',
                                       'http://localhost'))

    sparqlstore.headers["Content-type"] = "application/x-www-form-urlencoded"
    credentials = "%s:%s" % (getattr(settings, 'SPARQL_USERNAME'),
                                     getattr(settings, 'SPARQL_PASSWORD'))
    credentials64 = base64.encodestring(credentials.encode('utf-8'))
    sparqlstore.headers["Authorization"] = ("Basic %s" % credentials64)

    if not sparqlstore.connection:
        raise "UpdateEndpoint is not set - call 'open'"

    (subject, predicate, obj) = spo
    if not subject:
        subject = Variable("S")
    if not predicate:
        predicate = Variable("P")
    if not obj:
        obj = Variable("O")

    triple = "%s %s %s ." % (subject.n3(), predicate.n3(), obj.n3())
    if context is not None:
        q = "DELETE { GRAPH %s { %s } } WHERE { GRAPH %s { %s } } }}" % (
            context.identifier.n3(), triple,
            context.identifier.n3(), triple)
    else:
        q = "DELETE { %s } WHERE { %s } }}" % (triple, triple)
    q = 'view=HTML&format=HTML&handle=plain&submit=Update&query=%s' % q
    r = sparqlstore._do_update(q)
    content = r.read()  # we expect no content
    if r.status not in (200, 204):
        raise Exception("Could not update: %d %s\n%s" % (
            r.status, r.reason, content))
    sparqlstore.close()

