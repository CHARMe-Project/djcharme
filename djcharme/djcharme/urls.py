from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.views import login
from django.contrib.auth import views as auth_views

from djcharme.charme_security_model import LoginForm
from djcharme.views import node_gate, compose, endpoint, main_gui, search, \
    registration, facets, views


admin.autodiscover()

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

IFORMAT = ["atom"]
IFORMATS_RE = '(' + '|'.join(IFORMAT) + ')'

urlpatterns = patterns('',
    # Must be use HTTPS
    #-----------------------------------------------------------
    (r'^admin/', include(admin.site.urls)),
    url(r'^oauth2/', include('provider.oauth2.urls', namespace='oauth2')),

    # ACCOUNTS
    #-----------------------------------------------------------
    # Registation
    url(r'^accounts/registration/$', registration.registration,
        name='registration'),
    # Login
    url(r'^accounts/login/$', login,
        kwargs={'template_name': 'login.html',
                'authentication_form': LoginForm},
        name='login'),
    # Logout
    url(r'^accounts/logout/$', views.logout_view,),
    # Profile
    url(r'^accounts/profile/change/$', registration.profile_change,
        name='profile_change'),
    url(r'^accounts/profile/change/done/$', registration.profile_change_done,
        name='profile_change_done'),
    # Password change
    url(r'^accounts/password/change/$', auth_views.password_change,
        name='password_change'),
    url(r'^accounts/password/change/done/$', auth_views.password_change_done,
        name='password_change_done'),
    # Password reset
    url(r'^accounts/password/reset/$', auth_views.password_reset,
        {'post_reset_redirect' : '/accounts/password/reset/done/'},
        name="password_reset"),
    url(r'^accounts/password/reset/done/$', auth_views.password_reset_done),
    url(r'^accounts/password/reset/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
        auth_views.password_reset_confirm,
        {'post_reset_redirect' : '/accounts/password/reset/complete/'},
        name='password_reset_confirm'),
    url(r'^accounts/password/reset/complete/$',
        auth_views.password_reset_complete),
    #-----------------------------------------------------------

    # Accepts external new annotation
    url(r'^insert/annotation', node_gate.insert, name='node_gate.insert'),

    # Modify an annotation
    url(r'^modify/annotation', node_gate.modify, name='node_gate.modify'),

    # Annotation status management
    url(r'^advance_status/', node_gate.advance_status,
        name='advance_status'),

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
    url(r'^search/' + IFORMATS_RE, search.do_search, name='os_search'),
    url(r'^suggest/description', search.get_description,
        name='os_description'),
    url(r'^suggest/' + IFORMATS_RE, search.do_suggest, name='os_search'),

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

    # Server version
    url(r'^version', node_gate.version),

    # Index pages
    url(r'^index/(\w+)', node_gate.index, name='charme.index.id'),
    url(r'^index', node_gate.index, name='index'),

    # Anything else
    url(r'^', main_gui.welcome, name='charme.welcome'),

)
