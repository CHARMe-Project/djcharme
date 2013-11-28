'''
BSD Licence
Copyright (c) 2012, Science & Technology Facilities Council (STFC)
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, 
are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, 
        this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
        this list of conditions and the following disclaimer in the documentation
        and/or other materials provided with the distribution.
    * Neither the name of the Science & Technology Facilities Council (STFC) 
        nor the names of its contributors may be used to endorse or promote 
        products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, 
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR 
PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, 
OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Created on 25 May 2013

@author: Maurizio Nagni
'''
from ceda_markup.opensearch.osquery import OSQuery
from ceda_markup.gml.gml import createBeginPosition, createEndPosition, \
    createTimePeriod, createValidTime
from ceda_markup.opensearch import COUNT_DEFAULT, \
    START_INDEX_DEFAULT, START_PAGE_DEFAULT, filter_results
from ceda_markup.opensearch.template.osresponse import OSEngineResponse, Result

from ceda_markup.opensearch.os_request import OS_NAMESPACE
from ceda_markup.opensearch.os_param import OSParam
from djcharme.node.search import search_title, search_annotationByTarget,\
    search_annotationsByStatus, annotation_resource
from ceda_markup.opensearch.template.atom import OSAtomResponse
from djcharme.node.actions import CH_NODE, ANNO_STABLE
import datetime
from ceda_markup.atom.atom import createID, createUpdated, createPublished,\
    createEntry
from ceda_markup.atom.info import createContent, createTitle, TEXT_TYPE
from djcharme.views import checkMimeFormat
import logging







GUID = 'guid'
FILE_ID = 'guid'
COLLECTION = 'collection'
OBSERVATION = 'observation'
RESULT = 'result'
BBOX = 'bbox'
DUMMY_GUID = 'dummy_guid'

FATCAT_HOST = 'citest1.jc.rl.ac.uk'
FATCAT_ROOT_PATH = 'fatcatOS'
PROXY_URL = 'http://wwwcache.rl.ac.uk:8080'

CEDA_TITLE = 'ceda_title'

LOGGING = logging.getLogger(__name__)
   
def append_valid_time(subresult, entry, atomroot, 
                       begin_position, end_position):
    #xmlentry = entry.buildElement()
    if begin_position is not None:
        begin_position = createBeginPosition(root = atomroot, 
                                            body = subresult.beginPosition)
    if end_position is not None:                
        end_position = createEndPosition(root = atomroot, 
                                        body = subresult.endPosition)                
    time_period = createTimePeriod(root = atomroot, 
                                  begin = begin_position, end = end_position)       
    valid_time = createValidTime(root = atomroot, body = time_period)
    if begin_position is not None or end_position is not None:
        entry.append(valid_time) 

def extract_title(ceda_obj):
    if hasattr(ceda_obj, 'identifier'):
        for ident in ceda_obj.identifier:
            if ident.authority.title == CEDA_TITLE:
                return ident.code  

def generate_url_id(url, iid = None):
    if iid is None:
        return "%s/search" % (url)
    
    return "%s/search/%s" % (url, iid)


def import_count_and_page(context):
    ret = []        
    
    try: 
        ret.append(int(context.get('count', COUNT_DEFAULT)))
    except (ValueError, TypeError):
        ret.append(COUNT_DEFAULT)      
    
    try: 
        ret.append(int(context.get('startIndex', START_INDEX_DEFAULT)))
    except (ValueError, TypeError):
        ret.append(START_INDEX_DEFAULT)
    
    try: 
        ret.append(int(context.get('startPage', START_PAGE_DEFAULT)))
    except (ValueError, TypeError):
        ret.append(START_PAGE_DEFAULT)
    
    return tuple(ret)

class COSAtomResponse(OSAtomResponse):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        super(COSAtomResponse, self).__init__()

    def generate_entries(self, atomroot, subresults, path, \
                         params_model, context):
        if subresults is None:
            return
               
        entries = []
        for subresult in subresults: 
            #Here could loop over results
            atom_id = createID(subresult['subject'], root = atomroot)
            ititle = createTitle(root = atomroot, 
                                 body = subresult['subject'], 
                                 itype = TEXT_TYPE)
            atom_content = createContent(root = atomroot, 
                                        body = subresult['triple'], 
                                        itype = TEXT_TYPE)
            atom_updated = createUpdated(datetime.datetime.now().isoformat(), 
                                         root = atomroot)
            atom_published = createPublished('TO_BE_DONE_2011-01-21T11:05:29.511Z', 
                                            root = atomroot)            
            entry = createEntry(atom_id, ititle, atom_updated,
                                published=atom_published,
                                content=atom_content, root = atomroot)        

            entries.append(entry)

        for entry in entries:
            atomroot.append(entry) 
            
    def generate_url(self, osHostURL, context):
        '''
            Returns the proper URL to assemble the OSResponse links
        '''
        return generate_url_id(osHostURL, context.get('target', None))        

    def digest_search_results(self, results, context):
        title = "CHARMe results"
        count, start_index, start_page = import_count_and_page(context)
        
        #set_subresults = set(results.subjects())
        #subjects = [subj for subj in set_subresults]
        annotation_subresults = filter_results(results, 
                                            count, start_index, start_page)
        
        subresults = []
        iformat = context.get('format', 'json-ld')
        if iformat == None:
            iformat = 'json-ld'
        iformat = checkMimeFormat(iformat)
        for annotation_graph in annotation_subresults: 
            try:                       
                subject = [subj for subj 
                        in annotation_graph.triples(annotation_resource())][0][0]        
                subresults.append({'subject': str(subject), 
                        'triple': annotation_graph.serialize(format = iformat)})
            except (IndexError):
                LOGGING.warn("No Annotation resource for graph %s" 
                             % annotation_graph.serialize())
                continue
        return Result(count, start_index, start_page, len(annotation_subresults), \
                      subresult = subresults, title = title) 

'''            
    def generate_response(self, results, query, \
                          ospath, params_model, context):
        return results
'''

class COSRDFResponse(OSEngineResponse):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        super(COSRDFResponse, self).__init__('rdf')

    def digest_search_results(self, results, context):
        title = "CHARMe results"
        count, start_index, start_page = import_count_and_page(context)
        subresults = filter_results(results, count, start_index, start_page)
        return Result(count, start_index, start_page, len(results), \
                      subresult = subresults, title = title)        
        #return results.serialize(format='xml')
            
    def generate_response(self, results, query, \
                          ospath, params_model, context):
        return results

class COSJsonLDResponse(OSEngineResponse):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        super(COSJsonLDResponse, self).__init__('json-ld')

    def digest_search_results(self, results, context):
        return results.serialize(format='json-ld')
            
    def generate_response(self, results, query, \
                          ospath, params_model, context):
        return results

class COSTurtleResponse(OSEngineResponse):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        super(COSTurtleResponse, self).__init__('ttl')

    def digest_search_results(self, results, context):
        return results.serialize(format='turtle')
            
    def generate_response(self, results, query, \
                          ospath, params_model, context):
        return results

class COSHTMLResponse(OSAtomResponse):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        super(COSHTMLResponse, self).__init__()
        
    def generateResponse(self, result, queries, ospath, **kwargs):
        return result + " HTML!"
        
class COSQuery(OSQuery):
    '''
    classdocs
    '''

    def __init__(self):
        '''
            Constructor
        '''
        params = []
        params.append(OSParam("count", "count", 
                              namespace = OS_NAMESPACE, default = '1'))
        params.append(OSParam("startPage", "startPage", 
                              namespace = OS_NAMESPACE, default = '1'))
        params.append(OSParam("startIndex", "startIndex", 
                              namespace = OS_NAMESPACE, default = '1'))                
        params.append(OSParam("q", "searchTerms", 
                              namespace = OS_NAMESPACE, default = ''))                 
        params.append(OSParam("title", "title", 
                namespace = "http://purl.org/dc/terms/", default = ''))
        params.append(OSParam("target", "target", 
                namespace = CH_NODE, default = ''))
        params.append(OSParam("status", "status", 
                namespace = CH_NODE, default=ANNO_STABLE))            
        params.append(OSParam("depth", "depth", 
                namespace = CH_NODE, default='1'))
        params.append(OSParam("format", "format", 
                              namespace = CH_NODE, default = 'json-ld'))        
        '''        
        params.append(OSParam(BBOX, 'box', 
                namespace = "http://a9.com/-/opensearch/extensions/geo/1.0/"))       
        params.append(OSParam("start", "start", 
                namespace = "http://a9.com/-/opensearch/extensions/time/1.0/"))        
        params.append(OSParam("stop", "end", 
                namespace = "http://a9.com/-/opensearch/extensions/time/1.0/"))
        '''        
        self._query_signature = self._querySignature(params)
        super(COSQuery, self).__init__(params)
        
    def do_search(self, query, context):        
        results = []
        if query.attrib.get('title', None) != None \
                and len(query.attrib.get('title')) > 0:
            results.append(search_title(title=query.attrib['title'], 
                            graph=str(query.attrib['status']),
                            depth=int(query.attrib['depth']),
                            limit=int(query.attrib['count'])))
            
        elif query.attrib.get('target', None) \
                and len(query.attrib.get('target')) > 0:
            results.append(search_annotationByTarget(query.attrib['target'], 
                            graph=str(query.attrib['status']),
                            depth=int(query.attrib['depth']),
                            limit=int(query.attrib['count'])))
            
        elif query.attrib.get('status', None) \
                and len(query.attrib.get('status')) > 0:
            results.append(search_annotationsByStatus( 
                            graph=str(query.attrib['status']),
                            depth=int(query.attrib['depth']),
                            limit=int(query.attrib['count'])))
         
        return results[0]


    def _querySignature(self, params_model):
        _params = []        
        for params in params_model:
            if params.par_name not in ['count', 'startPage', 'startIndex']:
                _params.append(params.par_name)                
        return _params

class SearchProxy(object):
    def __init__(self, query):
        _query = query        
        self.query_signature = None
        super(SearchProxy, self).__init__(self)
        
                