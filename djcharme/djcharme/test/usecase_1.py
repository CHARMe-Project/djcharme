'''
Created on 31 May 2013

@author: mnagni
Use case 1.
A scientist wishes to record that a publication has been written mentioning a dataset.
'''
import unittest
from djcharme.node.actions import insert_rdf, ANNO_SUBMITTED
from rdflib.graph import Graph
from djcharme.local_settings import SPARQL_DATA
from djcharme.charme_middleware import CharmeMiddleware
from djcharme.test import turtle_usecase1

class Test(unittest.TestCase):


    def setUp(self):
        self.store = CharmeMiddleware.get_store(debug = True)
        self.graph = 'submitted'
        self.identifier = '%s/%s' % (SPARQL_DATA, self.graph)
        self.g = Graph(store=self.store, identifier=self.identifier)        

    def tearDown(self):   
        for res in self.g:
            self.g.remove(res)

    def test_usecase_1(self):
        tmp_g = insert_rdf(turtle_usecase1, 'text/turtle', graph=ANNO_SUBMITTED)
        print tmp_g.serialize()


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()