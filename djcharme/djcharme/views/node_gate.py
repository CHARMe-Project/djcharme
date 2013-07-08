'''
Created on 14 May 2013

@author: mnagni
'''
from djcharme.node.actions import _do_query
from django.http.response import HttpResponseRedirectBase, Http404, HttpResponse
from djcharme import mm_render_to_response

import logging

LOGGING = logging.getLogger(__name__)

class HttpResponseSeeOther(HttpResponseRedirectBase):
    status_code = 303

def accept_request(request, mime):
    '''
        Verifies if the a given mime-type is into the http request "accept" 
    '''    
    acc = [a.split(';')[0] for a in request.META['HTTP_ACCEPT'].split(',')]
    return mime in acc

SELECT_ANNOTATION = """
    PREFIX an: <http://charm.eu/data/anno/> 
    SELECT ?s ?p ?o
    WHERE {
        an:%s ?p ?o 
    }
"""

SELECT_ANNOTATIONS = """
PREFIX charm: <http://charm.eu/ch#>
SELECT * WHERE {
    ?s a charm:anno .
    ?s ?p ?o 
}
"""

DESCRIBE_ANNOTATIONS = """
PREFIX charm: <http://charm.eu/ch#>
DESCRIBE ?s
WHERE {
  ?s a charm:anno .
}
"""

DESCRIBE_ANNOTATION = """
    PREFIX an: <http://charm.eu/data/anno/> 
    DESCRIBE an:%s 
"""

CONSTRUCT_ANNOTATION = """
PREFIX an: <http://charm.eu/data/anno/>
prefix oa: <http://www.w3.org/ns/oa#>
prefix charm: <http://charm.eu/ch#> 

CONSTRUCT { an:%s ?p ?o .}

WHERE {
 an:%s ?p ?o .
}
"""

def process_data(request, item):
    mainmime = 'application/rdf+xml' 
    #if not accept_request(request, mainmime):
    #    return process_resource(request, item)
    GET_DATA = CONSTRUCT_ANNOTATION % (item, item)
    LOGGING.info("Requesting %s" % GET_DATA)
    results = _do_query(GET_DATA, mainmime)   
    return HttpResponse(results, 
                            mimetype = mainmime)

def _process_page(request, item = None):
    mainmime = 'text/html'    
    if not accept_request(request, mainmime):
        return process_resource(request, item)
    results = None
    if item == None:
        results = _do_query(DESCRIBE_ANNOTATIONS, 'application/rdf+xml')
    else:            
        results = _do_query(DESCRIBE_ANNOTATION % item, 'application/rdf+xml')
        
    context = {'results': results}
    return mm_render_to_response(request, context, 'viewer.html')

def process_page(request, item = None):
    return _process_page(request, item)
    '''
    mainmime = 'text/html'    
    if not accept_request(request, mainmime):
        return process_resource(request, item)
    results = []
    if item == None:
        results = _do_query(SELECT_ANNOTATIONS, 'application/json')
    else:            
        results = _do_query(DESCRIBE_ANNOTATION % item, 'application/json')

    properties = []
    subject = ''
    subj_type = ''
    for subj in results['results']['bindings']:
        subject = subj
        for key in results[subject].keys():
            if key.endswith('#type'):
                subj_type = results[subject][key][0]['value']
                break
     
        for props in results[subject]:
            properties.append({
            'p_name': props[props.rfind('#') + 1:],
            'p_uri': props, 
            'object': results[subject][props][0]})
        
    context = {'subj_type': subj_type, 'properties': properties, 'subj_name': subject[subject.rfind('/') + 1:]}
    return mm_render_to_response(request, context, 'viewer.html')
    '''

def process_resource(request, item=None): 
    if accept_request(request, 'application/rdf+xml'):        
        LOGGING.info("Redirecting to /data/%s" % item)
        return HttpResponseSeeOther('/data/%s' % item)
    if accept_request(request, 'text/html'):
        LOGGING.info("Redirecting to /page/%s" % item)
        return HttpResponseSeeOther('/page/%s' % item)
    return Http404()