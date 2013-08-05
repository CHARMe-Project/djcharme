def isPOST(request):
    return request.method == 'POST'

def isGET(request):
    return request.method == 'GET'