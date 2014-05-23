'''
Created on 25 Sep 2013

@author: mnagni
'''
import unittest
from djcharme.charme_middleware import CharmeMiddleware
from djcharme.local_settings import SPARQL_DATA
from rdflib.graph import Graph
from djcharme.node.actions import ANNO_SUBMITTED, insert_rdf
from djcharme.test import turtle_usecase1
from djcharme.node.search import search_title


class Test(unittest.TestCase):

    def setUp(self):
        self.store = CharmeMiddleware.get_store(debug=True)
        self.graph = 'submitted'
        self.identifier = '%s/%s' % (SPARQL_DATA, self.graph)
        self.g = Graph(store=self.store, identifier=self.identifier)

    def tearDown(self):
        for res in self.g:
            self.g.remove(res)

    def testSearchTitle(self):
        print insert_rdf(turtle_usecase1, 'turtle', graph=ANNO_SUBMITTED).serialize(format="turtle")
        print search_title("L*", graph=ANNO_SUBMITTED).serialize(format="turtle")


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
