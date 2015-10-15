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


Contents: This module contains views of the login. If the login was via an
unknown OpenID then Register is used to link the OpenID to an existing account
or a new one.
'''
import logging
import urllib

from django.contrib.auth.models import User
from django.contrib.auth.views import login
from django.core.urlresolvers import reverse
from django.db.utils import IntegrityError
from django.forms.util import ErrorList
from django.http import HttpResponseRedirect
from django.http.response import HttpResponseServerError
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import View
from django_authopenid.forms import OpenidSigninForm, UserAssociation
from django_authopenid.utils import get_url_host
from django_authopenid.views import ask_openid

from djcharme.charme_security_model import LoginForm, UserForm
from djcharme.models import UserProfile
from djcharme.settings import REDIRECT_FIELD_NAME
from djcharme.views import get_extra_context, get_safe_redirect, \
    not_authenticated


LOGGING = logging.getLogger(__name__)

LOGIN_TEMPLATE = 'registration/login.html'
REGISTER_TEMPLATE = 'authopenid/complete.html'


class Login(View):
    """
    Display the login view.

    """
    @method_decorator(not_authenticated)
    def dispatch(self, *args, **kwargs):
        try:
            return super(Login, self).dispatch(*args, **kwargs)
        except Exception as ex:
            LOGGING.error("Login - unexpected error: %s", ex)
            return HttpResponseServerError(str(ex))

    def get(self, request, *args, **kwargs):
        return login(request, template_name=LOGIN_TEMPLATE,
                     authentication_form=LoginForm)

    def post(self, request, *args, **kwargs):
        auth_form = LoginForm
        extra_context = get_extra_context(kwargs)

        # local sign in
        if 'openid_url' not in request.POST.keys():
            return login(request, template_name=LOGIN_TEMPLATE,
                         authentication_form=auth_form,
                         extra_context=extra_context)

        # open id sign in
        redirect_to = get_safe_redirect(request)
        openid_form = OpenidSigninForm(data=request.POST)
        context = {
            'openid_form': openid_form,
            'form': auth_form(),
            REDIRECT_FIELD_NAME: redirect_to,
        }
        if extra_context is not None:
            context.update(extra_context)

        if openid_form.is_valid():
            redirect_url = ("%s%s?%s" % 
                            (get_url_host(request),
                             reverse('user_complete_signin'),
                             urllib.urlencode
                             ({REDIRECT_FIELD_NAME: redirect_to})))
            return ask_openid(request,
                              openid_form.cleaned_data['openid_url'],
                              redirect_url,
                              on_failure=signin_failure)

        # form not valid
        return render(request, LOGIN_TEMPLATE, context)


class Register(View):
    """
    Display the associate view. This prompts a user to link their openid with a
    local account.

    """
    @method_decorator(not_authenticated)
    def dispatch(self, *args, **kwargs):
        try:
            return super(Register, self).dispatch(*args, **kwargs)
        except Exception as ex:
            LOGGING.error("Register - unexpected error: %s", ex)
            return HttpResponseServerError(str(ex))

    def get(self, request, *args, **kwargs):
        extra_context = get_extra_context(kwargs)
        redirect_to = get_safe_redirect(request)
        openid_ = request.session.get('openid', None)
        if openid_ is None or not openid_:
            # no open id credentials so back to login page
            return HttpResponseRedirect("%s?%s" % 
                                        (reverse('login'),
                                         urllib.urlencode
                                         ({REDIRECT_FIELD_NAME: redirect_to})))

        register_form = UserForm()
        auth_form = LoginForm()
        context = {
            'user_form': register_form,
            'auth_form': auth_form,
            'openid': True,
            REDIRECT_FIELD_NAME: redirect_to,
        }
        if extra_context is not None:
            context.update(extra_context)

        return render(request, REGISTER_TEMPLATE, context)

    def post(self, request, *args, **kwargs):
        send_email = True
        extra_context = get_extra_context(kwargs)
        redirect_to = get_safe_redirect(request)
        openid_ = request.session.get('openid', None)
        if openid_ is None or not openid_:
            # no open id credentials so back to login page
            return HttpResponseRedirect("%s?%s" % 
                                        (reverse('user_signin'),
                                         urllib.urlencode
                                         ({REDIRECT_FIELD_NAME: redirect_to})))

        user_ = None
        user_form = UserForm()
        auth_form = LoginForm()

        if 'email' in request.POST.keys():
            user_form = UserForm(request.POST)
            if user_form.is_valid():
                try:
                    user_ = User.objects.create_user(
                        user_form.cleaned_data.get('username'),
                        user_form.cleaned_data.get('email'),
                        password=user_form.cleaned_data.get('password'),
                        first_name=user_form.cleaned_data.get('first_name'),
                        last_name=user_form.cleaned_data.get('last_name'))
                    user_.save()
                    user_profile = UserProfile.objects.create(
                        user_id=user_.id,
                        show_email=user_form.cleaned_data.get('show_email'))
                    user_profile.save()
                except IntegrityError:
                    LOGGING.debug('Username is already registered')
                    errors = user_form._errors.setdefault('username',
                                                          ErrorList())
                    errors.append(u'Username is already registered')
        else:
            auth_form = LoginForm(data=request.POST)
            if auth_form.is_valid():
                user_ = auth_form.get_user()

        if user_ is not None:
            # associate the user to openid
            uassoc = UserAssociation(openid_url=str(openid_),
                                     user_id=user_.id)
            uassoc.save(send_email=send_email)
            login(request, user_)
            return HttpResponseRedirect(redirect_to)

        # form not valid
        context = {
            'user_form': user_form,
            'auth_form': auth_form,
            'openid': True,
            REDIRECT_FIELD_NAME: redirect_to,
        }
        if extra_context is not None:
            context.update(extra_context)

        return render(request, REGISTER_TEMPLATE, context)


def signin_failure(request, message, extra_context=None, **kwargs):
    """
    failure with openid signin. Go back to signin page.

    :attr request: request object
    :attr message: an error message
    :attr extra_context: A dictionary of variables to add to the template
    context. Any callable object in this dictionary will be called to produce
    the end result which appears in the context.
    """
    redirect_to = get_safe_redirect(request)
    extra_context = get_extra_context(kwargs)
    openid_form = OpenidSigninForm()
    if message is not None and message is not "":
        openid_form.non_field_errors = openid_form.error_class([message])
    context = {
        'openid_form': openid_form,
        'form': LoginForm(),
        REDIRECT_FIELD_NAME: redirect_to,
    }
    if extra_context is not None:
        context.update(extra_context)
    return render(request, LOGIN_TEMPLATE, context)

