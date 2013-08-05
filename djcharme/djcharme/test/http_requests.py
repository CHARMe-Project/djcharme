'''
Created on 25 Jul 2013

@author: mnagni
'''

from django.test.client import RequestFactory
from djcharme.views.node_gate import index, insert
from rdflib.graph import Graph
from djcharme.local_settings import SPARQL_DATA
from djcharme.charme_middleware import CharmeMiddleware
from djcharme.test import turtle_usecase1

import unittest
import logging

LOGGING = logging.getLogger(__name__)

class Test(unittest.TestCase):


    def setUp(self):
        self.store = CharmeMiddleware.get_store(debug = True)
        
        
        self.graph = 'submitted'
        self.identifier = '%s/%s' % (SPARQL_DATA, self.graph)
        self.g = Graph(store=self.store, identifier=self.identifier)               
        self.factory = RequestFactory()

    def tearDown(self):   
        for res in self.g:
            self.g.remove(res)

    def test_get_index(self): 
        response = insert(self.factory.post('/insert/annotation',
                                            content_type='text/turtle',
                                            data=turtle_usecase1))        
        self.assert_(response.status_code == 200, "HTTPResponse has status_code: %s" % response.status_code)
        
        graph = 'submitted'
        request = self.factory.get('/index/%s?format=xml' % graph)
        self.assert_('hasTarget' in str(index(request, graph)), 
                     "Cannot generate index page")

        request = self.factory.get('/index/%s?format=turtle' % graph)
        self.assert_('hasTarget' in str(index(request, graph)), 
                     "Cannot generate turtle index page")
        
        request = self.factory.get('/index/%s?format=jsonld' % graph)
        self.assert_('hasTarget' in str(index(request, graph)), 
                     "Cannot generate jsonld index page")

        graph = 'stable'
        request = self.factory.get('/index/%s?format=xml' % graph)  
        self.assert_('hasTarget' not in str(index(request, graph)), 
                     "Cannot generate index page")
        
        graph = 'retired'
        request = self.factory.get('/index/%s?format=xml' % graph)  
        self.assert_('hasTarget' not in str(index(request, graph)), 
                     "Cannot generate index page")

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_get_index']
    unittest.main()