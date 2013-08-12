'''
Created on 25 Jul 2013

@author: mnagni
'''

from django.test.client import RequestFactory
from djcharme.views.node_gate import insert
from rdflib.graph import Graph
from djcharme.local_settings import SPARQL_DATA
from djcharme.charme_middleware import CharmeMiddleware
from djcharme.test import turtle_usecase1

import unittest
import logging
from djcharme.node.actions import format_graphIRI, FORMAT_MAP
from djcharme.views.endpoint import endpoint

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
        

    def test_insert_anotation(self):
        response = insert(self.factory.post('/insert/annotation',
                                            content_type='text/turtle',
                                            data=turtle_usecase1))        
        
        self.assert_(response.status_code == 200, "HTTPResponse has status_code: %s" % response.status_code)
        return response

    def test_GET(self): 
        self.test_insert_anotation()

        graph = format_graphIRI('submitted')
        for accept in FORMAT_MAP.values():
            request = self.factory.get('/endpoint', data = {'graph': graph}, 
                                   HTTP_ACCEPT = accept)
            response = endpoint(request)
            self.assert_(response.status_code in [200, 204], "HTTPResponse has status: %s" 
                         % response.status_code)
            self.assert_('http://data.gov.uk//dataset/index-of-multiple-deprivation' 
                         in response.content, "Cannot serialize %s" % accept)

    def test_GET_406(self): 
        self.test_insert_anotation()
        graph = format_graphIRI('submitted')        
        request = self.factory.get('/endpoint', data = {'graph': graph}, 
                               HTTP_ACCEPT = 'fake')
        response = endpoint(request)
        self.assert_(response.status_code in [406], "HTTPResponse has status: %s" 
                     % response.status_code)
        
        
    def test_GET_default(self): 
        self.test_insert_anotation()
        graph = 'default'
        for accept in FORMAT_MAP.values():
            request = self.factory.get('/endpoint', data = {'graph': graph}, 
                                   HTTP_ACCEPT = accept)
            response = endpoint(request)
            self.assert_(response.status_code in [200, 204], "HTTPResponse has status: %s" 
                         % response.status_code)
            self.assert_('http://data.gov.uk//dataset/index-of-multiple-deprivation' 
                         in response.content, "Cannot serialize %s" % accept)
        
        
    def test_GET_default_2(self): 
        self.test_insert_anotation()
        for accept in FORMAT_MAP.values():
            request = self.factory.get('/endpoint', data = {}, 
                                   HTTP_ACCEPT = accept)
            response = endpoint(request)
            self.assert_(response.status_code in [200, 204], "HTTPResponse has status: %s" 
                         % response.status_code)
            self.assert_('http://data.gov.uk//dataset/index-of-multiple-deprivation' 
                         in response.content, "Cannot serialize %s" % accept)        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_get_index']
    unittest.main()