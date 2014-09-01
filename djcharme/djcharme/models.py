"""
Custom models.

"""
from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    """
    Additional information about a user.

    """
    user = models.OneToOneField(User)
    show_email = models.BooleanField()
