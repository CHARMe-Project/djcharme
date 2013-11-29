'''
Created on 18 Nov 2013

@author: mnagni
'''
import csv
from djcharme.node.actions import insert_rdf, ANNO_SUBMITTED
from rdflib.term import URIRef
from djcharme.node.doi import load_doi
from djcharme import get_resource
import logging
from rdflib.plugins.parsers.notation3 import BadSyntax

LOGGING = logging.getLogger(__name__)

citation_template = '''

@prefix oa: <http://www.w3.org/ns/oa#> . 
@prefix fabio: <http://purl.org/spar/fabio/> .
@prefix cito: <http://purl.org/spar/cito/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix chnode: <http://localhost/> .

<chnode:annoID> a oa:Annotation ; 
oa:hasBody <chnode:bodyID> ; 
oa:hasTarget <load_target> ; 
oa:motivatedBy oa:linking ;
#oa:annotatedAt load_annotated_at;
#oa:serializedAt load_serialized_at; 
oa:annotatedBy <chnode:kp_xs02300> .

<chnode:kp_xs02300> a foaf:Person ;
    foaf:name "Maurizio Nagni"  ;
    foaf:mbox <mailto:maurizio.nagni@example.org> .

<chnode:bodyID> a cito:CitationAct ; 
cito:hasCitingEntity <load_body> ; 
cito:hasCitationEvent cito:citesAsDataSource ; 
cito:hasCitedEntity <load_target> . 

<load_body> a fabio:load_classes . 
<load_target> a fabio:MetadataDocument .
'''


def __loadDatasets():
    
    datasets_file = open(get_resource('dataset_to_ceda_mappings.csv'))
    #datasets_file = open('resources/dataset_to_ceda_mappings.csv')
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
        except:
            pass
    return datasets

def __loadCitations():
    citations_file = open(get_resource('ceda_citations_to_metadata_url_mappings.csv'))
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
        except:
            pass
    return citations

def load_sample():
    datasets = __loadDatasets()
    citations = __loadCitations()
    for ds_key in datasets.keys():
        ds = datasets.get(ds_key)
        cts = citations.get(ds_key, None)
        for ct in cts:
            annotation = citation_template.replace("load_target", ds[1].strip())                
            if ct[8]: 
                annotation = annotation.replace("load_body", ct[8].strip())
            else:
                continue
            if ct[0] == 'article':
                annotation = annotation.replace("load_classes", "Article")
            elif ct[0] == 'inbook':
                annotation = annotation.replace("load_classes", "BookChapter")  
            elif ct[0] == 'proceedings':
                annotation = annotation.replace("load_classes", "AcademicProceedings")                    
            elif ct[0] == 'techreport':
                annotation = annotation.replace("load_classes", "TechnicalReport")                    
            elif ct[0] == 'misc':
                continue                  
            else:
                print "other"
                continue
            
            try:
                tmp_g = insert_rdf(annotation, 'turtle', graph=ANNO_SUBMITTED)
            except BadSyntax as e:
                LOGGING.warn(e)
                continue
            
            #print tmp_g.serialize(format='turtle')
            for item in tmp_g.triples((None, None, URIRef('http://purl.org/spar/fabio/Article'))):
                if 'doi' in str(item[0]):
                    load_doi(item[0], tmp_g)                            