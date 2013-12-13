'''
Created on 11 Dec 2013

@author: mnagni
'''
from django.test import TestCase
from djcharme.forms import UserForm

class UserFormTestCase(TestCase):
    user_form_initial = {}
    
    def setUp(self):
        self.user_form_initial = {
        'email': 'aa@mymail.com', 
        'confirm_email': 'aa@mymail.com',
        'password': '123', 
        'confirm_password': '123'
        }

    def test_email_mismatch(self):
        self.user_form_initial['confirm_email'] = 'bbb@maymeil.com'
        user_form = UserForm(initial=self.user_form_initial)                
        self.assert_(user_form.is_valid())
        
    def test_password_mismatch(self):
        self.user_form_initial['confirm_password'] = '789'
        user_form = UserForm(initial=self.user_form_initial)                
        self.assert_(user_form.is_valid())        