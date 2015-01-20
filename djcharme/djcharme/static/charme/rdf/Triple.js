define(["dojox/xml/parser", "dojox/grid/DataGrid", "dojo/store/Memory",
		"dojo/data/ObjectStore", "dojox/grid/cells", "dojo/_base/lang", 
		"dojo/_base/array", "dojo/json", "dojox/grid/_CheckBoxSelector"],
		function(parser, DataGrid, Memory, ObjectStore, gridCells, lang, baseArray, JSON){
			return {
				describeAnnotation: function(xml, states, div_id){
					var store = new Memory({ idProperty: "key" });

					var xmldom = parser.parse(xml);
					var nsResolver = document.createNSResolver( xmldom.ownerDocument == null ? 
							xmldom.documentElement : 
								xmldom.ownerDocument.documentElement );
					var queryResult = xmldom.evaluate('//rdf:Description', xmldom, nsResolver, 
							5, null);
					
					var states_obj = null
					try { 
						states_obj = JSON.parse(states.value);
					} catch (e) {
						
					}

					var value = queryResult.iterateNext();
					var storedAnnotation = '';
					var keyValue = 0;
		            while(value){            	
		            	var nodes = value.childNodes;
		            	var child = "";
		            	for(i=0; i<nodes.length; i++) {
		            		child = nodes[i];
		            		if (child.localName == "hasBody") {
		            			storedAnnotation=getStoredAnnotation(store, value)
		            			storedAnnotation.property = "hasBody"		            			
			            		storedAnnotation.value = child.getAttribute('rdf:resource');
				            	continue
		            		} 
		            		if (child.localName == "hasTarget") {
		            			storedAnnotation=getStoredAnnotation(store, value)
		            			storedAnnotation.property = "hasTarget"		            			
		            			storedAnnotation.value = child.getAttribute('rdf:resource');
				            	continue
				            }
		            		if (child.localName == "annotatedBy") {
		            			storedAnnotation=getStoredAnnotation(store, value)
		            			storedAnnotation.property = "annotatedBy"		            			
			            		storedAnnotation.value = child.getAttribute('rdf:resource');
				            	continue
				            }
		            		if (child.localName == "annotatedAt") {
		            			storedAnnotation=getStoredAnnotation(store, value)
		            			storedAnnotation.property = "annotatedAt"		            			
				            	storedAnnotation.value = child.textContent;
				            	continue
				            }
		            		if (child.localName == "accountName") {
		            			storedAnnotation=getStoredAnnotation(store, value)
		            			storedAnnotation.property = "accountName"		            			
				            	storedAnnotation.value = child.textContent;
				            	continue
				            }
		            		if (child.localName == "givenName") {
		            			storedAnnotation=getStoredAnnotation(store, value)
		            			storedAnnotation.property = "givenName"		            			
				            	storedAnnotation.value = child.textContent;
				            	continue
				            }
		            		if (child.localName == "familyName") {
		            			storedAnnotation=getStoredAnnotation(store, value)
		            			storedAnnotation.property = "familyName"		            			
				            	storedAnnotation.value = child.textContent;
				            	continue
				            }
		            		if (child.localName == "name") {
		            			storedAnnotation=getStoredAnnotation(store, value)
		            			storedAnnotation.property = "name"		            			
				            	storedAnnotation.value = child.textContent;
				            	keyValue++
				            	continue
				            }		            			
		            		if (child.localName == "type") {
		            			storedAnnotation=getStoredAnnotation(store, value)
		            			storedAnnotation.property = "type"		            			
				            	storedAnnotation.value = child.getAttribute('rdf:resource');
				            	continue
				            }		            		
		            	}
		                value = queryResult.iterateNext();
		            }
					
					var dataStore = new ObjectStore({ objectStore: store });

					var grid = new DataGrid({
						store: dataStore,
						query: { annotation: "*" },
						escapeHTMLInData: false,
						structure: 
						            [
						             new gridCells.RowIndex({ width: "10%" }),
						             {name: "Resource", field: "annotation", width: "100%",
						            	 formatter: function(value) {  
						            	 	return "<a href=\'" + value + "\'>" + value + "</a>"; 
						             	 }
						             },
						             {name: "Property", field: "property", width: "100%",
						            	 formatter: function(value) {  
					            	 		return value; 
					             	 	}
						             },
						             {name: "Value", field: "value", width: "100%",
					            	 formatter: function(value) {  
				            	 		return "<a href=\'" + value + "\'>" + value + "</a>"; 				             	 	
						             	}
						             },						             
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
					
					function getStoredAnnotation(store,value){
		            	keyValue++
		            	store.put({key:keyValue});
		            	storedAnnotation = store.get(keyValue);
		            	storedAnnotation.annotation=value.getAttribute('rdf:about')
		            	return storedAnnotation
					}
					
					grid.on("SelectionChanged",
					lang.hitch(this, reportSelection, document.getElementById("clicked")), true);
				
					grid.startup();	            
				}
			}
});