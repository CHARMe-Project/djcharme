'''
Created on 11 Dec 2013

@author: mnagni
'''
from django.test import TestCase
from django.test.client import Client
from djcharme.forms import UserForm

class RegisterTestCase(TestCase):
    def setUp(self):
        pass

    def test_user_registration(self):
        csrf_client = Client(enforce_csrf_checks=False, 
                             HTTP_USER_AGENT='Mozilla/5.0')
        response = csrf_client.get('/accounts/registration/', 
                                   {'user_form': UserForm()})
        print response
                
        post_data = {'password': 'mypassword', 
                     'confirm_password': 'mypassword',
                     'email': 'my.email@mail.com', 
                     'confirm_email': 'my.email@mail.com'}                
        response = csrf_client.post('/accounts/registration/', post_data)
        print response