'''
Created on 11 Dec 2013

@author: mnagni
'''
from json import dumps
import logging

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.utils import IntegrityError
from django.forms.util import ErrorList
from django.http.response import HttpResponseRedirect, HttpResponse, \
    HttpResponseNotFound
from provider.oauth2.models import AccessToken

from djcharme import mm_render_to_response
from djcharme.charme_security_model import UserForm, UserUpdateForm, \
    UserProfileUpdateForm
from djcharme.models import UserProfile
from djcharme.security_middleware import is_valid_token


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
            user_profile = UserProfile.objects.create(
                            user_id=user.id,
                            show_email=user_form.cleaned_data.get('show_email'))
            return HttpResponseRedirect(reverse('login'))
        except IntegrityError:
            LOGGING.debug('Username is already registered')
            errors = user_form._errors.setdefault('username', ErrorList())
            errors.append(u'Username is already registered')

    context['user_form'] = user_form
    return mm_render_to_response(request, context,
                                 'registration/registration.html')


def _update_user(request):
    LOGGING.debug('_update_user')
    context = {}
    user_form = UserUpdateForm(request.POST, instance=request.user)
    user_profile_form = UserProfileUpdateForm(request.POST,
                                              instance=request.user.userprofile)
    if user_form.is_valid() and user_profile_form.is_valid:
        try:
            user_form.save()
            user_profile_form.save()
            context = {}
            return mm_render_to_response(request, context,
                        'registration/profile_change_done.html')
        except IntegrityError:
            LOGGING.debug('Username is already registered')
            errors = user_form._errors.setdefault('username', ErrorList())
            errors.append(u'Username is already registered')

    context['user_form'] = user_form
    context['user_profile_form'] = user_profile_form
    return mm_render_to_response(request, context,
                                 'registration/profile_change_form.html')


def registration(request):
    context = {}
    LOGGING.debug('Registration request received')

    if request.method == 'POST':
        return _register_user(request)
    else:  # GET
        context['user_form'] = UserForm()
        return mm_render_to_response(request, context,
                                     'registration/registration.html')


def profile_change(request):
    context = {}
    LOGGING.debug('Profile request received')

    if request.method == 'POST':
        LOGGING.debug('method is POST')
        return _update_user(request)
    else:  # GET
        # Set up initial values
        user = request.user
        orig_values = {}
        orig_values['username'] = user.get_username
        orig_values['first_name'] = user.first_name
        orig_values['last_name'] = user.last_name
        orig_values['email'] = user.email
        user_form = UserUpdateForm(initial=orig_values)
        context['user_form'] = user_form
        user_profile = user.userprofile
        orig_values = {}
        orig_values['show_email'] = user_profile.show_email
        user_profile_form = UserProfileUpdateForm(initial=orig_values)
        context['user_profile_form'] = user_profile_form
        return mm_render_to_response(request, context,
                                     'registration/profile_change_form.html')


def profile_change_done(request):
    context = {}
    return mm_render_to_response(request, context,
                                 'registration/profile_change_done.html')


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
