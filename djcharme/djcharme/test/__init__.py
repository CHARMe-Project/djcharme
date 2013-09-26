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

rdf_usecase1 = '''
<rdf:RDF
   xmlns:ns1="http://purl.org/spar/cito/"
   xmlns:ns2="http://www.w3.org/ns/oa#"
   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
   xmlns:dcterm="http://purl.org/dc/terms/"
>
  <rdf:Description rdf:about="http://data.gov.uk//dataset/index-of-multiple-deprivation">
    <rdf:type rdf:resource="http://purl.org/dc/dcmitype/Dataset"/>
  </rdf:Description>
  <rdf:Description rdf:about="http://localhost/annoID">
    <ns2:motivatedBy rdf:resource="http://www.w3.org/ns/oa#linking"/>
    <ns2:hasBody rdf:resource="http://localhost/bodyID"/>
    <rdf:type rdf:resource="http://www.w3.org/ns/oa#Annotation"/>
    <ns2:hasTarget rdf:resource="http://data.gov.uk//dataset/index-of-multiple-deprivation"/>
  </rdf:Description>
  <rdf:Description rdf:about="http://localhost/bodyID">
    <ns1:hasCitationEvent rdf:resource="http://purl.org/spar/cito/citesAsDataSource"/>
    <ns1:hasCitingEntity rdf:resource="http://dx.doi.org/10.1371/journal.pone.0043294"/>
    <ns1:hasCitedEntity rdf:resource="http://data.gov.uk//dataset/index-of-multiple-deprivation"/>
    <rdf:type rdf:resource="http://purl.org/spar/cito/CitationAct"/>
  </rdf:Description>
  <rdf:Description rdf:about="http://dx.doi.org/10.1371/journal.pone.0043294">
      <dcterm:title xml:lang="en-us">Lost Letter Measure of Variation in Altruistic Behaviour in 20 Neighbourhoods</dcterm:title>
      <dcterm:creator>John R. Anderson</dcterm:creator>
  </rdf:Description>
</rdf:RDF>
'''

turtle_usecase1 = '''
    @prefix chnode: <http://localhost/> . 
    @prefix oa: <http://www.w3.org/ns/oa#> . 
    @prefix dctype: <http://purl.org/dc/dcmitype/> .
    @prefix dcterm: <http://purl.org/dc/terms/> .
    @prefix cito: <http://purl.org/spar/cito/> . 
    
    <chnode:annoID> a oa:Annotation ;
    oa:hasTarget <http://data.gov.uk//dataset/index-of-multiple-deprivation> ;
    oa:hasBody <chnode:bodyID> ;
    oa:motivatedBy oa:linking .

    <chnode:bodyID> a cito:CitationAct ;
       cito:hasCitingEntity <http://dx.doi.org/10.1371/journal.pone.0043294> ;
       cito:hasCitationEvent cito:citesAsDataSource ;
       cito:hasCitedEntity <http://data.gov.uk//dataset/index-of-multiple-deprivation> .
        
    <http://data.gov.uk//dataset/index-of-multiple-deprivation>
        a dctype:Dataset .
        
    <http://dx.doi.org/10.1371/journal.pone.0043294>
        dcterm:creator "John R. Anderson" ;  
        dcterm:title "Lost Letter Measure of Variation in Altruistic Behaviour in 20 Neighbourhoods"@en-us .                  
'''        

jsonld_usecase1 = ''' 
{
  "@graph": [
    {
      "@id": "http://data.gov.uk//dataset/index-of-multiple-deprivation",
      "@type": "http://purl.org/dc/dcmitype/Dataset"
    },
    {
      "@id": "http://localhost/annoID",
      "@type": "http://www.w3.org/ns/oa#Annotation",
      "http://www.w3.org/ns/oa#hasBody": {
        "@id": "http://localhost/bodyID"
      },
      "http://www.w3.org/ns/oa#hasTarget": {
        "@id": "http://data.gov.uk//dataset/index-of-multiple-deprivation"
      },
      "http://www.w3.org/ns/oa#motivatedBy": {
        "@id": "http://www.w3.org/ns/oa#linking"
      }
    },
    {
      "@id": "http://localhost/bodyID",
      "@type": "http://purl.org/spar/cito/CitationAct",
      "http://purl.org/spar/cito/hasCitationEvent": {
        "@id": "http://purl.org/spar/cito/citesAsDataSource"
      },
      "http://purl.org/spar/cito/hasCitedEntity": {
        "@id": "http://data.gov.uk//dataset/index-of-multiple-deprivation"
      },
      "http://purl.org/spar/cito/hasCitingEntity": {
        "@id": "http://dx.doi.org/10.1371/journal.pone.0043294"
      }
    },
    {
      "@id": "http://dx.doi.org/10.1371/journal.pone.0043294",
      "http://purl.org/dc/terms/creator": "John R. Anderson",
      "http://purl.org/dc/terms/title": {
        "@language": "en-us",
        "@value": "Lost Letter Measure of Variation in Altruistic Behaviour in 20 Neighbourhoods"
      }
    }
  ]
}
'''

turtle_usecase2_data_describing = ''' 
    @prefix chnode: <http://localhost/> . 
    @prefix oa: <http://www.w3.org/ns/oa#> . 
    @prefix dctypes: <http://purl.org/dc/dcmitype/> .
    @prefix dctterms: <http://purl.org/dc/dcterms/> .    
    @prefix cito: <http://purl.org/spar/cito/> . 
    
    <chnode:annoID> a oa:Annotation ;
    oa:hasTarget <http://badc.nerc.ac.uk/view/badc.nerc.ac.uk__ATOM__dataent_EAAM> ;
    oa:hasBody <chnode:bodyID> ;
    oa:motivatedBy oa:describing .

    <chnode:bodyID>
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