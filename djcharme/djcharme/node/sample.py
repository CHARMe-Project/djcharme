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

Created on 18 Nov 2013

@author: mnagni
'''
import csv
from datetime import datetime
import logging

from django.conf import settings
from django.utils.http import urlquote
from rdflib import Literal
from rdflib.plugins.parsers.notation3 import BadSyntax

from djcharme import get_resource
from djcharme.exception import ParseError
from djcharme.node.actions import insert_rdf
from djcharme.node.constants import SUBMITTED
from djcharme.node.model_queries import get_client, get_user


LOGGING = logging.getLogger(__name__)

CITATION_TEMPLATE = '''
@prefix chnode: <http://localhost/> .
@prefix oa: <http://www.w3.org/ns/oa#> .
@prefix cito: <http://purl.org/spar/cito/> .
@prefix fabio: <http://purl.org/spar/fabio/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<chnode:annoID> a oa:Annotation, cito:CitationAct ;
    oa:hasTarget <load_target> ;
    oa:motivatedBy oa:linking ;
    oa:serializedAt "load_serialized_at"^^xsd:dateTime ;
    oa:serializedBy <chnode:agentID> ;
    cito:hasCitingEntity <load_body> ;
    cito:hasCitedEntity <load_target> ;
    cito:hasCitationCharacterization cito:citesAsDataSource .

<chnode:agentID> a prov:SoftwareAgent ;
    foaf:name "CHARMe system" .

<load_body> a fabio:load_classes .

<load_target> a fabio:MetadataDocument .
'''


def __load_datasets():
    """
    Load sample data sets.

    """
    datasets_file = open(get_resource('dataset_to_ceda_mappings.csv'))
    # datasets_file = open('resources/dataset_to_ceda_mappings.csv')
    dataset_reader = csv.reader(datasets_file, dialect='excel-tab')
    datasets = {}
    for row in dataset_reader:
        if type(row) != list \
            or len(row[0]) == 0 \
            or (len(row[1]) + len(row[2])) == 0 \
            or row[0] == 'Dataset':
            continue
        try:
            datasets[row[0]] = row[1:3]
        except Exception:
            pass
    return datasets


def __load_citations():
    """
    Load sample citations.

    """
    citations_file = open(get_resource
                          ('ceda_citations_to_metadata_url_mappings.csv'))
    citations_reader = csv.reader(citations_file, dialect='excel-tab')
    citations = {}
    dataset_name = None
    for row in citations_reader:
        if type(row) != list \
            or len(row[0]) == 0 \
            or (len(row[1]) + len(row[2])) == 0 \
            or row[0] == 'Dataset':
            continue
        try:
            if dataset_name == row[0]:
                citations[row[0]].append(row[1:])
            else:
                citations[row[0]] = [row[1:]]
            dataset_name = row[0]
        except Exception:
            pass
    return citations


def load_sample():
    """
    Load sample data.

    """
    LOGGING.debug('Loading samples')
    timestamp = Literal(datetime.utcnow())
    datasets = __load_datasets()
    citations = __load_citations()
    user_name = getattr(settings, 'SAMPLE_USER_NAME', 'stfc')
    user = get_user(user_name)
    client_name = getattr(settings, 'SAMPLE_CLIENT_NAME', 'STFC')
    client = get_client(client_name)
    serialized_at = timestamp
    if user == None or client == None:
        LOGGING.warn(('Samples not loaded as use %s not found and/or client for %s not found' % (user, client)))
        return
    for ds_key in datasets.keys():
        data_set = datasets.get(ds_key)
        cts = citations.get(ds_key, None)
        if cts == None:  # remove
            continue  # remove
        for cit in cts:
            annotation = CITATION_TEMPLATE.replace("load_target",
                                                   urlquote(data_set[1].strip()))
            # in press causes a
            # Exception: "file:///home/wilsona/workspace-space/in press" does not look like a valid URI, I cannot serialize this as N3/Turtle. Perhaps you wanted to urlencode it?
            if cit[8] and cit[8] != 'in press':
                annotation = annotation.replace("load_body", urlquote(cit[8].strip()))
            else:
                continue
            annotation = annotation.replace("load_serialized_at", serialized_at)
            if cit[0] == 'article':
                annotation = annotation.replace("load_classes", "Article")
            elif cit[0] == 'inbook':
                annotation = annotation.replace("load_classes", "BookChapter")
            elif cit[0] == 'proceedings':
                annotation = annotation.replace("load_classes",
                                                "AcademicProceedings")
            elif cit[0] == 'techreport':
                annotation = annotation.replace("load_classes",
                                                "TechnicalReport")
            elif cit[0] == 'misc':
                continue
            else:
                LOGGING.debug('Samples - found type %, ignoring record' % cit[0])
                continue

            try:
                insert_rdf(annotation, 'turtle', user, client,
                                   graph=SUBMITTED)
            except BadSyntax as ex:
                LOGGING.warn(ex)
                continue
            except ParseError as ex:
                LOGGING.warn(ex)
                continue
            except Exception as ex:
                LOGGING.error(ex)

