'''
Created on 19 Aug 2013

@author: mnagni
'''
from djcharme import mm_render_to_response

def welcome(request):                
    context = {}
    return mm_render_to_response(request, context, 'welcome.html')