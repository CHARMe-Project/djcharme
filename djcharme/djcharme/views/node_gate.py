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

Created on 14 May 2013

@author: mnagni
'''
import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseBadRequest, \
    HttpResponseRedirectBase, HttpResponse, HttpResponseNotFound, \
    HttpResponseForbidden, HttpResponseNotAllowed, HttpResponseServerError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View

from djcharme import mm_render_to_response_error, \
    __version__
from djcharme.exception import NotFoundError
from djcharme.exception import ParseError
from djcharme.exception import SecurityError
from djcharme.exception import StoreConnectionError
from djcharme.exception import UserError
from djcharme.models import FollowedResource
from djcharme.node import is_following_resource, resource_exists
from djcharme.node.actions import collect_annotations, find_resource_by_id, \
    format_resource_uri_ref, change_annotation_state, get_vocab, \
    report_to_moderator, validate_graph_name
from djcharme.node.actions import insert_rdf, modify_rdf
from djcharme.node.constants import OA, FOAF, PROV, RDF, FORMAT_MAP, \
    CONTENT_HTML, CONTENT_JSON, CONTENT_RDF, CONTENT_TEXT, DATA, FOLLOWING, \
    PAGE, SUBMITTED, RETIRED
from djcharme.views import isPOST, isOPTIONS, \
    validate_mime_format, http_accept, get_depth, content_type, \
    check_mime_format, get_format
from djcharme.views.resource import agent, annotation, annotation_index, \
    activity, composite, person, resource


LOGGING = logging.getLogger(__name__)


class HttpResponseCreated(HttpResponse):
    """
    Implements a simple HTTP 201 response.
    """
    status_code = 201


class HttpResponseNoContent(HttpResponse):
    """
    Implements a simple HTTP 204 response.
    """
    status_code = 204


class HttpResponseSeeOther(HttpResponseRedirectBase):
    """
    Implements a simple HTTP 303 response.
    """
    status_code = 303



class HttpResponseNotAcceptable(HttpResponse):
    """
    Implements a simple HTTP 406 response.
    """        
    status_code = 406


class HttpResponseUnsupportedMediaType(HttpResponse):
    """
    Implements a simple HTTP 415 response.
    """        
    status_code = 415


def __serialize(graph, req_format=CONTENT_RDF):
    '''
        Serializes a graph according to the required format
        - rdflib:Graph **graph** the graph to serialize
        - string **req_format** the serialization format
        - **return** the serialized graph
    '''
    if req_format == FORMAT_MAP['json-ld']:
        req_format = 'json-ld'

    return graph.serialize(format=req_format)


def index(request, graph='submitted'):
    """
    Returns a tabular view of the stored annotations.
    - HTTPRequest **request** the client request
    - string **graph**  the required named graph
    TODO: In a future implementation this actions should be supported by an
    OpenSearch implementation

    """
    try:
        validate_graph_name(graph)
    except UserError as ex:
        if CONTENT_HTML in http_accept(request):
            messages.add_message(request, messages.ERROR, str(ex))
            return mm_render_to_response_error(request, '400.html', 400)
        else:
            return HttpResponseBadRequest(str(ex))
    tmp_g = None
    try:
        tmp_g = collect_annotations(graph)
    except StoreConnectionError as ex:
        LOGGING.error("index - unexpected error: %s", ex)
        if CONTENT_HTML in http_accept(request):
            messages.add_message(request, messages.ERROR, str(ex))
            return mm_render_to_response_error(request, '500.html', 500)
        else:
            return HttpResponseServerError(str(ex))

    req_format = validate_mime_format(request)
    if req_format is not None:
        return HttpResponse(__serialize(tmp_g, req_format=req_format))
    elif CONTENT_HTML in http_accept(request):
        return annotation_index(request, tmp_g, graph)

    return HttpResponseNotAcceptable('Format not accepted')


@csrf_exempt
def insert(request):
    """
    Inserts in the triplestore a new annotation under the "SUBMITTED" graph

    """
    try:
        return _insert(request)
    except UserError as ex:
        return HttpResponseBadRequest(str(ex))
    except Exception as ex:
        LOGGING.error("insert - unexpected error: %s", ex)
        return HttpResponseServerError(str(ex))


def _insert(request):
    """
    Inserts in the triplestore a new annotation under the "SUBMITTED" graph

    """
    request_format = check_mime_format(content_type(request))

    if request_format is None:
        return HttpResponseUnsupportedMediaType("Cannot ingest the posted format")

    if isPOST(request) or isOPTIONS(request):
        triples = request.body
        try:
            anno_uri = insert_rdf(triples, request_format, request.user,
                                  request.client, graph=SUBMITTED)
        except ParseError as ex:
            LOGGING.debug("insert parsing error: %s", str(ex))
            return HttpResponseBadRequest(str(ex))
        except StoreConnectionError as ex:
            LOGGING.error("insert - unexpected error: %s", ex)
            return HttpResponseServerError(str(ex))

        response = HttpResponseCreated(anno_uri, content_type=CONTENT_TEXT)
        response['Location'] = anno_uri
        return response
    
    return HttpResponseNotAllowed(["POST", "OPTIONS"],
                                  content='Only POST and OPTION methods are allowed')


@csrf_exempt
def modify(request):
    """
    Modify the annotation contained in the request.

    Args:
        request (WSGIRequest): The request from the user

    """
    try:
        return _modify(request)
    except NotFoundError as ex:
        return HttpResponseNotFound('Resource does not exist on this system')
    except SecurityError as ex:
        return HttpResponseForbidden(str(ex))
    except UserError as ex:
        return HttpResponseBadRequest(str(ex))
    except Exception as ex:
        LOGGING.error("modify - unexpected error: %s", str(ex))
        return HttpResponseServerError(str(ex))


def _modify(request):
    """
    Modify the annotation contained in the request.

    Args:
        request (WSGIRequest): The request from the user

    """
    request_format = check_mime_format(content_type(request))

    if request_format is None:
        return HttpResponseUnsupportedMediaType("Cannot ingest the posted format")

    if isPOST(request) or isOPTIONS(request):
        try:
            anno_uri = modify_rdf(request, request_format)
        except ParseError as ex:
            LOGGING.debug("modify parsing error: %s", str(ex))
            return HttpResponseBadRequest(str(ex))
        except StoreConnectionError as ex:
            LOGGING.error("modify - unexpected error: %s", str(ex))
            return HttpResponseServerError(str(ex))
        response = HttpResponseCreated(anno_uri, content_type=CONTENT_TEXT)
        response['Location'] = anno_uri
        return response

    return HttpResponseNotAllowed(["POST", "OPTIONS"],
                                  content='Only POST and OPTION methods are allowed')


@csrf_exempt
def advance_status(request):
    '''
        Advance the status of an annotation
    '''
    try:
        return _advance_status(request)
    except NotFoundError as ex:
        return HttpResponseNotFound('Resource does not exist on this system')
    except SecurityError as ex:
        return HttpResponseForbidden(str(ex))
    except UserError as ex:
        return HttpResponseBadRequest(str(ex))
    except Exception as ex:
        LOGGING.error("advance_status - unexpected error: %s", str(ex))
        return HttpResponseServerError(str(ex))


def _advance_status(request):
    '''
        Advance the status of an annotation
    '''
    if isPOST(request) and (CONTENT_JSON in content_type(request) or
                            'application/json' in content_type(request)):
        params = json.loads(request.body)
        if not params.has_key('annotation') or not params.has_key('toState'):
            return HttpResponseBadRequest("Missing annotation/state parameters")
        LOGGING.info("advancing %s to state:%s", str(params.get('annotation')),
                     str(params.get('toState')))
        change_annotation_state(params.get('annotation'),
                                params.get('toState'), request)
        return HttpResponseNoContent()
    elif not isPOST(request):
        return HttpResponseNotAllowed(["POST"],
                                      content='Only POST method is allowed')
    else:
        return HttpResponseUnsupportedMediaType("Message must contain %s" % 
                                                CONTENT_JSON)
    return HttpResponseNoContent()


class Following(View):
    """
    This class enables a user to follow or stop following a resource and to
    list the resources that they are following.

    """
    @method_decorator(csrf_exempt)
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        try:
            return super(Following, self).dispatch(*args, **kwargs)
        except Exception as ex:
            LOGGING.error("Following - unexpected error: %s", ex)
            return HttpResponseServerError(str(ex))

    def delete(self, request, *args, **kwargs):
        """
        Stop following the resource.
    
        """
        resource_uri = kwargs["resource_uri"]
        FollowedResource.objects.filter(
            user=self.request.user).filter(resource=resource_uri).delete()
        return HttpResponseNoContent()

    def get(self, request, *args, **kwargs):
        """
        Get a list of resources that the user is following.
        
        """
        # if text format redirect to GUI
        if CONTENT_HTML in http_accept(request):
            LOGGING.info("Redirecting to /following/")
            path = "/%s/" % FOLLOWING
            return HttpResponseSeeOther(path)
        if CONTENT_JSON not in http_accept(request):
            return HttpResponseNotAcceptable('Format not accepted')
        following = (FollowedResource.objects.filter(user=request.user)
                     .order_by('resource'))
        data = []
        for follow in following:
            data.append({"resource": follow.resource})
        return HttpResponse(json.dumps(data), content_type=CONTENT_JSON)

    def put(self, request, *args, **kwargs):
        """
        Validate the resource. Check that the user is not already following the
        resource and that the resource exists in the triple store. Add a new
        record to the FollowedResource model.
        
        """
        resource_uri = kwargs["resource_uri"]
        if is_following_resource(request.user, resource_uri):
            # You are already following this resource
            return HttpResponseNoContent()
        if not (resource_exists(resource_uri)):
            return HttpResponseNotFound('Resource does not exist on this system')
    
        followed_resource = FollowedResource.objects.create(
                                user_id=request.user.id,
                                resource=resource_uri)
        followed_resource.save()
        return HttpResponseNoContent()
 

class ReportToModerator(View):
    """
    Report the resource to the moderator.

    """
    @method_decorator(csrf_exempt)
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        try:
            return super(ReportToModerator, self).dispatch(*args, **kwargs)
        except Exception as ex:
            LOGGING.error("ReportToModerator - unexpected error: %s", ex)
            return HttpResponseServerError(str(ex))

    def put(self, request, *args, **kwargs):
        resource_id = kwargs["resource_id"]
        LOGGING.info("reporting %s to moderator", resource_id)
        c_type = content_type(request)
        if c_type is not None and CONTENT_TEXT not in c_type:
            return HttpResponseUnsupportedMediaType("Message must contain %s" % 
                                                    CONTENT_TEXT)
        try:
            report_to_moderator(request, resource_id)
        except NotFoundError as ex:
            return HttpResponseNotFound(str(ex))
        except SecurityError as ex:
            return HttpResponseForbidden(str(ex))
        return HttpResponseNoContent()
    
    
class Resource(View):
    """
    Get a resources details or delete the resource.

    """
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        try:
            return super(Resource, self).dispatch(*args, **kwargs)
        except Exception as ex:
            LOGGING.error("Resource - unexpected error: %s", ex)
            return HttpResponseServerError(str(ex))

    def delete(self, request, *args, **kwargs):
        """
        Delete the resource, move it to the 'retired' graph.

        """
        resource_id = kwargs["resource_id"]
        LOGGING.info("advancing %s to state:%s", resource_id, RETIRED)
        try:
            change_annotation_state(resource_id, RETIRED, request)
        except NotFoundError as ex:
            return HttpResponseNotFound(str(ex))
        except SecurityError as ex:
            return HttpResponseForbidden(str(ex))
        return HttpResponseNoContent()

    def get(self, request, *args, **kwargs):
        """
        Get the resource details dependent on the mime format.

        """
        resource_id = kwargs["resource_id"]
        # if valid format requested redirect to DATA
        if validate_mime_format(request) is not None:
            path = "/%s/%s" % (DATA, resource_id)
            path = self.process_resource_parameters(request, path)
            LOGGING.info("Redirecting to %s", path)
            return HttpResponseSeeOther(path)

        # if text format redirect to PAGE
        if CONTENT_HTML in http_accept(request):
            path = '/%s/%s' % (PAGE, resource_id)
            path = self.process_resource_parameters(request, path)
            LOGGING.info("Redirecting to %s", path)
            return HttpResponseSeeOther(path)

        return HttpResponseNotAcceptable('Format not accepted')


    def process_resource_parameters(self, request, path):
        """
        Add depth and format parameters onto the path.

        """
        depth = get_depth(request)
        format_ = get_format(request)
        if format_ is not None:
            path = "%s/?format=%s" % (path, format_)
            if depth is not None:
                path = "%s&depth=%s" % (path, depth)
        elif depth is not None:
            path = "%s/?depth=%s" % (path, depth)
        return path

    
class ResourceData(View):
    """
    Get the resources details.

    """
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        try:
            return super(ResourceData, self).dispatch(*args, **kwargs)
        except Exception as ex:
            LOGGING.error("ResourceData - unexpected error: %s", ex)
            return HttpResponseServerError(str(ex))

    def get(self, request, *args, **kwargs):
        """
        Get the resource details dependent on the mime format.

        """
        resource_id = kwargs["resource_id"]
        req_format = validate_mime_format(request)
        if req_format is None:
            return HttpResponseNotAcceptable('Format not accepted')

        depth = get_depth(request)
        if depth == None:
            depth = 1
        tmp_g = find_resource_by_id(resource_id, depth)
        if len(tmp_g) < 1:
            return HttpResponseNotFound('Resource does not exist on this system')
        return HttpResponse(tmp_g.serialize(format=req_format),
                            mimetype=FORMAT_MAP.get(req_format))


class ResourcePage(View):
    """
    Get the resources details and present them in a html page.

    """
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        try:
            return super(ResourcePage, self).dispatch(*args, **kwargs)
        except Exception as ex:
            LOGGING.error("ResourcePage - unexpected error: %s", ex)
            messages.add_message(self.request, messages.ERROR, str(ex))
            return mm_render_to_response_error(self.request, '500.html', 500)

    def get(self, request, *args, **kwargs):
        """
        Get the resources details and present them in a html page.

        """
        resource_id = kwargs["resource_id"]
        if CONTENT_HTML not in http_accept(request):
            return HttpResponseNotAcceptable('Format not accepted')

        tmp_g = find_resource_by_id(resource_id, 1)
        if len(tmp_g) < 1:
            messages.add_message(self.request, messages.ERROR,
                                 'Resource does not exist on this system')
            return mm_render_to_response_error(self.request, '404.html', 404)
        resource_uri = format_resource_uri_ref(resource_id)
    
        # Check if the resource is an annotation
        triples = tmp_g.triples((resource_uri, RDF['type'], OA['Annotation']))
        for _ in triples:
            return annotation(request, resource_uri, tmp_g)

        # Check if the resource is a SoftwareAgent
        triples = tmp_g.triples((resource_uri, RDF['type'],
                                 PROV['SoftwareAgent']))
        for _ in triples:
            return agent(request, resource_uri, tmp_g)
    
        # Check if the resource is an activity
        triples = tmp_g.triples((resource_uri, RDF['type'], PROV['Activity']))
        for _ in triples:
            return activity(request, resource_uri, tmp_g)
    
        # Check if the resource is a person
        triples = tmp_g.triples((resource_uri, RDF['type'], FOAF['Person']))
        for _ in triples:
            return person(request, resource_uri, tmp_g)
    
        # Check if the resource is a composite
        triples = tmp_g.triples((resource_uri, RDF['type'], OA['Composite']))
        for _ in triples:
            return composite(request, resource_uri, tmp_g)
        return resource(request, resource_uri, tmp_g)


def version(request):
    """
    Get the version number of the server.

    Args:
        request (WSGIRequest): The request from the user

    """
    return HttpResponse(__version__, content_type=CONTENT_TEXT)


def vocab(request):
    """
    Get the chame vocab.

    Args:
        request (WSGIRequest): The request from the user

    """
    tmp_g = None
    try:
        tmp_g = get_vocab()
    except StoreConnectionError as ex:
        LOGGING.error("vocab - unexpected error: %s", ex)
        return HttpResponseServerError(str(ex))

    req_format = validate_mime_format(request)
    if req_format is None or CONTENT_HTML in http_accept(request):
        req_format = CONTENT_JSON
    return HttpResponse(__serialize(tmp_g, req_format=req_format))


