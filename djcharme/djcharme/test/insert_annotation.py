'''
Created on 31 May 2013

@author: mnagni
'''
import unittest
from djcharme.node.actions import insert_rdf,\
    _formatNodeURIRef, ANNO_SUBMITTED
from rdflib.graph import Graph, ConjunctiveGraph
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.term import URIRef

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
        
        
        self.graph = 'submitted'
        self.identifier = '%s/%s' % (SPARQL_DATA, self.graph)
        self.g = Graph(store=self.store, identifier=self.identifier)
        self.gs = Graph(store=self.graphstore, identifier=self.identifier)        
        
        self.rdf_data = '''
            <rdf:RDF
               xmlns:ns1="http://www.w3.org/2011/content#"
               xmlns:ns2="http://www.w3.org/ns/oa#"
               xmlns:ns3="http://purl.org/dc/elements/1.1/"
               xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
              <rdf:Description rdf:about="http://charm.eu/data/anno/a_1374142212954">
                <rdf:type rdf:resource="http://charm.eu/ch#anno"/>
                <ns2:hasTarget rdf:resource="http://localhost:8001/ca960608.dm3"/>
                <ns2:hasBody rdf:resource="http://charm.eu/data/anno/b_1374142212953"/>
              </rdf:Description>
              <rdf:Description rdf:about="http://localhost:8001/ca960608.dm3">
                <ns3:format>html/text</ns3:format>
              </rdf:Description>
              <rdf:Description rdf:about="http://charm.eu/data/anno/b_1374142212953">
                <rdf:type rdf:resource="http://purl.org/dc/dcmitype/Text"/>
                <rdf:type rdf:resource="http://www.w3.org/2011/content#ContentAsText"/>
                <ns3:format>text/plain</ns3:format>
                <ns1:chars>hello there!</ns1:chars>
              </rdf:Description>
            </rdf:RDF>
        '''
        
        self.turtle_data = '''
            @prefix charm: <http://charm.eu/ch#> . 
            @prefix anno: <nodeURI/> . 
            @prefix oa: <http://www.w3.org/ns/oa#> . 
            @prefix dc: <http://purl.org/dc/elements/1.1/> . 
            @prefix cnt: <http://www.w3.org/2011/content#> . 
            @prefix dctypes: <http://purl.org/dc/dcmitype/> . 
            
            anno:annoURI a charm:anno ;
            oa:hasTarget <http://localhost:8001/ca960608.dm3> ;
            oa:hasBody anno:bodyURI .
    
            anno:bodyURI
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
    
    '''
    def tearDown(self):   
        for res in self.g:
            self.g.remove(res)
    '''


    def test_insert_turtle(self):
        insert_rdf(self.turtle_data, 'text/turtle', graph=ANNO_SUBMITTED)

    '''
    def test_insert_jsonld(self):
        insert_rdf(self.jsonld_data, 'application/ld+json', graph=ANNO_SUBMITTED)
        
    def test_insert_rdf(self):
        insert_rdf(self.rdf_data, 'application/rdf+xml', graph=ANNO_SUBMITTED)   
        
    def test_formatNode(self):
        tmpURIRef = URIRef('file:///home/users/mnagni/git/djcharme/djcharme/djcharme/test/nodeURI/annoURI')
        res = _formatNodeURIRef(tmpURIRef, 'abcdef', '123456')
        self.assert_('abcdef' in res, "Error")
        self.assertFalse('nodeURI' in res, "Error")
        self.assertFalse('annoURI' in res, "Error")
        self.assertFalse('123456' in res, "Error")
    '''


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()