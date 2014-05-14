'''
Created on 30 Jul 2013

@author: mnagni
'''
from django.http.response import HttpResponse


class Http503(HttpResponse):
    status_code = 503
