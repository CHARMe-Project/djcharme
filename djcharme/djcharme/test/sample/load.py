'''
Created on 15 Nov 2013

@author: mnagni
'''
import unittest
import csv
from httplib import HTTPConnection
from djcharme.node.actions import ANNO_SUBMITTED, insert_rdf, \
    ANNO_STABLE
from rdflib.term import URIRef
from djcharme.node.sample import load_sample







class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def testLoad(self):
        #pass
        load_sample()

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testLoad']
    unittest.main()