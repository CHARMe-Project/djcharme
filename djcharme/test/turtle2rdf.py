'''
Created on 18 Jul 2013

@author: mnagni
'''
import unittest
from rdflib.graph import Graph
import logging

LOGGING = logging.getLogger(__name__)

class Test(unittest.TestCase):

    def setUp(self):
        self.turtle_source = '''
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


    def tearDown(self):
        pass


    def testTurtleEqualToJSONLD(self):
        g = Graph()
        LOGGING.info("Parsing turtle into rdflib Graph...")
        g.parse(data=self.turtle_source, format='turtle')

        LOGGING.info("Serializing Graph into JSON-LD...")        
        rdf_json = g.serialize(format='json-ld', indent=4)
        
        new_g = Graph()
        LOGGING.info("Parsing json-ld into a new rdflib Graph...")
        new_g.parse(data=rdf_json, format='json-ld')
        
        LOGGING.info("Comparing the two rdflib Graphs")
        self.assertTrue(g.isomorphic(new_g), "Graphs are different FAILED")  


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()