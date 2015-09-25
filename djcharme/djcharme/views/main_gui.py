'''
BSD Licence
Copyright (c) 2015, Science & Technology Facilities Council (STFC)
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice,
        this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
        this list of conditions and the following disclaimer in the
        documentation and/or other materials provided with the distribution.
    * Neither the name of the Science & Technology Facilities Council (STFC)
        nor the names of its contributors may be used to endorse or promote
        products derived from this software without specific prior written
        permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


Contents:
This module contains views of the user pages, excluding login and registration.

Created on 19 Aug 2013

@author: mnagni
'''
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.forms.forms import NON_FIELD_ERRORS
from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView, DeleteView
from django.views.generic.list import ListView

from djcharme import mm_render_to_response
from djcharme.models import FollowedResource
from djcharme.node import is_following_resource, resource_exists


def welcome(request):
    """
    Display the welcome page.

    """
    context = {}
    return mm_render_to_response(request, context, 'welcome.html')


def conditions_of_use(request):
    """
    Display the conditions of use.

    """
    context = {}
    return mm_render_to_response(request, context, 'conditions_of_use.html')


class Following(ListView):
    """
    Display the list of resources that are being followed by the user.

    """

    def get(self, request):
        following = self.get_queryset()
        if len(following) == 0:
            return redirect(reverse('following-add'))
        context = {'followed_resource' : following}
        return render(request,
                      'followed-resources/followed_resource.html',
                      context)
    
    def get_queryset(self):
        """
        Return the resources followed by the user.

        """
        return FollowedResource.objects.filter(
            user=self.request.user
        ).order_by('resource')


class FollowingCreate(CreateView):
    """
    Add a resource to the list of resources that are being followed by the user.

    """
    model = FollowedResource
    fields = ['resource']
    template_name = 'followed-resources/followed_resource_form.html'
    success_url = reverse_lazy('following-list')
        
    def form_valid(self, form):
        """
        Validate the form. Check that the user is not already following the
        resource and that the resource exists in the triple store.
        
        """
        if is_following_resource(self.request.user, form.instance.resource.strip()):
            form.full_clean()
            form._errors[NON_FIELD_ERRORS] = form.error_class(['You are already following this resource'])
            form.non_field_errors()
            return super(FollowingCreate, self).form_invalid(form)            

        if not (resource_exists(form.instance.resource.strip())):
            form.full_clean()
            form._errors[NON_FIELD_ERRORS] = form.error_class(['Resource does not exist on this system'])
            form.non_field_errors()
            return super(FollowingCreate, self).form_invalid(form)

        form.instance.user = self.request.user
        return super(FollowingCreate, self).form_valid(form)

    
class FollowingDelete(DeleteView):
    """
    Delete the resource that is being followed by the user.

    """
    model = FollowedResource
    template_name = 'followed-resources/followed_resource_confirm_delete.html'   
    success_url = reverse_lazy('following-list')

