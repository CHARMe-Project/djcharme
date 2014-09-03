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

Created on 2 Nov 2012

@author: mnagni
'''
import logging
import re

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse
from django.http.response import HttpResponse
from provider.oauth2.models import AccessToken


DJ_SECURITY_SHAREDSECRET_ERROR = 'No SECURITY_SHAREDSECRET parameter \
is defined in the application settings.py file. \
Please define it accordingly to the used LOGIN_SERVICE'

AUTHENTICATION_COOKIE_MISSING = 'The expected cookie is missing. \
Redirect to the authentication service'

DJ_MIDDLEWARE_IP_ERROR = 'No DJ_MIDDLEWARE_IP parameter \
is defined in the application settings.py file. \
Please define it accordingly to the machine/proxy seen by the LOGIN_SERVICE'

LOGIN_SERVICE_ERROR = 'No LOGIN_SETTING parameter is defined in the \
application settings.py file. Please define a proper URL to the \
authenticating service'

LOGOUT = 'logout'
LOGIN = 'login'

LOGGER = logging.getLogger(__name__)


def get_login_service_url():
    return reverse('login')


auth_tkt_name = lambda: getattr(settings, 'AUTH_TKT_NAME', 'auth_tkt')
token_field_name = lambda: getattr(settings, 'TOKEN_FIELD_NAME', 't')
security_filter = lambda: getattr(settings, 'SECURITY_FILTER', [])
redirect_field_name = lambda: getattr(settings, 'REDIRECT_FIELD_NAME', 'r')


def preapare_user_for_session(request, timestamp, userid, tokens, user_data):
    request.authenticated_user = {
        'timestamp': timestamp,
        'userid': userid,
        'tokens': tokens,
        'user_data': user_data
    }
    LOGGER.debug("preapare_user_for_session - Stored in request - " \
                 "userid:%s, user_data:%s", userid, user_data)
    request.session['accountid'] = userid


def filter_request(request, filters):
    """
        Checks a given strings against a list of strings.
        ** string ** string a url
        ** filters ** a list of strings
    """
    if filters is None:
        return False

    for ifilter in filters:
        if re.search(ifilter[0], request.path) and request.method in ifilter[1]:
            return True

    return False


def is_public_url(request):
    '''Test a given is public or secured - True if public'''
    url_filters = security_filter()

    # adds a default filter for reset password request
    reset_regexpr = '%s=[a-f0-9-]*$' % (token_field_name())
    if reset_regexpr not in url_filters:
        url_filters.append(reset_regexpr)

    if filter_request(request, url_filters):
        LOGGER.debug('is_public_url  -Public path and method %r / %r',
                     request.path, request.method)
        return True

    LOGGER.debug('is_public_url - Secured path and method %r / %r',
                 request.path, request.method)
    return False


def is_valid_token(token):
    if token:
        try:
            access_t = AccessToken.objects.get(token=token)
            if access_t.get_expire_delta() > 0:
                return True
        except AccessToken.DoesNotExist:
            return False
    return False


def _get_user(token):
    """
    Get the user information for the given token.

    Args:
        token (str): The auth token.

    Returns:
        User. Details about the user.

    """
    if token:
        try:
            access_t = AccessToken.objects.get(token=token)
        except AccessToken.DoesNotExist:
            LOGGER.warn("_get_user - Cannot get 'User' from access token")
            return None
    return access_t.user


def _get_client(token):
    """
    Get the client information for the given token.

    Args:
        token (str): The auth token.

    Returns:
        Client. Details about the client.

    """
    if token:
        try:
            access_t = AccessToken.objects.get(token=token)
        except AccessToken.DoesNotExist:
            LOGGER.warn("_get_client - Cannot get 'Client' from access token")
            return None
    return access_t.client


class SecurityMiddleware(object):
    """
        Validates if the actual user is authenticated against a
        given authentication service.
        Actually the middleware intercepts all the requests submitted
        to the underlying Django application and verifies if the presence
        or not of a valid paste cookie in the request.
    """

    def process_request(self, request):
        LOGGER.info('process_request - Request: %r',
                    request.build_absolute_uri())

        # The required URL is public
        if is_public_url(request):
            LOGGER.debug('process_request - URL is public')
            return

        # The request has an Access Token
        if request.environ.get('HTTP_AUTHORIZATION', None):
            for term in request.environ.get('HTTP_AUTHORIZATION').split():
                if is_valid_token(term):
                    request.user = _get_user(term)
                    request.client = _get_client(term)
                    LOGGER.debug('process_request - ' \
                    'Request has an access token')
                    return

        login_service_url = get_login_service_url()

        # An anonymous user want to access restricted resources
        if request.path != login_service_url \
            and isinstance(request.user, AnonymousUser):
            LOGGER.debug('process_request - Redirect to login page')
            return HttpResponse('<meta http-equiv="refresh" content="0; url='
                                + login_service_url + '" />', status=401)

        # An anonymous user wants to login
        if request.path == get_login_service_url():
            LOGGER.debug('process_request - Request is for login page')
            return

        LOGGER.debug('process_request - End of method')

    def process_response(self, request, response):
        if hasattr(response, 'url') and "access_token=" in response.url \
        and "token_type" in response.url:
            try:
                response.delete_cookie("sessionid")
                response.delete_cookie("csrftoken")
                # att_token = {'token': json.loads(response.content)}
                # return mm_render_to_response(request, att_token,
                # "token_response.html")
            except Exception as ex:
                LOGGER.warn('process_response - Caught: ' + ex)
        return response
