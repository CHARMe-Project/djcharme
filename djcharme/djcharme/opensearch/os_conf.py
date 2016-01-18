'''
BSD Licence
Copyright (c) 2014, Science & Technology Facilities Council (STFC)
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

Created on 4 May 2012

@author: Maurizio Nagni
'''
from ceda_markup.markup import createMarkup
from ceda_markup.opensearch.os_engine import OSEngine
from ceda_markup.opensearch.os_engine_helper import OSEngineHelper
from ceda_markup.opensearch.os_request import OS_PREFIX, OS_NAMESPACE
from ceda_markup.opensearch.os_request import OpenSearchDescription

from djcharme.opensearch.cimpl import COSQuery, COSAtomResponse


def setUp():
    query = COSQuery()
    # responses = [COSRDFResponse(), COSTurtleResponse(), COSJsonLDResponse(),
    # COSAtomResponse()]
    responses = [COSAtomResponse()]
    os_short_name = "CHARMe Search"
    os_description = "Use CHARMe Search to search for annotations"
    os_tags = "bodyType citingType dataType domainOfInterest motivation " \
        "organization region"
    os_adult_content = "false"
    os = OpenSearchDescription(os_short_name, os_description, os_tags=os_tags,
                               os_adult_content=os_adult_content)
    return OSEngine(query, responses, os, os_engine_helper=helper())


class helper(OSEngineHelper):
    """
    An implementation of the OSEngineHelper class used to provide additional
    information for the description document.

    """

    def __init__(self):
        """
        Constructor
        """
        super(OSEngineHelper)

    def additional_description(self, req_doc):
        """
        Overriding the OSEngineHelper method to add further tags into reqDoc.

        Args:
            req_doc: a request OpenSource document

        """
        markup = createMarkup('Query', OS_PREFIX, OS_NAMESPACE, req_doc)
        markup.set("role", "example")
        markup.set("status", "submitted")
        req_doc.append(markup)
        return req_doc

