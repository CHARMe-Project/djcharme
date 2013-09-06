'''
Created on 25 Jul 2013

@author: mnagni
'''


from djcharme.views.node_gate import process_page, process_resource,\
    process_data
from djcharme.charme_middleware import CharmeMiddleware
from djcharme.test import turtle_usecase1, test_insert_anotation,\
    extract_annotation_uri, _prepare_get
from django.contrib.auth.models import User
from django.test.client import RequestFactory

from rdflib.graph import Graph

import unittest
import logging
from djcharme import settings
from djcharme.node.actions import FORMAT_MAP

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

    def test_get_annotation_as_html(self):
        response = test_insert_anotation(self,
                          http_accept='application/rdf+xml', 
                          content_type='text/turtle', 
                          data=turtle_usecase1)        
        
        anno_uri = extract_annotation_uri(response.content)
        annoid = anno_uri[anno_uri.rfind('/') + 1 : ]
        
        request = _prepare_get(self.factory, '/resource/%s' % annoid)
        request.META['HTTP_ACCEPT'] = "text/html"
        response = process_resource(request, resource_id = annoid)
        self.assert_(response.status_code == 303, 
                     "HTTPResponse has status_code: %s" % response.status_code)
        
        location = response._headers.get('location', ('Location', None))[1]
        self.assert_('/page' in location, "Wrong 303 to %s" % location)
        
        request = _prepare_get(self.factory, location)
        request.META['HTTP_ACCEPT'] = "text/html"
        response = process_page(request, resource_id = annoid)
        
        
        self.assert_(response.status_code == 200, "HTTPResponse has status_code: %s" % response.status_code)
        print response
        return response

    def test_get_annotation_as_jsonld(self):
        response = test_insert_anotation(self,
                          http_accept=FORMAT_MAP['xml'], 
                          content_type=FORMAT_MAP['turtle'], 
                          data=turtle_usecase1)                
        
        anno_uri = extract_annotation_uri(response.content)
        annoid = anno_uri[anno_uri.rfind('/') + 1 : ]
        
        request = _prepare_get(self.factory, '/resource/%s' % annoid)
        request.META['HTTP_ACCEPT'] = FORMAT_MAP['json-ld']
        response = process_resource(request, resource_id = annoid)        
        self.assert_(response.status_code == 303, "HTTPResponse has status_code: %s" % response.status_code)

        location = response._headers.get('location', ('Location', None))[1]
        self.assert_('/data' in location, "Wrong 303 to %s" % location)

        request = _prepare_get(self.factory, location)
        request.META['HTTP_ACCEPT'] = FORMAT_MAP['json-ld']
        response = process_data(request, resource_id = annoid)
        print response
        return response

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_get_index']
    unittest.main()