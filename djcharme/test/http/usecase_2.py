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
from djcharme.node.constants import SUBMITTED
from djcharme.test import _dump_store, \
    turtle_usecase2_data_citing
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

    def test_usecase_2(self):
        response = insert(self.factory.post('/insert/annotation',
                                            content_type='text/turtle',
                                            data=turtle_usecase2_data_citing))
        self.assert_(response.status_code == 200,
                     "HTTPResponse has status_code: %s" % response.status_code)

        _dump_store()


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
