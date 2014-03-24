'''
Created on 11 Dec 2013

@author: mnagni
'''
from django.forms.forms import Form
from django.forms.fields import CharField, EmailField
from django.forms.widgets import PasswordInput
from django.core.exceptions import ValidationError
from django import forms
from django.contrib.auth import authenticate, get_user_model
import logging
from django.contrib.auth.backends import ModelBackend
from djcharme.exception import SecurityError
from django.utils.text import capfirst

LOGGING = logging.getLogger(__name__)


class UserForm(Form):
    first_name = CharField(max_length=30, required=False)
    last_name = CharField(max_length=30, required=False)    
    password = CharField(max_length=30, widget=PasswordInput(), required=True)
    confirm_password = CharField(max_length=30, widget=PasswordInput(), 
                                 required=True)
    email  = EmailField(required=True)
    confirm_email = EmailField(required=True)
    
    def clean(self):
        if (self.cleaned_data.get('email') !=
            self.cleaned_data.get('confirm_email')):            
            raise ValidationError(
                "Email addresses must match."
            )

        if (self.cleaned_data.get('password') !=
            self.cleaned_data.get('confirm_password')):            
            raise ValidationError(
                "Password must match."
            )
        return self.cleaned_data
            
            
class LoginForm(Form):            
    email           = EmailField(required=True)
    password        = CharField(max_length=30, 
                                widget=PasswordInput(), 
                                required=True)
    
    error_messages = {
        'invalid_login': "Please enter a correct %(username)s and password. "
                           "Note that both fields may be case-sensitive.",
        'inactive': "This account is inactive."
    }    
    
    def __init__(self, request=None, *args, **kwargs):
        """
        The 'request' parameter is set for custom auth use by subclasses.
        The form data comes in via the standard 'data' kwarg.
        """
        self.request = request
        self.user_cache = None
        super(LoginForm, self).__init__(*args, **kwargs)

        # Set the label for the "username" field.
        UserModel = get_user_model()
        self.username_field = UserModel._meta.get_field(UserModel.USERNAME_FIELD)
        if self.fields['email'].label is None:
            self.fields['email'].label = capfirst(self.username_field.verbose_name)
    
    def clean(self):
        username = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
    
        if username and password:
            self.user_cache = authenticate(username=username,
                                           password=password)
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                    params={'username': self.username_field.verbose_name},
                )
            elif not self.user_cache.is_active:
                raise forms.ValidationError(
                    self.error_messages['inactive'],
                    code='inactive',
                )
        return self.cleaned_data

    def check_for_test_cookie(self):
        LOGGING.warn("check_for_test_cookie is deprecated; ensure your login "
                "view is CSRF-protected.", DeprecationWarning)

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache
        
class CharmeAuthenticationBackend(ModelBackend):
    """
    Extends Django's ``ModelBackend`` to allow login via username, 
    or verification token.

    Args are either ``username`` and ``password``
    and ``token``. In either case, ``is_active`` can also be given.

    For login, is_active is not given, so that the login form can
    raise a specific error for inactive users.
    For password reset, True is given for is_active.
    For signup verficiation, False is given for is_active.
    """

    def __init__(self, *args, **kwargs):
        super(CharmeAuthenticationBackend, self).__init__(*args, **kwargs)

    def authenticate(self, **kwargs):
        if kwargs:
            username = kwargs.pop("username", None)
            password = kwargs.pop("password", None)
            if username:
                try:
                    backend = ModelBackend()
                    return backend.authenticate(username=username, 
                                                password=password)
                except Exception:
                    LOGGING.error("Wrong password for username: %s" % username)
                    raise SecurityError()