'''
Created on 31 May 2013

@author: mnagni
Use case 1.
A scientist wishes to record that a publication has been written mentioning a dataset.
'''
import unittest
from djcharme.node.actions import FORMAT_MAP
from rdflib.graph import Graph
from djcharme.charme_middleware import CharmeMiddleware
from djcharme.test import turtle_usecase1, test_insert_anotation, rdf_usecase1
from djcharme import settings
from django.test.client import RequestFactory

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

    def test_usecase_1(self):
        response = test_insert_anotation(self,
                  http_accept=FORMAT_MAP['turtle'], 
                  content_type=FORMAT_MAP['xml'], 
                  data=rdf_usecase1) 
        print response
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()