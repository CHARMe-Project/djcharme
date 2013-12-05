from djcharme.node.actions import FORMAT_MAP

FORMAT = 'format'
DEPTH = 'depth'

def isGET(request):
    return request.method == 'GET'

def isPUT(request):
    return request.method == 'PUT'

def isDELETE(request):
    return request.method == 'DELETE'

def isPOST(request):
    return request.method == 'POST'

def isOPTIONS(request):
    return request.method == 'OPTIONS'

def isHEAD(request):
    return request.method == 'HEAD'

def isPATCH(request):
    return request.method == 'PATCH'

def content_type(request):
    return request.environ.get('CONTENT_TYPE', None).split(';')[0]

def get_format(request):
    try:
        return request.GET[FORMAT]
    except KeyError:
        return None

def get_depth(request):
    depth = request.GET.get(DEPTH, 1)
    if depth is not None:
        try:    
            return int(depth)
        except ValueError:
            return None
    return None

def http_accept(request):
    accept = request.META.get('HTTP_ACCEPT', None)
    if accept is None:
        return None
    return accept.split(';')[0].split(',')

def checkMimeFormat(mimeformat):
    if '/' in mimeformat:
        for k,v in FORMAT_MAP.iteritems():
            if v in mimeformat:
                return k
    else:
        for k,v in FORMAT_MAP.iteritems():
            if k in mimeformat:
                return k

def validateMimeFormat(request):
    req_format = [get_format(request)] 
    if req_format[0] is None: 
        req_format = http_accept(request)

    for mimeformat in req_format:
        ret = checkMimeFormat(mimeformat)
        if ret is not None:
            return ret        
    return None 

'''
        SELECT Distinct ?g ?s ?p ?o WHERE { GRAPH ?g { ?s ?p ?o . }}
'''