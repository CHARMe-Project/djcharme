'''
Created on 31 May 2013

@author: mnagni

Use case 2.
A data provider wishes to record that a certain publication describes a dataset
(i.e. is a "canonical" description that everyone should read)
'''
import unittest

from django.test.client import RequestFactory
from rdflib.graph import Graph

from djcharme.charme_middleware import CharmeMiddleware
from djcharme.local_settings import SPARQL_DATA
from djcharme.node.constants import SUBMITTED, FORMAT_MAP
from djcharme.test import charme_turtle_model, turtle_usecase3, json_ld_usecase3
from djcharme.views.node_gate import insert


class Test(unittest.TestCase):

    def setUp(self):
        self.store = CharmeMiddleware.get_store(debug=True)
        self.factory = RequestFactory()

    def tearDown(self):
        identifier = '%s/%s' % (SPARQL_DATA, SUBMITTED)
        g = Graph(store=self.store, identifier=identifier)
        for res in g:
            g.remove(res)

    def test_usecase_3(self):
        insert(self.factory.post('/insert/annotation',
                                    content_type='text/turtle',
                                    data=charme_turtle_model))

        response = insert(self.factory.post('/insert/annotation',
                                    content_type='text/turtle',
                                    HTTP_ACCEPT=FORMAT_MAP['json-ld'],
                                    data=turtle_usecase3))

        print response
        self.assert_(response.status_code == 200,
                     "HTTPResponse has status_code: %s" % response.status_code)

    def test_usecase_3_json_ld(self):
        insert(self.factory.post('/insert/annotation',
                                    content_type='text/turtle',
                                    data=charme_turtle_model))

        response = insert(self.factory.post('/insert/annotation',
                                    content_type='application/ld+json',
                                    HTTP_ACCEPT=FORMAT_MAP['json-ld'],
                                    data=json_ld_usecase3))

        print response
        self.assert_(response.status_code == 200,
                     "HTTPResponse has status_code: %s" % response.status_code)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
