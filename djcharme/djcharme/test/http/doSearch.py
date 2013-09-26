'''
Created on 25 Jul 2013

@author: mnagni
'''


from djcharme.charme_middleware import CharmeMiddleware
from django.contrib.auth.models import User
from django.test.client import RequestFactory

from rdflib.graph import Graph

import unittest
import logging
from djcharme import settings
from djcharme.node.actions import FORMAT_MAP, ANNO_STABLE, ANNO_SUBMITTED
from djcharme.test import _prepare_get, test_insert_anotation, turtle_usecase1
from djcharme.views.search import get_description, do_search
from urllib import urlencode

LOGGING = logging.getLogger(__name__)

class Test(unittest.TestCase):


    def setUp(self):
        self.store = CharmeMiddleware.get_store(debug = True)
        
        
        self.graph = 'submitted'
        self.identifier = '%s/%s' % (getattr(settings, 'SPARQL_DATA'),
                                     self.graph)
        self.g = Graph(store=self.store, identifier=self.identifier)               
        self.factory = RequestFactory()
        
        users = User.objects.filter(username = 'Alberto Sordi')
        if users.count() == 0:
            self.user = User.objects.create_user('Alberto Sordi', 'albertone@sordi.com', 'ammericano')

    def tearDown(self):   
        for res in self.g:
            self.g.remove(res)
        if hasattr(self, 'user'):
            self.user.delete() 


    def test_getOSDescription(self):
        request = _prepare_get(self.factory, '/search/description')
        request.META['HTTP_ACCEPT'] = "text/html"
        print get_description(request)
        
         
    
    def test_doSearch(self):
        test_insert_anotation(self,
                          http_accept='application/rdf+xml', 
                          content_type='text/turtle', 
                          data=turtle_usecase1)        
        
        params = {'title': 'L*', 'status': ANNO_SUBMITTED}
        request = _prepare_get(self.factory, '/search/rdf?%s' % urlencode(params))
        request.META['HTTP_ACCEPT'] = "application/rdf+xml"
        response = do_search(request, 'rdf')
        self.assertIn('http://proteus.badc.rl.ac.uk:8000/resource/', response.content, "Error!")
        
        params = {'title': 'L*'}
        request = _prepare_get(self.factory, '/search/rdf?%s' % urlencode(params))
        request.META['HTTP_ACCEPT'] = "application/rdf+xml"
        response = do_search(request, 'rdf')
        self.assertNotIn('http://proteus.badc.rl.ac.uk:8000/resource/fc0c428d5e204a07992b3c354da91a5b', response.content, "Error!")
        return response
    

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_get_index']
    unittest.main()