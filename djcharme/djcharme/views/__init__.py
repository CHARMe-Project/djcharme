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


Contents:
This module contains helper functions for the views package.

'''
from django.http import HttpResponseRedirect

from djcharme.node.constants import FORMAT_MAP
from djcharme.settings import LOGIN_REDIRECT_URL, REDIRECT_FIELD_NAME
from django.utils.http import is_safe_url
from django.shortcuts import resolve_url


FORMAT = 'format'
DEPTH = 'depth'


def isGET(request):
    return request.method == 'GET'


def isPUT(request):
    return request.method == 'PUT'


def isDELETE(request):
    return request.method == 'DELETE'


def isPOST(request):
    return request.method == 'POST'


def isOPTIONS(request):
    return request.method == 'OPTIONS'


def isHEAD(request):
    return request.method == 'HEAD'


def isPATCH(request):
    return request.method == 'PATCH'


def content_type(request):
    content_type_ = request.environ.get('CONTENT_TYPE', None)
    if content_type_ is None:
        return None
    else:
        return content_type_.split(';')[0]


def get_format(request):
    try:
        return request.GET[FORMAT]
    except KeyError:
        return None


def get_depth(request):
    depth = request.GET.get(DEPTH)
    if depth is not None:
        try:
            return int(depth)
        except ValueError:
            return None
    return None


def http_accept(request):
    accept = request.META.get('HTTP_ACCEPT', None)
    if accept is None:
        return None
    return accept.split(';')[0].split(',')


def check_mime_format(mimeformat):
    """
    Map input MIME format to one of the accepted formats available.

    """
    # Set a default MIME format if none was set
    if mimeformat is None:
        mimeformat = 'application/ld+json'

    if '/' in mimeformat:
        for k, value in FORMAT_MAP.iteritems():
            if value in mimeformat:
                return k
    else:
        for k, value in FORMAT_MAP.iteritems():
            if k in mimeformat:
                return k


def get_extra_context(kwargs):
    """ Get any extra context from the keywords.
    """
    try:
        extra_context = kwargs['extra_context']
    except KeyError:
        extra_context = None
    return extra_context


def get_safe_redirect(request):
    """ Check that the URL is safe, i.e. it points back to whence it came.
    """
    redirect_to = request.REQUEST.get(REDIRECT_FIELD_NAME, '')
    # Ensure the user-originating redirection url is safe.
    if not is_safe_url(url=redirect_to, host=request.get_host()):
        redirect_to = resolve_url(LOGIN_REDIRECT_URL)
    return redirect_to


def not_authenticated(func):
    """ decorator that redirect user to next page if
    he is already logged.
    """
    def decorated(request, *args, **kwargs):
        if request.user.is_authenticated():
            next_ = request.GET.get(REDIRECT_FIELD_NAME,
                                    LOGIN_REDIRECT_URL)
            return HttpResponseRedirect(next_)
        return func(request, *args, **kwargs)
    return decorated


def validate_mime_format(request):
    req_format = [get_format(request)]
    if req_format[0] is None:
        req_format = http_accept(request)

    for mimeformat in req_format:
        ret = check_mime_format(mimeformat)
        if ret is not None:
            return ret
    return None

