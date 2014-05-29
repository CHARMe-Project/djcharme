from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.views import login

from djcharme.charme_security_model import LoginForm
from djcharme.views import node_gate, compose, endpoint, main_gui, search, \
    registration, facets, views


admin.autodiscover()

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

iformat = ["atom"]
iformats_re = '(' + '|'.join(iformat) + ')'

urlpatterns = patterns('',
     # Must be use HTTPS
     #-----------------------------------------------------------
     (r'^admin/', include(admin.site.urls)),
     url(r'^oauth2/', include('provider.oauth2.urls', namespace='oauth2')),

     # Registation
     url(r'^accounts/registration/$',
         registration.registration,
         name='registration'),
     # Login
     url(r'^accounts/login/$',
         login,
         kwargs={'template_name': 'login.html',
                 'authentication_form': LoginForm},
         name='login'),
     # Logout
     url(r'^accounts/logout/$', views.logout_view,),

     # Accepts external new annotation
     url(r'^insert/annotation', node_gate.insert, name='node_gate.insert'),
     # Annotation status management
     url(r'^advance_status/(\w+)', node_gate.advance_status,
         name='advance_status'),
     #-----------------------------------------------------------

     # Display linked data resources
     url(r'^resource/(\w+)', node_gate.process_resource,
         name='process_resource'),
     url(r'^data/(\w+)', node_gate.process_data, name='process_data'),
     url(r'^page/(\w+)', node_gate.process_page, name='process_page'),

     # Annotation composition
     url(r'^compose/annotation', compose.compose_annotation,
         name='compose_annotation'),

     # HTTP SPARQL implementation
     url(r'^endpoint', endpoint.endpoint, name='endpoint'),

     # Opensearch
     url(r'^search/description', search.get_description,
         name='os_description'),
     url(r'^search/' + iformats_re, search.do_search, name='os_search'),

     # Tokens
     url(r'^token/validate/(?P<token>\w+)/(?P<expire>\w+)',
         registration.validate_token, name='validate_token'),
     url(r'^token/validate', registration.validate_token,
         name='validate_token'),
     url(r'^token/test', registration.test_token, name='test_token'),
     url(r'^token/response', registration.token_response,
         name='token_response'),
     url(r'^token/userinfo', registration.userinfo, name='userinfo'),

     # Facets
     url(r'^facets/test', facets.test_facets, name='test_facets'),

     # Index pages
     url(r'^index/(\w+)', node_gate.index, name='charme.index.id'),
     url(r'^index', node_gate.index, name='index'),
     url(r'^', main_gui.welcome, name='charme.welcome'),

)
