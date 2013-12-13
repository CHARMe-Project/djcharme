# -*- coding: utf-8 -*-
from distutils.core import setup
from setuptools import find_packages
import re
import os

base_name='djcharme'

v_file = open(os.path.join(os.path.dirname(__file__), 
                       base_name, '__init__.py'))
                       
README = open(os.path.join(os.path.dirname(__file__), 'README')).read()
                       
VERSION = re.compile(r".*__version__ = '(.*?)'",
                     re.S).match(v_file.read()).group(1)

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name=base_name,
    version=VERSION,
    author=u'Maurizio Nagni',
    author_email='maurizio.nagni@stfc.ac.uk',
    include_package_data = True,    
    packages=find_packages(), # include all packages under this directory    
    #url='http://team.ceda.ac.uk/svn/ceda/ceda_software/cedasite/ceda_services/dj_dataset_registration',  
    license='BSD licence, see LICENCE',
    description='to update',
    long_description=open('README').read(),
    zip_safe=False,

    # Adds dependencies    
    install_requires = ['django',
                        'cedatheme_mf54',
                        'rdflib==4.1-dev',
                        'rdflib-jsonld',
                        'ceda-markup',
                        'py-bcrypt'],
)

