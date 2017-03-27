# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('djcharme', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='organizationuser',
            name='following',
        ),
        migrations.AlterField(
            model_name='followedresource',
            name='resource',
            field=models.URLField(help_text=b'The URI of the resource followed by the user.', max_length=500),
        ),
        migrations.AlterField(
            model_name='organization',
            name='primary_email',
            field=models.EmailField(help_text=b'The email of a person/list who is responsible for the CHAMRe client at this organization.', max_length=254),
        ),
        migrations.AlterField(
            model_name='organizationclient',
            name='client',
            field=models.OneToOneField(to='provider.Client', help_text=b'The client to associate with this organization.'),
        ),
    ]
