'''
Created on 18 Nov 2013

@author: mnagni
'''
from httplib import HTTPConnection

from djcharme import settings, HTTP_PROXY, HTTP_PROXY_PORT
from djcharme.node.actions import insert_rdf
from djcharme.node.constants import SUBMITTED


def get_document(source, headers={}, host='data.datacite.org', proxy=None,
                 proxy_port=None, params=None):
    conn = HTTPConnection(host=host)
    if proxy and proxy_port:
        conn = HTTPConnection(proxy, proxy_port)
    # conn.connect()

    request_url = source

    if proxy and proxy_port:
        request_url = 'http://%s/%s' % (host, source)

    if request_url[-1] == '/':
        request_url = request_url[:len(request_url) - 1]
    if params:
        request_url = '%s?%s' % (request_url, params)

    conn.request('GET', request_url, headers=headers)
    res = conn.getresponse()
    if res.status in (302, 303):
        conn.request('GET', res.msg['location'], headers=headers)
        res = conn.getresponse()
    doc = res.read()
    conn.close()
    return doc


def load_doi(doi, graph, user):
    try:
        _id = str(doi)[str(doi).index('//') + 2:]

        response = get_document(_id[_id.index('/') + 1:].encode("utf8"),
                                headers={'accept': 'application/rdf+xml'},
                                host="dx.doi.org",
                                proxy=getattr(settings, HTTP_PROXY),
                                proxy_port=getattr(settings, HTTP_PROXY_PORT))

        insert_rdf(response, 'xml', user,
                   graph=SUBMITTED).serialize(format='turtle')
    except Exception as ex:
        # pass
        print ex
