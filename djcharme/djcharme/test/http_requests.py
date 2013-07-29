'''
Created on 25 Jul 2013

@author: mnagni
'''
import unittest
from django.test.client import RequestFactory
from djcharme.views.node_gate import index
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.graph import Graph


class Test(unittest.TestCase):


    def setUp(self):
        FUSEKI_URL = 'http://localhost:3333/privateds'
        
        SPARQL_UPDATE = FUSEKI_URL + '/update'
        SPARQL_QUERY = FUSEKI_URL + '/sparql'
        SPARQL_DATA = FUSEKI_URL + '/data'

        GRAPH_STORE_R = FUSEKI_URL + '/get'
        GRAPH_STORE_RW = FUSEKI_URL + '/data'
                        
        self.store = SPARQLUpdateStore(queryEndpoint = SPARQL_QUERY,
                                       update_endpoint = SPARQL_UPDATE)
        
        self.graphstore = SPARQLUpdateStore(queryEndpoint = GRAPH_STORE_R,
                                       update_endpoint = GRAPH_STORE_RW)
        
        self.graph = 'stable'
        self.identifier = '%s/%s' % (SPARQL_DATA, self.graph)
        self.g = Graph(store=self.store, identifier=self.identifier)
        self.gs = Graph(store=self.graphstore, identifier=self.identifier)        
        
        self.turtle_data = '''
            @prefix charm: <http://charm.eu/ch#> . 
            @prefix anno: <http://charm.eu/data/anno/> . 
            @prefix oa: <http://www.w3.org/ns/oa#> . 
            @prefix dc: <http://purl.org/dc/elements/1.1/> . 
            @prefix cnt: <http://www.w3.org/2011/content#> . 
            @prefix dctypes: <http://purl.org/dc/dcmitype/> . 
            
            anno:a_1374142212954 a charm:anno ;
            oa:hasTarget <http://localhost:8001/ca960608.dm3> ;
            oa:hasBody anno:b_1374142212953 .
    
            anno:b_1374142212953
            a cnt:ContentAsText, dctypes:Text ;
            cnt:chars "hello there!" ;
            dc:format "text/plain" .
            <http://localhost:8001/ca960608.dm3>
            dc:format "html/text" .
        '''
        
        self.jsonld_data = '''
            {
                "@graph": [
                    {
                        "@id": "http://charm.eu/data/anno/b_1374142212953",
                        "@type": [
                            "http://www.w3.org/2011/content#ContentAsText",
                            "http://purl.org/dc/dcmitype/Text"
                        ],
                        "http://purl.org/dc/elements/1.1/format": "text/plain",
                        "http://www.w3.org/2011/content#chars": "hello there!"
                    },
                    {
                        "@id": "http://charm.eu/data/anno/a_1374142212954",
                        "@type": "http://charm.eu/ch#anno",
                        "http://www.w3.org/ns/oa#hasBody": {
                            "@id": "http://charm.eu/data/anno/b_1374142212953"
                        },
                        "http://www.w3.org/ns/oa#hasTarget": {
                            "@id": "http://localhost:8001/ca960608.dm3"
                        }
                    },
                    {
                        "@id": "http://localhost:8001/ca960608.dm3",
                        "http://purl.org/dc/elements/1.1/format": "html/text"
                    }
                ]
            }        
        '''
        g = Graph()        
        g.parse(data = self.turtle_data, format = 'text/turtle')        
        for res in g:
            self.g.add(res)
        
        self.factory = RequestFactory()


    def tearDown(self):        
        for res in self.g:
            self.g.remove(res)


    def test_get_index(self):
        # Create an instance of a GET request.
        request = self.factory.get('/index/stable')
        request.META['HTTP_ACCEPT'] = 'application/rdf+xml'  
        self.assert_('hasTarget' in str(index(request, 'stable')), 
                     "Cannot generate index page")

        request = self.factory.get('/index/retired')
        request.META['HTTP_ACCEPT'] = 'application/rdf+xml' 
        self.assert_('hasTarget' not in  str(index(request, 'retired')), 
                     "Cannot generate index page")

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_get_index']
    unittest.main()