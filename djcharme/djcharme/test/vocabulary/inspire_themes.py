'''
Created on 19 Nov 2013

@author: mnagni
'''
import unittest
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.graph import Graph
from djcharme.node.doi import get_document
from urllib import urlencode


class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def testInspireThemes(self):
        INSPIRE_SPARQL_ENDPOINT = "semantic.eea.europa.eu/sparql"
        #INSPIRE_SPARQL_ENDPOINT = "vocab.nerc.ac.uk/sparql"
        
        params = {'query': "SELECT * WHERE {<http://eurovoc.europa.eu/89> ?p ?o } "}
        #params = {'query': "SELECT * WHERE {<http://eurovoc.europa.eu/89> ?p ?o } "}
        
        inspire_store = SPARQLUpdateStore(queryEndpoint = INSPIRE_SPARQL_ENDPOINT, 
                        postAsEncoded=False)

        

        response = get_document('', 
                                headers = {'accept': 'application/rdf+xml'}, 
                                host = INSPIRE_SPARQL_ENDPOINT,
                                proxy = 'wwwcache.rl.ac.uk',
                                proxy_port = 8080,
                                params=urlencode(params))

        print response
        '''
        graph = Graph()
        

        
        response = graph.query(select_themes)
        for theme in response:
            print theme
        '''

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()