'''
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
from djcharme.node.actions import resource_exists
from djcharme.node.look_ups import is_following_resource


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

