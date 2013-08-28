'''
Created on 31 May 2013

@author: mnagni
'''
import unittest
from djcharme.node.actions import insert_rdf,\
    _formatNodeURIRef, ANNO_SUBMITTED
from rdflib.graph import Graph
from rdflib.term import URIRef
from djcharme.local_settings import SPARQL_DATA
from djcharme.charme_middleware import CharmeMiddleware
from djcharme.test import turtle_data, jsonld_data, rdf_data

class Test(unittest.TestCase):


    def setUp(self):
        self.store = CharmeMiddleware.get_store(debug = True)
        
        
        self.graph = 'submitted'
        self.identifier = '%s/%s' % (SPARQL_DATA, self.graph)
        self.g = Graph(store=self.store, identifier=self.identifier)        
        
        '''
        SELECT Distinct ?g ?s ?p ?o
        WHERE {
           GRAPH ?g {
             ?s ?p ?o .
           } 
        }
        '''

    def tearDown(self):   
        for res in self.g:
            self.g.remove(res)

    def test_insert_turtle(self):
        tmp_g = insert_rdf(turtle_data, 'text/turtle', graph=ANNO_SUBMITTED)
        final_doc = tmp_g.serialize()
        print tmp_g.serialize()
        self.assertFalse('localhost' in final_doc, "Error ingesting turtle")
        self.assertFalse('annoID' in final_doc, "Error ingesting turtle")
        self.assertFalse('bodyID' in final_doc, "Error ingesting turtle")
        self.assertFalse('chnode: <nodeURI/>' in final_doc, "Error ingesting turtle")
        self.assertFalse('chnode:annoID' in final_doc, "Error ingesting turtle")
        self.assertFalse('chnode:bodyID' in final_doc, "Error ingesting turtle")
        
    def test_insert_jsonld(self):
        tmp_g = insert_rdf(jsonld_data, 'application/ld+json', graph=ANNO_SUBMITTED)
        final_doc = tmp_g.serialize()
        print tmp_g.serialize()        
        self.assertFalse('localhost' in final_doc, "Error ingesting jsonld")
        self.assertFalse('annoID' in final_doc, "Error ingesting jsonld")
        self.assertFalse('bodyID' in final_doc, "Error ingesting jsonld")
        self.assertFalse('localhost/bodyID' in final_doc, "Error ingesting jsonld")
        self.assertFalse('localhost/annoID' in final_doc, "Error ingesting jsonld")  
    
    def test_insert_rdf(self):
        tmp_g = insert_rdf(rdf_data, 'application/rdf+xml', graph=ANNO_SUBMITTED)
        final_doc = tmp_g.serialize()
        print tmp_g.serialize()
        self.assertFalse('localhost' in final_doc, "Error ingesting rdf")
        self.assertFalse('annoID' in final_doc, "Error ingesting rdf")
        self.assertFalse('bodyID' in final_doc, "Error ingesting rdf")
        self.assertFalse('localhost/bodyID' in final_doc, "Error ingesting rdf")
        self.assertFalse('localhost/annoID' in final_doc, "Error ingesting rdf")            
            
    def test_formatNode(self):
        tmpURIRef = URIRef('http://localhost/annoID')
        res = _formatNodeURIRef(tmpURIRef, 'abcdef', '123456')
        self.assertFalse('annoID' in res, "Error")



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()