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
This module contains pre-formatted queries of the models.

'''
import logging

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from provider.oauth2.models import Client

from djcharme.models import FollowedResource, Organization, \
    OrganizationClient, OrganizationUser


LOGGING = logging.getLogger(__name__)

def get_admin_email_addresses(organization_name):
    """
    Get the list of admin email addresses associated with the organization.

    Args:
        organization_name (str): The name of the organization.

    Returns:
        [str] List of admin email addresses.

    """
    organizations = (Organization.objects.filter(name=organization_name))
    if len(organizations) < 1:
        LOGGING.warn("No data found for %s", organization_name)
        return []
    organization_ids = []
    for organization in organizations:
        organization_ids.append(organization.id)
    # there should only be one
    organization_id = organization_ids[0]
    organization_users = (OrganizationUser.objects.filter(role='admin').
                          filter(organization=organization_id))
    if len(organization_users) < 1:
        LOGGING.error("No admin found for organization %s", organization_name)
        return []
    admins = []
    for organization_user in organization_users:
        users = User.objects.filter(username=organization_user.user)
        for user in users:
            admins.append(user.email)
    return admins


def get_users_admin_role_orgs(user_id):
    """
    Get the list of organizations that this user is the admin for.

    Args:
        user_id (str): The id of the user.

    Returns:
        [str] List of organizations that this user is the admin for.

    """
    organization_users = (OrganizationUser.objects.filter(user=user_id).
                          filter(role='admin'))
    organizations = []
    for organization_user in organization_users:
        organizations.append(organization_user.organization.name)
    return organizations


def get_client(organization_name):
    """
    Get the client with the given organization name. Return None if not found.

    Args:
        organization_name (str): The name of the organization.

    Returns:
        client The client object or None if not found.

    """
    try:
        organization = Organization.objects.get(name=organization_name)
        organization_client = OrganizationClient.objects.get(organization=organization)
        client = Client.objects.get(organizationclient=organization_client)
    except ObjectDoesNotExist():
            return None
    return client


def get_user(user_name):
    """
    Get the user with the given user name. Return None if not found.

    Args:
        user_name (str): The user name of the user.

    Returns:
        User The User object or None if not found.

    """
    try:
        user = User.objects.get(username=user_name)
    except ObjectDoesNotExist():
        return None
    except Exception:
        return None
    return user


def get_organization_for_client(client):
    """
    Get the name of the organization associated with the client.

    Args:
        client (client): The Client object from a request

    Returns:
        str The name of the organization or None.

    """
    organization_id = (client.organizationclient_set.
                       values_list('organization', flat=True))
    if len(organization_id) < 1:
        LOGGING.warn("No organization found for client %s", client.url)
        return None
    # there should only be one
    organization_id = organization_id[0]
    organizations = (Organization.objects.filter(id=organization_id))
    for organization in organizations:
        return organization.name
    return None


def get_followers(resources):
    """
    Get the users that are following the resources.

    Args:
        resources(list[str]): The list of URIs of the resources.

    Returns:
        [User] List of users that are following the resource.

    """
    followers = []
    for resource in resources:
        followed_resources = (FollowedResource.objects.
                              filter(resource=resource))
        for followed_resource in followed_resources:
            followers.append(followed_resource)
    return followers


def is_following_resource(user, resource):
    """
    Check if the user is following the resource.

    Args:
        user(User): The name of the user
        resource(str): The URI of the resource.

    Returns:
        True if the user is already following the resource.

    """
    followed_resources = (FollowedResource.objects.
                          filter(user=user).
                          filter(resource=resource))
    if len(followed_resources) > 0:
        return True
    else:
        return False


def is_moderator(user):
    """
    Check to see if this user is in the moderator group. This is the super group
    with privileges to moderate ALL annotations.

    Args:
        user(User): The user object

    Returns:
        boolean True if the user is listed as a member of the moderator group.

    """
    groups = user.groups.values_list('name', flat=True)
    if "moderator" in groups:
        LOGGING.debug("User %s is a moderator", user.username)
        return True
    return False


def is_organization_admin(client, user, annotation_uri):
    """
    Check to see if this user is an admin for the organization at which the
    annotation was created.

    Args:
        client(Client): The client object
        user(User): The user object
        annotation_uri (URIRef): The URI of the annotation.

    Returns:
        boolean True if the user is listed as a admin for the organization.

    """
    user_id = user.id
    organization_id = (client.organizationclient_set.
                       values_list('organization', flat=True))
    if len(organization_id) < 1:
        LOGGING.warn("No organization found for client %s", client.url)
        return False
    # there should only be one
    organization_id = organization_id[0]
    organization_users = (OrganizationUser.objects.filter(user=user_id).
                          filter(organization=organization_id))
    for organization_user in organization_users:
        if organization_user.role == 'admin':
            LOGGING.debug("User %s is an admin for this annotation: %s",
                          user.username, annotation_uri)
            return True
    return False

