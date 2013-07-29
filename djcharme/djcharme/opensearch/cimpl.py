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

Created on 5 May 2012

@author: Maurizio Nagni
'''
from ceda_markup.opensearch.osquery import OSQuery
from ceda_markup.atom.atom import createID, createUpdated, \
    createPublished, createEntry
from ceda_markup.atom.info import createTitle, HTML_TYPE, createContent
from ceda_markup.dc.dc import createDate
from ceda_markup.gml.gml import createBeginPosition, createEndPosition, \
    createTimePeriod, createValidTime
from ceda_markup.atom.link import REL_SEARCH, REL_ALTERNATE, createLink
from ceda_markup.opensearch import filter_results, COUNT_DEFAULT, \
    START_INDEX_DEFAULT, START_PAGE_DEFAULT, create_autodiscovery_link
from ceda_markup.opensearch.template.osresponse import Result, Subresult
from ceda_markup.opensearch.template.atom import OSAtomResponse
from ceda_markup.opensearch.template.html import OSHTMLResponse
from ceda_markup.georss import create_where_from_postgis
from ceda_markup.opensearch.os_request import OS_NAMESPACE
from ceda_markup.opensearch.os_param import OSParam







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



def apply_query_params(context, results):
    # A cleaner implementation would require calls to
    # db's merge_period_instant_views() but actually it does not collect 
    # infos about CEDA_Results
    
    subresults = []
    if results is None:
        return subresults
    for result in results:          
        pass
        '''
        item = Subresult(result_guid.id, ititle, datetime.now().isoformat(), 
                         **kwargs)               
        subresults.append(item)
        '''
    return subresults

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
        super(COSAtomResponse, self).__init__()       

    def digest_search_results(self, results, context):
        pass                                                           
        #return Result(count, start_index, start_page, tot_results, \
        #              subresult = subresults, title = title)
        
    def generateEntryLinks(self, entry, atomroot, path, params_model, context):
        entry.append(create_autodiscovery_link(atomroot, path, \
                                               params_model, context, \
                                               self.extension, \
                                               rel = REL_ALTERNATE))                
        
        entry.append(create_autodiscovery_link(atomroot, path, \
                                           params_model, context, \
                                           extension = self.extension, \
                                           rel = REL_SEARCH))                

    def generate_url(self, os_host_urlURL, context):
        return generate_url_id(os_host_urlURL, context.get('guid'))  

    def generate_entries(self, atomroot, subresults, path, params_model, context):
        if subresults is None:
            return
              
        entries = []
        
        for subresult in subresults: 
            #Here could loop over results
            entry_path = generate_url_id(path, subresult.id)
            atom_id = createID(entry_path + '/' + self.extension, root = atomroot)
            ititle = createTitle(root = atomroot, 
                                 body = subresult.title, 
                                 itype = HTML_TYPE)
            atom_content = createContent(root = atomroot, 
                                        body = subresult.description, 
                                        itype = HTML_TYPE)
            atom_updated = createUpdated(subresult.updated, root = atomroot)
            atom_published = createPublished('TO_BE_DONE_2011-01-21T11:05:29.511Z', 
                                            root = atomroot)            
            entry = createEntry(atom_id, ititle, atom_updated,
                                published=atom_published,
                                content=atom_content, root = atomroot)
            
            begin_position = None
            end_position = None
            if hasattr(subresult, 'beginPosition') \
                    and subresult.beginPosition is not None:
                begin_position = subresult.beginPosition
            if hasattr(subresult, 'endPosition') \
                    and subresult.endPosition is not None:                
                end_position = subresult.endPosition 
            append_valid_time(subresult, entry, atomroot, 
                              begin_position, end_position)            
            
            idate = createDate(root = atomroot, 
                body = 'TO_BE_DONE_2002-10-18T08:07:37.387Z/2012-03-29T07:12:20.735Z')        
            entry.append(idate)
            
            if hasattr(subresult, 'geometry') \
                    and subresult.geometry is not None:
                where = create_where_from_postgis(subresult.geometry, atomroot)
                entry.append(where)
            
            
            
            self.generateEntryLinks(entry, atomroot, entry_path, \
                                    params_model, context)
            if hasattr(subresult, 'enclosure') \
                    and subresult.enclosure is not None: 
                for enclosure in subresult.enclosure:
                    if enclosure.get('rel', None) == 'enclosure': 
                        entry.append(createLink(enclosure.get('href'), 
                                            rel = 'enclosure', 
                                            root = atomroot, 
                                            itype = enclosure.get('type'),
                                            length = enclosure.get('length')))                
                            
            entries.append(entry)

        for entry in entries:
            atomroot.append(entry) 

class COSHTMLResponse(OSHTMLResponse):
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
                              namespace = OS_NAMESPACE))
        params.append(OSParam("startPage", "startPage", 
                              namespace = OS_NAMESPACE))
        params.append(OSParam("startIndex", "startIndex", 
                              namespace = OS_NAMESPACE))                
        params.append(OSParam("q", "searchTerms", 
                              namespace = OS_NAMESPACE))
        '''         
        params.append(OSParam("uid", "uid", 
                namespace = "http://a9.com/-/opensearch/extensions/geo/1.0/"))        
        params.append(OSParam(BBOX, 'box', 
                namespace = "http://a9.com/-/opensearch/extensions/geo/1.0/"))       
        params.append(OSParam("start", "start", 
                namespace = "http://a9.com/-/opensearch/extensions/time/1.0/"))        
        params.append(OSParam("stop", "end", 
                namespace = "http://a9.com/-/opensearch/extensions/time/1.0/"))
        '''        
        super(COSQuery, self).__init__(params)
        
    def do_search(self, context):
        pass
