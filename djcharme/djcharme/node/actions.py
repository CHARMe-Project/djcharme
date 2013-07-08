'''
Created on 12 Apr 2013

@author: mnagni
'''

from rdflib import Graph, URIRef
import httplib2
import urllib
from SPARQLWrapper.Wrapper import SPARQLWrapper, XML, JSON, RDF
import json
import logging

LOGGING = logging.getLogger(__name__)

#SPARQL_QUERY = "http://localhost:3030/charmenode/sparql?%s"
#SPARQL_QUERY = "http://localhost:3333/charmenode/sparql?%s"
#SPARQL_UPDATE = "http://localhost:3333/charmenode/data?%s"

SPARQL_QUERY = "http://localhost:3333/publicds/sparql"
#SPARQL_QUERY = "http://localhost:3333/charmenode/sparql?%s"
SPARQL_UPDATE = "http://localhost:3333/privateds/data"

def get_by_known_namespace():
    g = Graph()
    #g.parse(location=http://dbpedia.org/resource/Elvis_Presley")
    g.parse(location="http://localhost:8080/openrdf-sesame/repositories/firstTest/rdf-graphs/service?default")
    for stmt in g.subject_predicates(URIRef("charm:anno")):
        print stmt

def load_file(defaultGraph, data, content_type='text/turtle'):
    #return _do_query(data, defaultGraph)
    params = { 'graph': defaultGraph }    
    endpoint = SPARQL_UPDATE# + "?" + urllib.urlencode(params)
    insert_rdf(endpoint, data, content_type)
    return True

def do_query(query):
    params = { 'query': query }    
    endpoint = SPARQL_QUERY % (urllib.urlencode(params))       
    return get_by_sparql(endpoint)

def do_update(data, defaultGraph):
    return _do_query(data, defaultGraph)

def _do_query(query, mimetype = None, endpoint = None, defaultGraph = None):
    ret_format = None
    if mimetype == 'application/json':
        ret_format = JSON    
    if mimetype == 'application/rdf+xml':
        ret_format = RDF        
    
    results = __do_query(query, ret_format, defaultGraph)
    
    #Is an update
    if mimetype == None:
        return True

    if not results:
        return ""
        
    if hasattr(results, 'read') and results.headers.type == 'application/rdf+json':
        return json.load(results)
    
    if ret_format == RDF:
        res = results.read()
        return res
    return results

def __do_query(query, ret_format = None, defaultGraph = None):
    sparql = SPARQLWrapper(SPARQL_QUERY, updateEndpoint=SPARQL_UPDATE, defaultGraph=defaultGraph)
    sparql.setQuery(query)
    
    if ret_format:
        sparql.setReturnFormat(ret_format)
        return sparql.query().convert()
    else:
        return sparql.query()

    

def get_by_sparql(endpoint):
    """
        Executes a query
    """
    (response, content) = httplib2.Http().request(endpoint, 'GET')
    LOGGING.info("Getting: \n %s \n Response: %s" % (endpoint, response.status))
    return content


def insert_rdf(endpoint, data, content_type):
    """
        Inserts a turtle file
    """
    (response, content) = httplib2.Http().request(endpoint, 'PUT', body=data, headers={ 'content-type': content_type })
    LOGGING.info("Inserting: \n %s \n Response: %s" % (data, response.status))
