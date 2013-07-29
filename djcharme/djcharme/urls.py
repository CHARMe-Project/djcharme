
from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin

from django.conf import settings


admin.autodiscover()

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns("", 
    # Change the admin prefix here to use an alternate URL for the
    # admin interface, which would be marginally more secure.
    ("^admin/", include(admin.site.urls)),
)

urlpatterns += patterns('djcharme.views.node_gate',
    (r'^index/(\w+)', 'index'),
)

urlpatterns += patterns('djcharme.views.node_gate',
    (r'^insert/annotation', 'insert'),
)

urlpatterns += patterns('djcharme.views.node_gate',
    (r'^require/annotationTicket', 'annoTickets'),
)

urlpatterns += patterns('djcharme.views.node_gate',
    (r'^resource/(\w+)', 'process_resource'),
)

urlpatterns += patterns('djcharme.views.node_gate',
    (r'^data/(\w+)', 'process_data'),
)

urlpatterns += patterns('djcharme.views.node_gate',
    (r'^page/(\w+)', 'process_page'),
)

urlpatterns += patterns('djcharme.views.compose',
    (r'^compose/annotation', 'compose_annotation'),
)

urlpatterns += patterns('djcharme.views.demo',
    (r'^demo', 'demo'),
)