# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('provider', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='FollowedResource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('resource', models.CharField(help_text=b'The URI of the resource followed by the user.', max_length=500)),
                ('user', models.ForeignKey(help_text=b'The user to associate with this resource.', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'The name of the organization.', unique=True, max_length=100)),
                ('primary_email', models.EmailField(help_text=b'The email of a person/list who is responsible for the CHAMRe client at this organization.', max_length=75)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrganizationClient',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('client', models.ForeignKey(to='provider.Client', help_text=b'The client to associate with this organization.', unique=True)),
                ('organization', models.ForeignKey(help_text=b'The name of the organization.', to='djcharme.Organization')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrganizationUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role', models.CharField(help_text=b"The user's role within this organization.", max_length=10, choices=[(b'user', b'user'), (b'admin', b'admin')])),
                ('following', models.BooleanField(default=False, help_text=b'Send emails about any annotation created or altered by the organization.', verbose_name=b'email changes')),
                ('organization', models.ForeignKey(help_text=b'The name of the organization.', to='djcharme.Organization')),
                ('user', models.ForeignKey(help_text=b'The user to associate with this organization.', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('show_email', models.BooleanField(default=False, help_text=b'Include your email address in any new annotations you create.', verbose_name=b'show email')),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
