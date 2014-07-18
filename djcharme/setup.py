# -*- coding: utf-8 -*-
from distutils.core import setup
from setuptools import find_packages
import re
import os

BASE_NAME = 'djcharme'

V_FILE = open(os.path.join(os.path.dirname(__file__),
                       BASE_NAME, '__init__.py'))

README = open(os.path.join(os.path.dirname(__file__), 'README')).read()

VERSION = re.compile(r".*__version__ = '(.*?)'",
                     re.S).match(V_FILE.read()).group(1)

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name=BASE_NAME,
    version=VERSION,
    author=u'Maurizio Nagni',
    author_email='maurizio.nagni@stfc.ac.uk',
    include_package_data=True,
    packages=find_packages(),  # include all packages under this directory
    url='https://github.com/cedadev/djcharme',
    license='BSD licence, see LICENCE',
    description='CHARMe Node',
    long_description=open('README').read(),
    zip_safe=False,

    # Adds dependencies
    install_requires=['django',
                      'cedatheme_mf54',
                      'rdflib==4.1-dev',
                      'rdflib-jsonld==0.1',
                      'ceda-markup',
                      'py-bcrypt',
                      'django-oauth2-provider==0.2.7-dev'],
)

