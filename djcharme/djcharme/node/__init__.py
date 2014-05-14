from rdflib.graph import Graph


def _collect_all(graph, cache_graph, uri_ref, depth=None):
    for res in graph.triples((uri_ref, None, None)):
        cache_graph.add(res)
        if depth is None or depth > 0:
            if depth > 0:  # if fixed depth decrease the depth by one
                depth = depth - 1
            _collect_all(graph, cache_graph, res[2], depth)

def _extract_subject(graph, subject, depth):
    '''
        Extracts from graph and describes, if exists, the specified subject
        - Graph **graph**
            the graph to search in
        - URIRef **uriRef**
            the subject to describe
        - integer **depth**
            how deep should the subject's properties be described

        **return** an rdflib.Graph containing the subject details
    '''
    tmp_g = Graph()
    for res in graph.triples((subject, None, None)):
        tmp_g.add(res)
        if depth is None or depth > 0:
            _collect_all(graph, tmp_g, res[2], depth)
    return tmp_g
