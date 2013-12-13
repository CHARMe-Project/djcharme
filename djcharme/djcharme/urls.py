from django.contrib import admin
from django.conf.urls import patterns, include, url
from djcharme.views import node_gate, compose, endpoint, main_gui, search, \
    registration
from django.contrib.auth.views import login
from djcharme.charme_security_model import LoginForm


admin.autodiscover()

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

iformat = ["atom"]
iformats_re = '(' + '|'.join(iformat) + ')'

urlpatterns = patterns('',

    # Uncomment the next line to enable the admin:
     (r'^admin/', include(admin.site.urls)),
          
     # Registation
     url(r'^accounts/registration/$', registration.registration, 
         name='registration'),
     # Login                       
     url(r'^accounts/login/$', login, kwargs={'template_name': 'login.html',
                                            'authentication_form': LoginForm,
                                            'redirect_field_name': 'logged_in'},  
         name='login'),                                                
     
     #Display linked data resources
     url(r'^resource/(\w+)', node_gate.process_resource, 
         name='process_resource'),   
     url(r'^data/(\w+)', node_gate.process_data, name='process_data'),
     url(r'^page/(\w+)', node_gate.process_page, name='process_page'),
     
     #Annotation status management     
     url(r'^advance_status/(\w+)', node_gate.advance_status, 
         name='advance_status'),
                       
     #Annotation composition                       
     url(r'^compose/annotation', compose.compose_annotation, 
         name='compose_annotation'),

    #Accepts external new annotation
     url(r'^insert/annotation', node_gate.insert, name='insert'),

     #HTTP SPARQL implementation                       
     url(r'^endpoint', endpoint.endpoint, name='endpoint'),
     
     #Opensearch
     url(r'^search/description', search.get_description, 
         name='os_description'),
     url(r'^search/' + iformats_re, search.do_search, name='os_search'),
     
     #Index pages
     url(r'^index/(\w+)', node_gate.index, name='index'),
     url(r'^index', node_gate.index, name='index'),                                              
     url(r'^', main_gui.welcome, name='welcome'),
)