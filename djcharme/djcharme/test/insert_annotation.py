'''
Created on 31 May 2013

@author: mnagni
'''
import unittest
from djcharme.node.actions import load_file


class Test(unittest.TestCase):


    def setUp(self):
        self.graph = ''
        self.data = '@prefix charm: <http://charm.eu/ch#> . \
        @prefix anno: <http://charm.eu/data/anno/> . \
        @prefix oa: <http://www.w3.org/ns/oa#> . \
        @prefix dc: <http://purl.org/dc/elements/1.1/> . \
        @prefix cnt: <http://www.w3.org/TR/Content-in-RDF10/> . \
        anno:1370011184776 a charm:anno ; \
        oa:hasTarget <http://www.google.com> ; \
        oa:hasBody <http://www.badc.rl.ac.uk> . \
        <http://www.badc.rl.ac.uk> dc:format "text/html" .\
        <http://www.google.com> dc:format "html/text" .'
        
        self.content_type = 'text/turtle'

    def tearDown(self):
        pass


    def testName(self):
        result = load_file(self.graph, self.data, self.content_type)
        self.assertTrue(result, "Failed to load turtle")


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()