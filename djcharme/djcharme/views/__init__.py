from djcharme.node.actions import FORMAT_MAP

def isGET(request):
    return request.method == 'GET'

def isPUT(request):
    return request.method == 'PUT'

def isDELETE(request):
    return request.method == 'DELETE'

def isPOST(request):
    return request.method == 'POST'

def isHEAD(request):
    return request.method == 'HEAD'

def isPATCH(request):
    return request.method == 'PATCH'

def content_type(request):
    return request.environ.get('CONTENT_TYPE', None)

def http_accept(request):
    return request.META.get('HTTP_ACCEPT', None)

def validateMimeFormat(request):
    req_format = http_accept(request)
    if req_format:
        for k,v in FORMAT_MAP.iteritems():
            if req_format == v:
                return k
    return None 

'''
        SELECT Distinct ?g ?s ?p ?o
        WHERE {
           GRAPH ?g {
             ?s ?p ?o .
           } 
        }
'''