define(["dojox/xml/parser", "dojox/grid/DataGrid", "dojo/store/Memory",
		"dojo/data/ObjectStore", "dojox/grid/cells", "dojo/_base/lang", 
		"dojo/_base/array", "dojo/json", "dojox/grid/_CheckBoxSelector"],
		function(parser, DataGrid, Memory, ObjectStore, gridCells, lang, baseArray, JSON){
			return {
				describeAnnotation: function(xml, states, div_id){
					var store = new Memory({ idProperty: "annotation" });

					var xmldom = parser.parse(xml);
					var nsResolver = document.createNSResolver( xmldom.ownerDocument == null ? 
							xmldom.documentElement : 
								xmldom.ownerDocument.documentElement );
					var queryResult = xmldom.evaluate('//rdf:Description', xmldom, nsResolver, 
							5, null);
					var states_obj = JSON.parse(states.value);

					var value = queryResult.iterateNext();
					var storedAnnotation = ''
		            while(value){
		            	store.put({annotation:value.getAttribute('rdf:about')})
		            	storedAnnotation = store.get(value.getAttribute('rdf:about'))
		            	storedAnnotation.state = states_obj[storedAnnotation.annotation]
		            	var nodes = value.childNodes;
		            	var child = ""
		            	for(i=0; i<nodes.length; i++) {
		            		child = nodes[i];
		            		if (child.localName == "hasBody") {
		            			storedAnnotation.hasBody 
		            				= "<a href=\'" + child.getAttribute('rdf:resource') + "\'>" +
				            		child.getAttribute('rdf:resource') + "</a>" 		            			
		            		}
		            		if (child.localName == "hasTarget") {
		            			storedAnnotation.hasTarget 
				            		= "<a href=\'" + child.getAttribute('rdf:resource') + "\'>" +
				            		child.getAttribute('rdf:resource') + "</a>"
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
						escapeHTMLInData: false,
						structure: 
						            [
						             new gridCells.RowIndex({ width: "10%" }),
						             {name: "Annotation", field: "annotation", width: "auto"},
						             {name: "hasTarget", field: "hasTarget", width: "auto"},
						             {name: "hasBody", field: "hasBody", width: "auto"},
						             {name: "state", field: "state", width: "auto"}
						            ],
						selectionMode: "multiple"
					 },div_id); 
					
					function reportSelection(node){
						var items = grid.selection.getSelected();
						var tmp = baseArray.map(items, function(item){
							return item.annotation;
						}, grid);
						var msg = "You have selected row" + ((tmp.length > 1) ? "s ": " ");
						node.innerHTML = msg + tmp.join(", ");
					}
					grid.on("SelectionChanged",
					lang.hitch(this, reportSelection, document.getElementById("clicked")), true);
				
					grid.startup();	            
				}
			}
});