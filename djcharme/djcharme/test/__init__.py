from django.test.client import RequestFactory
from djcharme.views.node_gate import index, insert, process_page, advance_status
from xml.etree import ElementTree


rdf_data = '''
    <rdf:RDF
       xmlns:ns1="http://www.w3.org/2011/content#"
       xmlns:ns2="http://www.w3.org/ns/oa#"
       xmlns:ns3="http://purl.org/dc/elements/1.1/"
       xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
      <rdf:Description rdf:about="http://localhost/annoID">
        <rdf:type rdf:resource="http://www.w3.org/ns/oa#Annotation"/>
        <ns2:hasTarget rdf:resource="http://dx.doi.org/10.1029/00EO00172"/>
        <ns2:hasBody rdf:resource="http://localhost/bodyID"/>
      </rdf:Description>
      <rdf:Description rdf:about="http://dx.doi.org/10.1029/00EO00172">
        <ns3:format>html/text</ns3:format>
      </rdf:Description>
      <rdf:Description rdf:about="http://localhost/bodyID">
        <rdf:type rdf:resource="http://purl.org/dc/dcmitype/Text"/>
        <rdf:type rdf:resource="http://www.w3.org/2011/content#ContentAsText"/>
        <ns3:format>text/plain</ns3:format>
        <ns1:chars>hello there!</ns1:chars>
      </rdf:Description>
    </rdf:RDF>
'''

turtle_data = ''' 
    @prefix anno: <http://localhost/> . 
    @prefix oa: <http://www.w3.org/ns/oa#> . 
    @prefix dc: <http://purl.org/dc/elements/1.1/> . 
    @prefix cnt: <http://www.w3.org/2011/content#> . 
    @prefix dctypes: <http://purl.org/dc/dcmitype/> . 
    
    anno:annoID a oa:Annotation ;
    oa:hasTarget <http://dx.doi.org/10.1029/00EO00172> ;
    oa:hasBody anno:bodyID .

    anno:bodyID
    a cnt:ContentAsText, dctypes:Text ;
    cnt:chars "hello there!" ;
    dc:format "text/plain" .
    <http://dx.doi.org/10.1029/00EO00172>
    dc:format "html/text" .
'''

jsonld_data = '''
    {
        "@graph": [
            {
                "@id": "http://localhost/bodyID",
                "@type": [
                    "http://www.w3.org/2011/content#ContentAsText",
                    "http://purl.org/dc/dcmitype/Text"
                ],
                "http://purl.org/dc/elements/1.1/format": "text/plain",
                "http://www.w3.org/2011/content#chars": "hello there!"
            },
            {
                "@id": "http://localhost/annoID",
                "@type": "http://www.w3.org/ns/oa#Annotation",
                "http://www.w3.org/ns/oa#hasBody": {
                    "@id": "nodeURI/bodyID"
                },
                "http://www.w3.org/ns/oa#hasTarget": {
                    "@id": "http://dx.doi.org/10.1029/00EO00172"
                }
            },
            {
                "@id": "http://dx.doi.org/10.1029/00EO00172",
                "http://purl.org/dc/elements/1.1/format": "html/text"
            }
        ]
    }        
'''

turtle_usecase1 = ''' 
    @prefix chnode: <http://localhost/> . 
    @prefix oa: <http://www.w3.org/ns/oa#> . 
    @prefix dctypes: <http://purl.org/dc/dcmitype/> .
    @prefix cito: <http://purl.org/spar/cito/> . 
    
    <chnode:annoID> a oa:Annotation ;
    oa:hasTarget <http://data.gov.uk//dataset/index-of-multiple-deprivation> ;
    oa:hasBody <http://dx.doi.org/10.1371/journal.pone.0043294> ;
    oa:motivatedBy oa:linking .

    <http://dx.doi.org/10.1371/journal.pone.0043294>
        a cito:CitationAct, dctypes:Text .
        
    <http://data.gov.uk//dataset/index-of-multiple-deprivation>
        a dctypes:Dataset .
'''        

turtle_usecase2_data_describing = ''' 
    @prefix chnode: <http://localhost/> . 
    @prefix oa: <http://www.w3.org/ns/oa#> . 
    @prefix dctypes: <http://purl.org/dc/dcmitype/> .
    @prefix cito: <http://purl.org/spar/cito/> . 
    
    <chnode:annoID> a oa:Annotation ;
    oa:hasTarget <http://badc.nerc.ac.uk/view/badc.nerc.ac.uk__ATOM__dataent_EAAM> ;
    oa:hasBody <http://dx.doi.org/10.1175/1520-0469%281983%29040%3C1584%3ATLHSOD%3E2.0.CO%3B2> ;
    oa:motivatedBy oa:describing .

    <http://dx.doi.org/10.1175/1520-0469%281983%29040%3C1584%3ATLHSOD%3E2.0.CO%3B2>
        a cito:CitationAct, dctypes:Text ;
        cito:hasCitingEntity <http://dx.doi.org/10.1175/1520-0469%281983%29040%3C1584%3ATLHSOD%3E2.0.CO%3B2> ;
        cito:hasCitationCharacterization cito:describes ;
        cito:hasCitedEntity <http://badc.nerc.ac.uk/view/badc.nerc.ac.uk__ATOM__dataent_EAAM> .
        
    <http://badc.nerc.ac.uk/view/badc.nerc.ac.uk__ATOM__dataent_EAAM>
        a dctypes:Dataset .
'''

turtle_usecase2_data_citing = ''' 
    @prefix chnode: <http://localhost/> . 
    @prefix oa: <http://www.w3.org/ns/oa#> . 
    @prefix dctypes: <http://purl.org/dc/dcmitype/> .
    @prefix cito: <http://purl.org/spar/cito/> . 
    
    <chnode:annoID> a oa:Annotation ;
    oa:hasTarget <http://badc.nerc.ac.uk/view/badc.nerc.ac.uk__ATOM__dataent_EAAM> ;
    oa:hasBody <http://dx.doi.org/10.1029/00EO00172> ;
    oa:hasBody <http://dx.doi.org/10.1175/1520-0469%281983%29040%3C1584%3ATLHSOD%3E2.0.CO%3B2> ;    
    oa:motivatedBy oa:linking .

    <http://dx.doi.org/10.1029/00EO00172>
        a cito:CitationAct, dctypes:Text ;
        cito:hasCitingEntity <http://dx.doi.org/10.1029/00EO00172> ;
        cito:hasCitationCharacterization cito:citesAsRelated ;
        cito:hasCitedEntity <http://badc.nerc.ac.uk/view/badc.nerc.ac.uk__ATOM__dataent_EAAM> .

    <http://dx.doi.org/10.1175/1520-0469%281983%29040%3C1584%3ATLHSOD%3E2.0.CO%3B2>
        a cito:CitationAct, dctypes:Text ;
        cito:hasCitingEntity <http://dx.doi.org/10.1175/1520-0469%281983%29040%3C1584%3ATLHSOD%3E2.0.CO%3B2> ;
        cito:hasCitationCharacterization cito:describes ;
        cito:hasCitedEntity <http://badc.nerc.ac.uk/view/badc.nerc.ac.uk__ATOM__dataent_EAAM> .
                
    <http://badc.nerc.ac.uk/view/badc.nerc.ac.uk__ATOM__dataent_EAAM>
        a dctypes:Dataset .
'''
def _prepare_get(factory, url, user = None):
    """
        **RequestFactory** - factory
        **String** - url
        **User** - user
    """
    request = factory.get(url)    
    request.user = user
    return request

def extract_annotation_uri(document):
    xml = ElementTree.fromstring(document)
    RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
    descriptions = xml.findall('%sDescription' % (RDF))
    for desc in descriptions:
        anno = desc.find('./%stype[@%sresource="http://www.w3.org/ns/oa#Annotation"]' % (RDF, RDF))
        if anno is not None:
            return desc.get('%sabout' % RDF)

def test_advance_status(test_instance, 
                   url='/advance_status', 
                   data=None):
    return test_instance.factory.post(url,
                               content_type='application/json',
                               data=data)

def test_insert_anotation(test_instance,
                          http_accept='application/rdf+xml', 
                          content_type='text/turtle', 
                          data=turtle_usecase1):
    response = insert(test_instance.factory.post('/insert/annotation',
                                        content_type=content_type,
                                        data=data,
                                        HTTP_ACCEPT = http_accept))        
    
    test_instance.assert_(response.status_code == 200, "HTTPResponse has status_code: %s" % response.status_code)
    
    '''
    anno_uri = extract_annotation_uri(response.content)
    annoid = anno_uri[anno_uri.rfind('/') + 1 : ]    
    request = _prepare_get(test_instance.factory, '/resource/%s' % annoid)
    request.META['HTTP_ACCEPT'] = "text/html"
    response = process_page(request, resource_id = annoid)
    '''
    return response

def _dump_store(graph = 'submitted', req_format = 'turtle'):
    factory = RequestFactory()
    request = factory.get('/index/%s?format=%s' % (graph, req_format))
    index(request, graph)