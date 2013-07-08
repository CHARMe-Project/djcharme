define(["dojox/xml/parser", "dojox/grid/DataGrid", "dojo/store/Memory",
		"dojo/data/ObjectStore"],
		function(parser, DataGrid, Memory, ObjectStore){
			return {
				describeAnnotation: function(xml, div_id){
					var store = new Memory({ idProperty: "annotation" });

					var xmldom = parser.parse(xml);
					var nsResolver = document.createNSResolver( xmldom.ownerDocument == null ? 
							xmldom.documentElement : 
								xmldom.ownerDocument.documentElement );
					var queryResult = xmldom.evaluate('//rdf:Description', xmldom, nsResolver, 
							5, null)
					
					var value = queryResult.iterateNext();
					var storedAnnotation = ''
		            while(value){
		            	store.put({annotation:value.getAttribute('rdf:about')})
		            	storedAnnotation = store.get(value.getAttribute('rdf:about'))
		            	var nodes = value.childNodes;
		            	var child = ""
		            	for(i=0; i<nodes.length; i++) {
		            		child = nodes[i];
		            		if (child.localName == "hasBody") {
		            			storedAnnotation.hasBody 
				            		= child.getAttribute('rdf:resource')		            			
		            		}
		            		if (child.localName == "hasTarget") {
		            			storedAnnotation.hasTarget 
				            		= child.getAttribute('rdf:resource')		            			
		            		}
		            		if (storedAnnotation.hasBody && storedAnnotation.hasTarget) {
		            			break
		            		}
		            	}
		                value = queryResult.iterateNext();
		            }
					 
					
					dataStore = new ObjectStore({ objectStore: store });

					grid = new DataGrid({
						store: dataStore,
						query: { annotation: "*" },
						structure: [
						            {name: "Annotation", field: "annotation", width: "auto"},
						            {name: "hasTarget", field: "hasTarget", width: "auto"},
						            {name: "hasBody", field: "hasBody", width: "auto"}
						            ]
					 },div_id); 
					grid.startup();	            
				}
			}
});