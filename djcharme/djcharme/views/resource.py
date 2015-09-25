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

'''
import datetime
import logging

from django.forms.fields import CharField
from django.forms.forms import Form
from django.http.response import HttpResponseRedirect

from djcharme import mm_render_to_response
from djcharme.node.actions import change_annotation_state, is_update_allowed, \
    find_annotation_graph
from djcharme.node.constants import  CITO, CONTENT, DC, DCTERMS, FOAF, \
    INVALID, OA, PROV, RDF, RETIRED, SKOS


LOGGING = logging.getLogger(__name__)

def annotation(request, resource_uri=None, graph=None):
    LOGGING.debug('Annotation request received')
    context = {}

    if request.method == 'POST':
        LOGGING.debug('method is POST')
        return _delete(request)
    else:  # GET
        context['uri'] = resource_uri

        triples = graph.triples((resource_uri, PROV['wasInvalidatedBy'], None))
        for triple in triples:
            context['wasInvalidatedBy'] = triple[2]

        triples = graph.triples((resource_uri, PROV['wasGeneratedBy'], None))
        for triple in triples:
            context['wasGeneratedBy'] = triple[2]

        triples = graph.triples((resource_uri, PROV['wasRevisionOf'], None))
        for triple in triples:
            context['wasRevisionOf'] = triple[2]

        triples = graph.triples((None, DCTERMS['title'], None))
        for triple in triples:
            context['title'] = triple[2]

        triples = graph.triples((resource_uri, OA['annotatedAt'], None))
        for triple in triples:
            ann_at = datetime.datetime.strptime(triple[2],
                                                "%Y-%m-%dT%H:%M:%S.%f")
            ann_at = ann_at.strftime("%H:%M %d %b %Y")
            context['annotated_at'] = ann_at

        triples = graph.triples((resource_uri, OA['annotatedBy'], None))
        for triple in triples:
            prov_triples = graph.triples((triple[2], FOAF['name'], None))
            for a_triple in prov_triples:
                context['organization_name'] = a_triple[2]
                context['organization_uri'] = a_triple[0]

        triples = graph.triples((resource_uri, OA['serializedBy'], None))
        for triple in triples:
            prov_triples = graph.triples((triple[2], FOAF['name'], None))
            for a_triple in prov_triples:
                context['agent_name'] = a_triple[2]
                context['agent_uri'] = a_triple[0]

        triples = graph.triples((resource_uri, OA['serializedAt'], None))
        for triple in triples:
            ann_at = datetime.datetime.strptime(triple[2],
                                                "%Y-%m-%dT%H:%M:%S.%f")
            ann_at = ann_at.strftime("%H:%M %d %b %Y")
            context['serialized_at'] = ann_at

        triples = graph.triples((resource_uri, OA['motivatedBy'], None))
        motivations = []
        for triple in triples:
            motivations.append(triple[2])
        context['motivations'] = motivations

        # person
        triples = graph.triples((None, RDF['type'], FOAF['Person']))
        for triple in triples:
            context['person'] = triple[0]

        triples = graph.triples((None, FOAF['givenName'], None))
        for triple in triples:
            context['first_name'] = triple[2]

        triples = graph.triples((None, FOAF['familyName'], None))
        for triple in triples:
            context['last_name'] = triple[2]

        triples = graph.triples((None, FOAF['mbox'], None))
        for triple in triples:
            context['email'] = triple[2]

        triples = graph.triples((None, FOAF['accountName'], None))
        for triple in triples:
            context['username'] = triple[2]

        # body
        triples = graph.triples((resource_uri, OA['hasBody'], None))
        bodies = []
        for triple in triples:
            body_triples = graph.triples((triple[2], RDF['type'], None))
            types = []
            for b_triple in body_triples:
                types.append(b_triple[2])
            body_triples = graph.triples((triple[2], CONTENT['chars'], None))
            text = []
            for b_triple in body_triples:
                text.append(b_triple[2])
            bodies.append((triple[2], types, text))
        context['bodies'] = bodies

        # target
        triples = graph.triples((resource_uri, OA['hasTarget'], None))
        targets = []
        for triple in triples:
            target_triples = graph.triples((triple[2], RDF['type'], None))
            types = []
            for t_triple in target_triples:
                types.append(t_triple[2])
            target_triples = graph.triples((triple[2], CONTENT['chars'], None))
            text = []
            for t_triple in target_triples:
                text.append(t_triple[2])
            targets.append((triple[2], types, text))
        context['targets'] = targets

        # citation
        triples = graph.triples((None, CITO['hasCitingEntity'], None))
        for triple in triples:
            context['citing_entity'] = triple[2]

        triples = graph.triples((None, CITO['hasCitedEntity'], None))
        for triple in triples:
            context['cited_entity'] = triple[2]

        triples = graph.triples((None, CITO['hasCitationCharacterization'],
                                 None))
        for triple in triples:
            context['citation_characterization'] = triple[2]

        # delete button
        context['delete'] = False

        # message
        if request.user.username == None or request.user.username == '':
            context['message'] = 'If you are the author of this annotation, ' \
                'or a moderator for %s, you may delete this annotation by ' \
                'logging in' % context['organization_name']
        else:
            # delete button
            graph_name = find_annotation_graph(resource_uri)
            update_allowed = is_update_allowed(graph, resource_uri, request)
            if (graph_name != INVALID and graph_name != RETIRED
                and update_allowed):
                context['delete'] = True

        orig_values = {}
        orig_values['resource_uri'] = resource_uri
        resource_form = ResourceForm(initial=orig_values)
        context['resource_form'] = resource_form

        return mm_render_to_response(request, context, 'resources/annotation.html')


def annotation_index(request, tmp_g, graph_name):
    LOGGING.debug('Annotation index request received')
    context = {}
    context['graph_name'] = graph_name

    annotations = []
    for subject, _, _ in tmp_g.triples((None, None, OA['Annotation'])):
        annotations.append(subject)
    context['annotations'] = annotations
    return mm_render_to_response(request, context, 'index.html')


def activity(request, resource_uri, graph):
    LOGGING.debug('Activity request received')
    context = {}

    context['uri'] = resource_uri

    triples = graph.triples((resource_uri, PROV['invalidated'], None))
    for triple in triples:
        context['invalidated'] = triple[2]

    triples = graph.triples((resource_uri, PROV['generated'], None))
    for triple in triples:
        context['generated'] = triple[2]

    triples = graph.triples((resource_uri, PROV['wasEndedAt'], None))
    for triple in triples:
            at = datetime.datetime.strptime(triple[2], "%Y-%m-%dT%H:%M:%S.%f")
            at = at.strftime("%H:%M %d %b %Y")
            context['wasEndedAt'] = at

    triples = graph.triples((resource_uri, PROV['wasEndedBy'], None))
    for triple in triples:
        activity_triples = graph.triples((triple[2], FOAF['givenName'], None))
        for a_triple in activity_triples:
            context['first_name'] = a_triple[2]

        activity_triples = graph.triples((triple[2], FOAF['familyName'], None))
        for a_triple in activity_triples:
            context['last_name'] = a_triple[2]

        activity_triples = graph.triples((triple[2], FOAF['mbox'], None))
        for a_triple in activity_triples:
            context['email'] = a_triple[2]

    return mm_render_to_response(request, context, 'resources/activity.html')


def agent(request, resource_uri, graph):
    LOGGING.debug('Agent request received')
    context = {}

    context['uri'] = resource_uri

    triples = graph.triples((resource_uri, FOAF['name'], None))
    for triple in triples:
        context['name'] = triple[2]

    return mm_render_to_response(request, context, 'resources/agent.html')


def composite(request, resource_uri, graph):
    LOGGING.debug('Composite request received')
    context = {}

    context['uri'] = resource_uri

    triples = graph.triples((resource_uri, OA['item'], None))
    items = []
    for triple in triples:
        items.append(triple[2])
    context['items'] = items

    return mm_render_to_response(request, context, 'resources/composite.html')


def person(request, resource_uri, graph):
    LOGGING.debug('Person request received')
    context = {}

    context['uri'] = resource_uri

    triples = graph.triples((resource_uri, FOAF['givenName'], None))
    for triple in triples:
        context['first_name'] = triple[2]

    triples = graph.triples((resource_uri, FOAF['familyName'], None))
    for triple in triples:
        context['last_name'] = triple[2]

    triples = graph.triples((resource_uri, FOAF['mbox'], None))
    for triple in triples:
        context['email'] = triple[2]

    triples = graph.triples((None, FOAF['accountName'], None))
    for triple in triples:
        context['username'] = triple[2]

    return mm_render_to_response(request, context, 'resources/person.html')


def resource(request, resource_uri, graph):
    LOGGING.debug('Resource request received')
    context = {}

    context['uri'] = resource_uri

    triples = graph.triples((resource_uri, RDF['type'], None))
    types = []
    for triple in triples:
        types.append(triple[2])
    context['types'] = types

    triples = graph.triples((resource_uri, DC['format'], None))
    for triple in triples:
        context['format'] = triple[2]

    triples = graph.triples((resource_uri, CONTENT['chars'], None))
    text = []
    for triple in triples:
        text.append(triple[2])
    context['text'] = text

    triples = graph.triples((resource_uri, SKOS['prefLabel'], None))
    tags = []
    for triple in triples:
        tags.append(triple[2])
    context['tags'] = tags

    return mm_render_to_response(request, context, 'resources/resource.html')


def _delete(request):
    LOGGING.debug('Annotation delete request received')
    resource_uri = request.POST['resource_uri']
    change_annotation_state(resource_uri, RETIRED, request)
    return HttpResponseRedirect(resource_uri)


class ResourceForm(Form):
    resource_uri = CharField(max_length=100, required=True)


