
from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin


admin.autodiscover()

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()



urlpatterns = patterns('',

    # Uncomment the next line to enable the admin:
     (r'^admin/', include(admin.site.urls)),
     (r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
)

urlpatterns += patterns('djcharme.views.node_gate',
    (r'^index/(\w+)', 'index'),
)
urlpatterns += patterns('djcharme.views.node_gate',
    (r'^index', 'index'),
)

urlpatterns += patterns('djcharme.views.node_gate',
    (r'^insert/annotation', 'insert'),
)

# CHARMe node resources methods 
urlpatterns += patterns('djcharme.views.node_gate',
    (r'^resource/(\w+)', 'process_resource'),
)

urlpatterns += patterns('djcharme.views.node_gate',
    (r'^data/(\w+)', 'process_data'),
)

urlpatterns += patterns('djcharme.views.node_gate',
    (r'^page/(\w+)', 'process_page'),
)

urlpatterns += patterns('djcharme.views.node_gate',
    (r'^advance_status', 'advance_status'),
)

urlpatterns += patterns('djcharme.views.compose',
    (r'^compose/annotation', 'compose_annotation'),
)

urlpatterns += patterns('djcharme.views.endpoint',
    (r'^endpoint', 'endpoint'),
)

#----------------------
# Open Search
iformat = ["rdf", "turtle", "json-ld"]
iformats_re = '(' + '|'.join(iformat) + ')'

urlpatterns += patterns('djcharme.views.search',
    (r'^search/description', 'get_description'),
)

urlpatterns += patterns('djcharme.views.search',
    (r'^search/' + iformats_re, 'do_search'),
)

urlpatterns += patterns('djcharme.views.main_gui',
    (r'^', 'welcome'),
)
#----------------------