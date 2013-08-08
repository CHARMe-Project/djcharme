def isPOST(request):
    return request.method == 'POST'

def isGET(request):
    return request.method == 'GET'

def hasContentType(request, mimetype):
    return mimetype in request.environ.get('CONTENT_TYPE', None) 