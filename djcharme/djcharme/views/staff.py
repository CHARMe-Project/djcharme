'''
BSD Licence
Copyright (c) 2017, Science & Technology Facilities Council (STFC)
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

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
This module contains views for staff
'''

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView

from djcharme import __version__
from djcharme.models import Organization
from djcharme.node import get_target_types, get_annotation_count, \
    get_annotation_count_per_organization, get_annotation_count_per_user, \
    get_annotation_count_per_target
from djcharme.node.constants import GRAPH_NAMES


User = get_user_model()


class Status(TemplateView):
    """
    Provide a series of stats to staff.

    """
    template_name = 'staff/status.html'
    model = User

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if not self.request.user.is_staff:
            return redirect(reverse('charme.welcome'))
        return super(Status, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(Status, self).get_context_data(**kwargs)
        context['version'] = __version__
        context['user_count'] = User.objects.count

        old_date = timezone.now() - timezone.timedelta(days=30)
        context['user_count_new_30'] = User.objects.filter(
            date_joined__gte=old_date).count
        context['user_count_last_30'] = User.objects.filter(
            last_login__gte=old_date).count

        old_date = timezone.now() - timezone.timedelta(days=90)
        context['user_count_new_90'] = User.objects.filter(
            date_joined__gte=old_date).count
        context['user_count_last_90'] = User.objects.filter(
            last_login__gte=old_date).count

        old_date = timezone.now() - timezone.timedelta(days=365)
        context['user_count_new_365'] = User.objects.filter(
            date_joined__gte=old_date).count
        context['user_count_last_365'] = User.objects.filter(
            last_login__gte=old_date).count

        graphs = {}
        type_counts = {}
        organization_counts = {}
        user_counts = {}
        target_counts = {}
        for graph_name in GRAPH_NAMES:
            graphs[graph_name] = get_annotation_count(graph_name)
            type_counts[graph_name] = sorted(
                get_target_types(graph_name).items(), key=lambda x: x[1],
                reverse=True)
            organization_counts[graph_name] = sorted(
                get_annotation_count_per_organization(graph_name).items(),
                key=lambda x: x[1], reverse=True)
            user_counts[graph_name] = sorted(get_annotation_count_per_user(
                graph_name).items(), key=lambda x: x[1], reverse=True)[0:9]
            target_counts[graph_name] = sorted(get_annotation_count_per_target(
                graph_name).items(), key=lambda x: x[1], reverse=True)[0:9]

        context['graphs'] = graphs
        context['type_counts'] = type_counts
        context['organization_counts'] = organization_counts
        context['user_counts'] = user_counts
        context['target_counts'] = target_counts

        context['organizations'] = ', '.join(Organization.objects.get_names())

        return context
