'''
Created on 11 Dec 2013

@author: mnagni
'''
from djcharme import mm_render_to_response
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
import logging
from django.core.urlresolvers import reverse
from django.forms.util import ErrorList
from django.http.response import HttpResponseRedirect, HttpResponse, \
    HttpResponseNotFound
from djcharme.charme_security_model import UserForm
from djcharme.security_middleware import is_valid_token
from provider.oauth2.models import AccessToken
from json import dumps


LOGGING = logging.getLogger(__name__)

def _register_user(request):
    context = {}
    user_form = UserForm(request.POST)
    if user_form.is_valid():
        try:
            user = User.objects.create_user(
                        user_form.cleaned_data.get('username'),
                        user_form.cleaned_data.get('email'),
                        password=user_form.cleaned_data.get('password'),
                        first_name=user_form.cleaned_data.get('first_name'),
                        last_name=user_form.cleaned_data.get('last_name'))
            user.save()
            return HttpResponseRedirect(reverse('login'))
        except IntegrityError:
            LOGGING.debug('Username is already registered')
            errors = user_form._errors.setdefault('username', ErrorList())
            errors.append(u'Username is already registered')

    context['user_form'] = user_form
    return mm_render_to_response(request, context, 'registration.html')

def registration(request):
    context = {}
    LOGGING.debug('Registration request received')

    if request.method == 'POST':
        return _register_user(request)
    else:  # GET
        context['user_form'] = UserForm()
        return mm_render_to_response(request, context, 'registration.html')

def validate_token(request, token=None, expire=None):
    if is_valid_token(token):
        return HttpResponse(status=200)
    return HttpResponseNotFound()

def userinfo(request):
    # The request has an Access Token
    if request.environ.get('HTTP_AUTHORIZATION', None):
        for term in request.environ.get('HTTP_AUTHORIZATION').split():
            try:
                access_t = AccessToken.objects.get(token=term)
                ret = {}
                ret['username'] = access_t.user.username
                ret['first_name'] = access_t.user.first_name
                ret['last_name'] = access_t.user.last_name
                return HttpResponse(dumps(ret),
                        content_type="application/json")
            except AccessToken.DoesNotExist:
                continue
    return HttpResponseNotFound()

def token_response(request):
    return mm_render_to_response(request, {}, 'token_response.html')

def test_token(request):
    return mm_render_to_response(request, {}, 'oauth_test2.html')

User        
