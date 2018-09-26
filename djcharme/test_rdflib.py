'''
Created on 17 May 2013

@author: mnagni
'''
# To create an annotation
import datetime
import hashlib

from rdflib import URIRef, Literal
from rdflib.graph import Graph
from rdflib.namespace import Namespace, RDF


GRAPH = Graph()

RESOURCE_HOST = Namespace("http://localhost:8000/resource/")

# Defines some namespaces
CH = Namespace("http://charm.eu/ch#")
OA = Namespace("http://www.w3.org/ns/oa#")
DC = Namespace("http://purl.org/dc/elements/1.1/")

# Generates the future annotation name
m = hashlib.md5()
m.update(str(datetime.datetime.now()))
anno_mau = getattr(RESOURCE_HOST, m.hexdigest())


anno_mau_body = Literal('What a nice dataset')

anno_mau_target = URIRef('http://badc.nerc.ac.uk/view/badc.nerc.ac.uk__ATOM__DE_dcaa78b2-4008-11e0-88c9-00e081470265')

GRAPH.add((anno_mau_target, RDF.type, DC.InteractiveResource))
GRAPH.add((anno_mau_target, DC['format'], Literal("text/html")))

GRAPH.add((anno_mau, RDF.type, CH.anno))
GRAPH.add((anno_mau, OA.hasBody, anno_mau_body))
GRAPH.add((anno_mau, OA.hasTarget, anno_mau_target))

print GRAPH.serialize(format='turtle')



