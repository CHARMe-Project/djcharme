# -*- coding: utf-8 -*-
from distutils.core import setup
from setuptools import find_packages
import re
import os

BASE_NAME = 'djcharme'

V_FILE = open(os.path.join(os.path.dirname(__file__),
                           BASE_NAME, '__init__.py'))

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

VERSION = re.compile(r".*__version__ = '(.*?)'",
                     re.S).match(V_FILE.read()).group(1)

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name=BASE_NAME,
    version=VERSION,
    author=u'Antony Wilson',
    author_email='antony.wilson@stfc.ac.uk',
    include_package_data=True,
    packages=find_packages(),  # include all packages under this directory
    url='https://github.com/CHARMe-Project/djcharme',
    license='BSD licence, see LICENCE',
    description='CHARMe Node',
    long_description=README,
    zip_safe=False,

    classifiers=[
        'Framework :: Django :: 1.7',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
    ],

    # Adds dependencies
    # django-registration==0.8 is explicitly included as 1.0 breaks
    # django-authopenid
    install_requires=[
        'ceda-markup==0.1.0',
        'cedatheme_mf54==1.0.0',
        'Django==1.7',
        'django-authopenid==1.0.2',
        'django-classy-tags==0.6.2',
        'django-cookie-law==1.0.6',
        'django-oauth2-provider==0.2.7.dev0',
        'django-registration==0.8',
        'html5lib==0.9999999',
        'isodate==0.5.4',
        'ordereddict==1.1',
        'py-bcrypt==0.4',
        'pyparsing==2.0.3',
        'rdflib==4.1.2',
        'rdflib-jsonld==0.2',
        'shortuuid==0.4.2',
        'SPARQLWrapper==1.6.4',
    ],
)

