from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views

from djcharme.charme_security_model import LoginForm
from djcharme.views import node_gate, endpoint, main_gui, search, \
    registration, resource, facets, auth, staff


admin.autodiscover()

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

IFORMAT = ["atom"]
IFORMATS_RE = '(' + '|'.join(IFORMAT) + ')'

urlpatterns = patterns('',
    # Must be use HTTPS
    # -----------------------------------------------------------
    (r'^admin/', include(admin.site.urls)),
    url(r'^oauth2/', include('provider.oauth2.urls', namespace='oauth2')),

    # ACCOUNTS
    # -----------------------------------------------------------
    # Registation
    url(r'^accounts/registration/$', registration.Registration.as_view(),
        name='registration'),
    # Login
    url(r'^accounts/login/$', auth.Login.as_view(), name='login'),
    # Profile
    url(r'^accounts/profile/$', registration.Profile.as_view(),
        name='profile'),
    # Profile change
    url(r'^accounts/profile/change/$', registration.profile_change,
        name='profile_change'),
    # Password change
    url(r'^accounts/password/change/$', auth_views.password_change,
        name='password_change'),
    url(r'^accounts/password/change/done/$', auth_views.password_change_done,
        name='password_change_done'),
    # Password reset
    url(r'^accounts/password/reset/$', auth_views.password_reset,
        {'post_reset_redirect': '/accounts/password/reset/done/'},
        name="password_reset"),
    url(r'^accounts/password/reset/done/$', auth_views.password_reset_done),
    url(r'^accounts/password/reset/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
        auth_views.password_reset_confirm,
        {'post_reset_redirect': '/accounts/password/reset/complete/'},
        name='password_reset_confirm'),
    url(r'^accounts/password/reset/complete/$',
        auth_views.password_reset_complete),
    # Username reminder
    url(r'^accounts/username/reminder/$', registration.username_reminder,
        name='username_reminder'),
    url(r'^accounts/username/reminder/done$',
        registration.username_reminder_done,
        name='username_reminder_done'),

    # replacement for django_authopenid register
    url(r'^accounts/register/$', auth.Register.as_view(),
        name='user_register'),

    # update for django_authopenid signin complete
    url(r'^accounts/signin/complete/$',
        'django_authopenid.views.complete_signin',
        {'auth_form': LoginForm, 'on_success': auth.signin_success,
         'on_failure': auth.signin_failure},
        name='user_complete_signin'),

    # django_authopenid, we have to explicitly include only the urls we need as
    # some are broken with django > 1.7
    url(r'^/accounts/signin/$', 'django_authopenid.views.signin',
        name='user_signin'),
    url(r'^accounts/signout/$', 'django_authopenid.views.signout',
        name='user_signout'),
    url(r'^accounts/associate/complete/$',
        'django_authopenid.views.complete_associate',
        name='user_complete_associate'),
    url(r'^accounts/associate/$', 'django_authopenid.views.associate',
        name='user_associate'),
    url(r'^accounts/dissociate/$', 'django_authopenid.views.dissociate',
        name='user_dissociate'),

    # -----------------------------------------------------------

    # API - Add new annotation
    url(r'^insert/annotation', node_gate.Insert.as_view(),
        name='node_gate.insert'),

    # API - Modify an annotation
    url(r'^modify/annotation', node_gate.Modify.as_view(),
        name='node_gate.modify'),

    # API - Annotation status management
    url(r'^advance_status', node_gate.AdvanceStatus.as_view(),
        name='advance_status'),

    # API - Follow resources
    url(r'^user/following/(?P<resource_uri>.*)', node_gate.Following.as_view(),
        name='follow_resource'),

    # API - Report annotations
    url(r'^resource/(?P<resource_id>\w+)/reporttomoderator/$',
        node_gate.ReportToModerator.as_view(), name='report_resource'),

    # Display linked data resources
    # API
    url(r'^resource/(?P<resource_id>\w+)', node_gate.Resource.as_view(),
        name='process_resource'),
    # API
    url(r'^data/(?P<resource_id>\w+)', node_gate.ResourceData.as_view(),
        name='process_data'),
    # API/GUI
    url(r'^page/(?P<resource_id>\w+)', node_gate.ResourcePage.as_view(),
        name='process_page'),
    url(r'^annotation/$', resource.annotation, name='annotation'),
    url(r'^activity/$', resource.activity, name='activity'),

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

    # API - Server version
    url(r'^version', node_gate.version),

    # API - Vocab
    url(r'^vocab', node_gate.vocab),

    # Index pages
    url(r'^index/(\w+)', node_gate.Index.as_view(), name='charme.index.id'),
    url(r'^index', node_gate.Index.as_view(), name='index'),

    # GUI - Conditions of use
    url(r'^conditionsofuse/$', main_gui.conditions_of_use),

    # GUI - Following resources
    url(r'^following/$', main_gui.Following.as_view(), name='following-list'),
    url(r'^following/add$', main_gui.FollowingCreate.as_view(),
        name='following-add'),
    url(r'^following/(?P<pk>[0-9]+)/delete/$',
        main_gui.FollowingDelete.as_view(), name='following-delete'),

    # GUI - Staff pages
    url(r'^staff/status/$', staff.Status.as_view(), name='status'),

    # Anything else
    url(r'^', main_gui.welcome, name='charme.welcome'),

)
