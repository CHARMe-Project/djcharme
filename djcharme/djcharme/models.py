"""
Custom models.

"""
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from provider.oauth2.models import Client


AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class FollowedResource(models.Model):
    """
    The resource followed by a user.

    """
    user = models.ForeignKey(User,
                             help_text=
                             'The user to associate with this resource.')
    resource = models.CharField(max_length=500,
                            help_text=
                            "The URI of the resource followed by the user.")

    def __unicode__(self):
        return self.resource


class UserProfile(models.Model):
    """
    Additional information about a user.

    """
    user = models.OneToOneField(User)
    show_email = models.BooleanField('show email',
                                     help_text='Include your email address ' \
                                     'in any new annotations you create.')


class Organization(models.Model):
    """
    Information about an organization.

    """
    name = models.CharField(max_length=100, blank=False, unique=True,
                            help_text='The name of the organization.')
    primary_email = models.EmailField(blank=False, help_text=
                                      'The email of a person/list who is ' \
                                      'responsible for the CHAMRe client at ' \
                                      'this organization.')

    def __unicode__(self):
        return self.name


class OrganizationClient(models.Model):
    """
    The association of a client to an organization.

    """
    organization = models.ForeignKey(Organization,
                            help_text='The name of the organization.')
    client = models.ForeignKey(Client, unique=True, help_text=
                               'The client to associate with this ' \
                               'organization.')

    def __unicode__(self):
        return self.organization.name


class OrganizationUser(models.Model):
    """
    The role within an organization for a user.

    """
    organization = models.ForeignKey(Organization,
                                     help_text='The name of the organization.')
    user = models.ForeignKey(User,
                             help_text=
                             'The user to associate with this organization.')
    role = models.CharField(max_length=10,
                            choices=[('user', 'user'), ('admin', 'admin')],
                            help_text=
                            "The user's role within this organization.")

    def __unicode__(self):
        return self.role

