'''
Created on 25 Jul 2013

@author: mnagni
'''


import logging
import unittest
from urllib import urlencode

from django.contrib.auth.models import User
from django.test.client import RequestFactory
from rdflib.graph import Graph

from djcharme import settings
from djcharme.charme_middleware import CharmeMiddleware
from djcharme.node.actions import FORMAT_MAP, ANNO_STABLE, ANNO_SUBMITTED
from djcharme.test import _prepare_get, test_insert_anotation, turtle_usecase1, \
    extract_annotation_uri
from djcharme.views.search import get_description, do_search


LOGGING = logging.getLogger(__name__)

class Test(unittest.TestCase):

    def setUp(self):
        self.store = CharmeMiddleware.get_store(debug=True)


        self.graph = 'submitted'
        self.identifier = '%s/%s' % (getattr(settings, 'SPARQL_DATA'),
                                     self.graph)
        self.g = Graph(store=self.store, identifier=self.identifier)
        self.factory = RequestFactory()

        users = User.objects.filter(username='Alberto Sordi')
        if users.count() == 0:
            self.user = User.objects.create_user('Alberto Sordi',
                                                 'albertone@sordi.com',
                                                 'ammericano')

    def tearDown(self):
        for res in self.g:
            self.g.remove(res)
        if hasattr(self, 'user'):
            self.user.delete()

    def test_getOSDescription(self):
        request = _prepare_get(self.factory, '/search/description')
        request.META['HTTP_ACCEPT'] = "text/html"
        print get_description(request)

    def test_doSearch(self):
        test_insert_anotation(self,
                          http_accept='application/rdf+xml',
                          content_type='text/turtle',
                          data=turtle_usecase1)

        params = {'title': 'L*', 'status': ANNO_SUBMITTED, 'format': 'json-ld'}
        request = _prepare_get(self.factory, '/search/atom?%s' %
                               urlencode(params))
        request.META['HTTP_ACCEPT'] = "application/atom+xml"
        response = do_search(request, 'atom')
        # print response.content
        self.assertIn('Lost Letter Measure of Variation in Altruistic Behaviour in 20 Neighbourhoods',
                      response.content, "Error!")

        params = {'title': 'L*'}
        params = {'title': 'L*', 'status': ANNO_SUBMITTED, 'format': 'xml'}
        request = _prepare_get(self.factory, '/search/atom?%s' %
                               urlencode(params))
        request.META['HTTP_ACCEPT'] = "application/atom+xml"
        response = do_search(request, 'atom')
        # print response.content
        self.assertIn('Lost Letter Measure of Variation in Altruistic Behaviour in 20 Neighbourhoods',
                      response.content, "Error!")
        return response


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.test_get_index']
    unittest.main()
