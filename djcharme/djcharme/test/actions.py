'''
Created on 2 Aug 2013

@author: mnagni
'''
import unittest
from djcharme.node.actions import format_graphIRI
from djcharme.views.node_gate import index


class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass        

    def testName(self):

        format_graphIRI('myGraph', baseurl = 'http://localhost')


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()