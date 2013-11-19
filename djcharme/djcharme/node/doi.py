'''
Created on 18 Nov 2013

@author: mnagni
'''
from httplib import HTTPConnection
from djcharme.node.actions import ANNO_STABLE, insert_rdf
from djcharme import settings, HTTP_PROXY, HTTP_PROXY_PORT

def __get_document(source, headers = {}, host = 'data.datacite.org', proxy = None, proxy_port = None):
    conn = HTTPConnection(host = host)
    if proxy and proxy_port:
        conn = HTTPConnection(proxy, proxy_port)
    #conn.connect()
    
    if proxy and proxy_port:
        conn.request('GET', 'http://%s/%s' % (host, source), headers = headers)
    else:
        conn.request('GET', source, headers = headers)        
    res = conn.getresponse()
    if res.status in (302, 303):
        conn.request('GET', res.msg['location'], headers = headers)
        res = conn.getresponse()    
    doc = res.read()
    conn.close()
    return doc

def load_doi(doi, graph):
    try:
        id = str(doi)[str(doi).index('//') + 2:]
        
        response = __get_document(id[id.index('/') + 1:].encode("utf8"), 
                                headers = {'accept': 'application/rdf+xml'}, 
                                host = "dx.doi.org",
                                proxy = getattr(settings, HTTP_PROXY),
                                proxy_port = getattr(settings, HTTP_PROXY_PORT))

        insert_rdf(response, 'xml', graph=ANNO_STABLE).serialize(format='turtle')
    except Exception as e:
        #pass                                                             
        print e