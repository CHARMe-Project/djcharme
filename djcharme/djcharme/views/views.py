from django.contrib.auth import logout
from django.http.response import HttpResponseRedirect


def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/welcome')
