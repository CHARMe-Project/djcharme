'''
Created on 25 Jul 2013

@author: mnagni
'''


from djcharme.views.node_gate import insert, process_page
from djcharme.charme_middleware import CharmeMiddleware
from djcharme.test import turtle_usecase1
from django.contrib.auth.models import User
from django.test.client import RequestFactory

from rdflib.graph import Graph

import unittest
import logging
from djcharme import settings

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

    def test_insert_anotation(self):
        response = insert(self.factory.post('/insert/annotation',
                                            content_type='text/turtle',
                                            data=turtle_usecase1,
                                            HTTP_ACCEPT = 'application/rdf+xml'))        
        
        self.assert_(response.status_code == 200, "HTTPResponse has status_code: %s" % response.status_code)
        
        anno_uri = self.extract_annotation_uri(response.content)
        annoid = anno_uri[anno_uri.rfind('/') + 1 : ]
        
        request = self._prepare_get('/resource/%s' % annoid)
        request.META['HTTP_ACCEPT'] = "text/html"
        response = process_page(request, resource_id = annoid)
        print response
        return response

    def _prepare_get(self, url):
        request = self.factory.get(url)
        request.user = self.user
        return request
    '''
    def test_get_index(self): 
        self.test_insert_anotation()
        
        graph = 'submitted'
        request = self._prepare_get('/index/%s?format=xml' % graph)        
        self.assert_('hasTarget' in str(index(request, graph)), 
                     "Cannot generate index page")

        request = self._prepare_get('/index/%s?format=turtle' % graph)
        self.assert_('hasTarget' in str(index(request, graph)), 
                     "Cannot generate turtle index page")
        
        request = self._prepare_get('/index/%s?format=jsonld' % graph)
        self.assert_('hasTarget' in str(index(request, graph)), 
                     "Cannot generate jsonld index page")

        graph = 'stable'
        request = self._prepare_get('/index/%s?format=xml' % graph)  
        self.assert_('hasTarget' not in str(index(request, graph)), 
                     "Cannot generate index page")
        
        graph = 'retired'
        request = self._prepare_get('/index/%s?format=xml' % graph)
        self.assert_('hasTarget' not in str(index(request, graph)), 
                     "Cannot generate index page")
    '''

        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_get_index']
    unittest.main()