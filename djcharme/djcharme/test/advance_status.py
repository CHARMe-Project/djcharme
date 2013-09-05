'''
Created on 5 Sep 2013

@author: mnagni
'''
import unittest
import json
from djcharme.charme_middleware import CharmeMiddleware
from django.conf import settings
from django.test.client import RequestFactory
from rdflib.graph import Graph
from djcharme.test import test_insert_anotation, extract_annotation_uri,\
    test_advance_status
from urllib import urlencode
from djcharme.views.node_gate import advance_status


class Test(unittest.TestCase):


    def setUp(self):
        self.store = CharmeMiddleware.get_store(debug = True)
        
        
        self.graph = 'submitted'
        self.identifier = '%s/%s' % (getattr(settings, 'SPARQL_DATA'),
                                     self.graph)
        self.g = Graph(store=self.store, identifier=self.identifier)               
        self.factory = RequestFactory()


    def tearDown(self):
        for res in self.g:
            self.g.remove(res)
        if hasattr(self, 'user'):
            self.user.delete()


    def test_advance_status(self):
        new_state = 'stable' 
        response = test_insert_anotation(self)

        anno_uri = extract_annotation_uri(response.content)
        annoid = anno_uri[anno_uri.rfind('/') + 1 : ]
        self.assertIsNotNone(annoid, "Did not insert the annotation")

        data = {'annotation': annoid, 
                'toState': new_state}        
        response = advance_status(test_advance_status(self, json.dumps(data)))
        
        '''
            Need to verify better the triple has been moved
            for example using the  (TBD)
        '''
        
        self.assert_(response.status_code == 200, "HTTPResponse has status_code: %s" % response.status_code)
        #self.assert_(('%s a rdfg:Graph' % (new_state)) in response.content, "Response content does not return the correct state")

    def test_advance_status_wrong_body(self):
        new_state = 'stable' 
        response = test_insert_anotation(self)

        anno_uri = extract_annotation_uri(response.content)
        annoid = anno_uri[anno_uri.rfind('/') + 1 : ]
        self.assertIsNotNone(annoid, "Did not insert the annotation")

        data = {'annotation': annoid, 'toState': new_state}         
        
        response = advance_status(test_advance_status(self, 
                                  url='/advance_status?' + urlencode(data),
                                  data=json.dumps(data)))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()