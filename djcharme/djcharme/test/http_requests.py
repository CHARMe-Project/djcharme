'''
Created on 25 Jul 2013

@author: mnagni
'''


from djcharme.views.node_gate import insert, advance_status, process_page
from djcharme.charme_middleware import CharmeMiddleware
from djcharme.test import turtle_usecase1
from django.contrib.auth.models import User
from django.test.client import RequestFactory

from rdflib.graph import Graph

import unittest
import json
import logging
from djcharme import settings
from xml.etree import ElementTree

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
        self.user.delete()
        

    def extract_annotation_uri(self, document):
        xml = ElementTree.fromstring(document)
        RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
        descriptions = xml.findall('%sDescription' % (RDF))
        for desc in descriptions:
            anno = desc.find('./%stype[@%sresource="http://www.w3.org/ns/oa#Annotation"]' % (RDF, RDF))
            if anno is not None:
                return desc.get('%sabout' % RDF)

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
    def test_advance_status(self):
        new_state = 'stable' 
        response = self.test_insert_anotation()

        start = response.content.rfind('<', 0, response.content.index("oa:Annotation")) + 1
        end = response.content.rfind('>', start, response.content.index("oa:Annotation"))

        data = {'annotation': response.content[start:end], 
                'toState': new_state}        
       
        
        response = advance_status(self.factory.post('/advance_status',
                                            content_type='application/json',
                                            data=json.dumps(data))) 
        
        '''
            Need to verify better the triple has been moved
            for example using the  (TBD)
        '''
        
        self.assert_(response.status_code == 200, "HTTPResponse has status_code: %s" % response.status_code)
        #self.assert_(('%s a rdfg:Graph' % (new_state)) in response.content, "Response content does not return the correct state")
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_get_index']
    unittest.main()