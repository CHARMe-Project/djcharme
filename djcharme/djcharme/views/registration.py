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
This module contains views of the user registration pages.

Created on 11 Dec 2013

@author: mnagni
'''
from json import dumps
import logging

from django.contrib.auth.models import User
from django.contrib.auth.views import login
from django.core.urlresolvers import reverse
from django.db.models import ObjectDoesNotExist
from django.db.utils import IntegrityError
from django.forms.util import ErrorList
from django.http.response import HttpResponseRedirect, HttpResponse, \
    HttpResponseNotFound
from django.http.response import HttpResponseServerError
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View
from provider.oauth2.models import AccessToken

from djcharme import mm_render_to_response
from djcharme.charme_security_model import UserForm, UserUpdateForm, \
    UserProfileUpdateForm
from djcharme.forms import UsernameReminderForm
from djcharme.models import UserProfile
from djcharme.node import get_users_admin_role_orgs
from djcharme.security_middleware import is_valid_token
from djcharme.settings import REDIRECT_FIELD_NAME
from djcharme.views import get_extra_context, get_safe_redirect
from djcharme.views import not_authenticated


LOGGING = logging.getLogger(__name__)

CHANGE_FORM_TEMPLATE = 'registration/profile_change_form.html'
PROFILE_TEMPLATE = 'registration/profile.html'
REGISTEATION_TEMPLATE = 'registration/registration.html'


class Registration(View):
    """
    Display the registration view.

    """
    @method_decorator(not_authenticated)
    def dispatch(self, *args, **kwargs):
        try:
            return super(Registration, self).dispatch(*args, **kwargs)
        except Exception as ex:
            LOGGING.error("Registration - unexpected error: %s", ex)
            return HttpResponseServerError(str(ex))

    def get(self, request, *args, **kwargs):
        context = {}
        context['user_form'] = UserForm()
        context['openid'] = False
        return mm_render_to_response(request, context, REGISTEATION_TEMPLATE)

    def post(self, request, *args, **kwargs):
        LOGGING.debug('Registration request received')
        redirect_to = get_safe_redirect(request)
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
                user_profile.save()
                login(request, user)
                return HttpResponseRedirect(redirect_to)

            except IntegrityError:
                LOGGING.debug('Username is already registered')
                errors = user_form._errors.setdefault('username', ErrorList())
                errors.append(u'Username is already registered')

        # form not valid
        context = {
            'user_form': user_form,
            'openid': False,
            REDIRECT_FIELD_NAME: redirect_to,
        }
        extra_context = get_extra_context(kwargs)
        if extra_context is not None:
            context.update(extra_context)
        return mm_render_to_response(request, context, REGISTEATION_TEMPLATE)


class Profile(TemplateView):
    """
    Display the profile view.

    """
    template_name = PROFILE_TEMPLATE

    def get_context_data(self, **kwargs):
        context = super(Profile, self).get_context_data(**kwargs)
        return context


def _update_user(request):
    LOGGING.debug('_update_user')
    context = {}
    user_form = UserUpdateForm(request.POST, instance=request.user)
    create_profile = False
    try:
        user_profile_form = UserProfileUpdateForm(
            request.POST, instance=request.user.userprofile)
    except ObjectDoesNotExist:
        user_profile_form = UserProfileUpdateForm(request.POST)
        create_profile = True
    if user_form.is_valid() and user_profile_form.is_valid:
        try:
            user_form.save()
            if create_profile:
                user_profile = UserProfile.objects.create(
                    user_id=request.user.id,
                    show_email=user_profile_form.base_fields.get('show_email'))
                user_profile.save()
            else:
                user_profile_form.save()
            context = {}
            context['msg'] = 'Profile updated'
            return mm_render_to_response(request, context, PROFILE_TEMPLATE)
        except IntegrityError:
            LOGGING.debug('Username is already registered')
            errors = user_form._errors.setdefault('username', ErrorList())
            errors.append(u'Username is already registered')

    context['user_form'] = user_form
    context['user_profile_form'] = user_profile_form
    return mm_render_to_response(request, context, CHANGE_FORM_TEMPLATE)


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

        orig_values = {}
        try:
            user_profile = user.userprofile
            orig_values['show_email'] = user_profile.show_email
        except ObjectDoesNotExist:
            orig_values['show_email'] = False
        user_profile_form = UserProfileUpdateForm(initial=orig_values)
        context['user_profile_form'] = user_profile_form
        return mm_render_to_response(request, context, CHANGE_FORM_TEMPLATE)


def username_reminder(request, from_email=None):
    username_reminder_form = UsernameReminderForm
    post_reset_redirect = reverse('username_reminder_done')
    if request.method == "POST":
        form = username_reminder_form(request.POST)
        if form.is_valid():
            opts = {
                'use_https': request.is_secure(),
                'from_email': from_email,
                'email_template_name':
                    'registration/username_reminder_email.html',
                'subject_template_name':
                    'registration/username_reminder_subject.txt',
                'request': request,
            }
            form.save(**opts)
            return HttpResponseRedirect(post_reset_redirect)
    else:
        form = username_reminder_form()
    context = {
        'form': form,
    }

    return mm_render_to_response(request, context,
                                 'registration/username_reminder_form.html')


def username_reminder_done(request):
    context = {}
    return mm_render_to_response(request, context,
                                 'registration/username_reminder_done.html')


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
                ret['admin_for'] = ','.join(get_users_admin_role_orgs
                                            (request.user.id))
                return HttpResponse(dumps(ret),
                                    content_type="application/json")
            except AccessToken.DoesNotExist:
                continue
    return HttpResponseNotFound()


def token_response(request):
    return mm_render_to_response(request, {}, 'token_response.html')


def test_token(request):
    return mm_render_to_response(request, {}, 'oauth_test2.html')

