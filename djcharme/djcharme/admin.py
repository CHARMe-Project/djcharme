"""
Admin stuff.

"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from djcharme.models import FollowedResource, UserProfile, Organization, \
    OrganizationClient, OrganizationUser
from provider.oauth2.admin import ClientAdmin
from provider.oauth2.models import Client


class FollowedResourceAdmin(admin.ModelAdmin):
    """
    The Followed Resource Admin.

    """
    fields = ['user', 'resource']
    list_display = ('user', 'resource')
    list_filter = ['user']

class UserProfileInline(admin.StackedInline):
    """
    The in-line display of the User Profile.

    """
    model = UserProfile
    can_delete = False
    verbose_name = 'Profile'
    verbose_name_plural = 'Profiles'
    list_display = ('show_email')


class OrganizationUserInline(admin.StackedInline):
    """
    The in-line display of the Organization User.

    """
    model = OrganizationUser
    can_delete = False
    verbose_name = 'Role'
    verbose_name_plural = 'Roles'
    list_display = ('organization', 'role')
    extra = 1


class OrganizationClientInline(admin.StackedInline):
    """
    The in-line display of the Organization Client.

    """
    model = OrganizationClient
    verbose_name = 'Organization'
    verbose_name_plural = 'Organization'
    extra = 1
    fk_name = "client"


class OrganizationAdmin(admin.ModelAdmin):
    """
    The Organization Admin.

    """
    list_display = ('name', 'primary_email')


class OrganizationClientAdmin(admin.ModelAdmin):
    """
    The Organization Client Admin.

    """
    list_display = ('organization', 'client')
    list_filter = ['organization']


class OrganizationUserAdmin(admin.ModelAdmin):
    """
    The Organization User Admin.

    """
    fields = ['organization', 'user', 'role']
    list_display = ('organization', 'user', 'role')
    list_filter = ['organization', 'user']


class ClientAdmin_(ClientAdmin):
    """
    The new version of ClientAdmin, which includes the Organization Client.

    """
    inlines = [OrganizationClientInline]
    list_display = ('url', 'get_organization', 'redirect_uri', 'client_id',
                    'client_type')

    def get_organization(self, obj):
        """
        Get the name of the organization, there should only be one.

        """
        return obj.organizationclient_set.first()

    get_organization.short_description = 'organization'


class UserAdmin_(UserAdmin):
    """
    The new version of UserAdmin, which includes the User Profile and
    Organization User.

    """
    inlines = [UserProfileInline, OrganizationUserInline]
    list_display = ('username', 'get_role', 'email', 'first_name', 'last_name',
                    'is_staff')

    def get_role(self, obj):
        """
        Get the role of the user, they may have more than one role.

        """
        admin_ = False
        user = False
        for organizationuser in obj.organizationuser_set.iterator():
            if organizationuser.role == 'admin':
                admin_ = True
            else:
                user = True

        if admin_ and user:
            return 'admin & user'
        elif admin_:
            return 'admin'
        elif admin_:
            return 'user'
        else:
            return ''

    get_role.short_description = 'roles in organizations'


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin_)
admin.site.unregister(Client)
admin.site.register(Client, ClientAdmin_)
admin.site.register(FollowedResource, FollowedResourceAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(OrganizationUser, OrganizationUserAdmin)
admin.site.register(OrganizationClient, OrganizationClientAdmin)
