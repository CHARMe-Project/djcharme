'''
Created on 4 Feb 2014

@author: mnagni
'''
from djcharme import mm_render_to_response


def test_facets(request):
    return mm_render_to_response(request, {}, 'facets_test.html')
