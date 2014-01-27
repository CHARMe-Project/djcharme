'''
Created on 11 Dec 2013

@author: mnagni
'''
from djcharme import mm_render_to_response
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
import logging
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect, HttpResponse,\
    HttpResponseNotFound
from djcharme.charme_security_model import UserForm
from djcharme.security_middleware import is_valid_token


LOGGING = logging.getLogger(__name__)

def _register_user(request):
    context = {}
    user_form = UserForm(request.POST)
    if user_form.is_valid():
        try:
            user = User.objects.create_user(user_form.cleaned_data.get('email'), 
                        user_form.cleaned_data.get('email'), 
                        password = user_form.cleaned_data.get('password'))
            user.save()
            return HttpResponseRedirect(reverse('login'))
        except IntegrityError:
            LOGGING.debug('User registration required an existing username')

    context['user_form'] = user_form
    return mm_render_to_response(request, context, 'registration.html')        

def registration(request):
    context = {}
    print 'RECEIVED REQUEST: ' + request.method
    
    if request.method == 'POST':
        return _register_user(request)
    else: #GET
        context['user_form'] = UserForm()       
        return mm_render_to_response(request, context, 'registration.html')          

def validate_token(request, token=None, expire=None):
    if is_valid_token(token):
        return HttpResponse(status=200)
    return HttpResponseNotFound()

def test_token(request):
    return mm_render_to_response(request, {}, 'oauth_test2.html')
        