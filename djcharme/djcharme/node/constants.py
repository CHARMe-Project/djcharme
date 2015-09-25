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
'''
from rdflib import URIRef
from rdflib.namespace import Namespace


CONTENT_HTML = 'text/html'
CONTENT_JSON = 'application/ld+json'
CONTENT_RDF = 'application/rdf+xml'
CONTENT_TURTLE = 'text/turtle'
CONTENT_TEXT = 'text/plain'

# order is important
FORMAT_MAP = {'json-ld': CONTENT_JSON,
              'xml': CONTENT_RDF,
              'rdf': CONTENT_RDF,
              'turtle': CONTENT_TURTLE,
              'ttl': CONTENT_TURTLE}

CH_NS = "http://purl.org/voc/charme#"
# Create a namespace object for the CHARMe namespace.
CITO = Namespace("http://purl.org/spar/cito/")
CONTENT = Namespace("http://www.w3.org/2011/content#")
DC = Namespace("http://purl.org/dc/elements/1.1/")
DCTERMS = Namespace("http://purl.org/dc/terms/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
OA = Namespace("http://www.w3.org/ns/oa#")
PROV = Namespace("http://www.w3.org/ns/prov#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
CH = Namespace(CH_NS)

SUBMITTED = 'submitted'
INVALID = 'invalid'
STABLE = 'stable'
RETIRED = 'retired'
GRAPH_NAMES = [SUBMITTED, STABLE, RETIRED, INVALID]

LOCALHOST_URI = 'http://localhost/'
TARGET_URI = 'targetID'
ANNO_URI = 'annoID'
REPLACEMENT_URIS = ['agentID', ANNO_URI, 'bodyID', TARGET_URI,
                    'subsetSelectorID']
REPLACEMENT_URIS_MULTIVALUED = ['variableID', 'spatialExtentID',
                                'temporalExtentID', 'verticalExtentID']

CH_NODE = 'chnode'

RESOURCE = 'resource'
DATA = 'data'
FOLLOWING = 'following'
PAGE = 'page'

ALLOWED_CREATE_TARGET_TYPE = [URIRef(OA + 'Composite'),
                              URIRef(CH_NS + 'DatasetSubset'),
                              URIRef(OA + 'SpecificResource')]










