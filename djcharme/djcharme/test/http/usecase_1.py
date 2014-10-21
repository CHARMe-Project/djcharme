# coding: utf-8
'''
Created on 31 May 2013

@author: mnagni
Use case 1.
A scientist wishes to record that a publication has been written mentioning a dataset.
'''
import unittest

from django.test.client import RequestFactory
from rdflib.graph import Graph

from djcharme import settings
from djcharme.charme_middleware import CharmeMiddleware
from djcharme.node.constants import FORMAT_MAP
from djcharme.test import test_insert_anotation, turtle_semantic


class Test(unittest.TestCase):

    def setUp(self):
        self.store = CharmeMiddleware.get_store(debug=True)
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
                  http_accept=FORMAT_MAP['json-ld'],
                  content_type=FORMAT_MAP['turtle'],
                  data=turtle_semantic)
        print response


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
