define(["dojo/_base/declare","dijit/_WidgetBase", "dijit/_TemplatedMixin", 
        "dojo/text!./templates/DCTypesVocab.html",  "dojo/dom-style"], 
    function(declare, _WidgetBase, _TemplatedMixin, template, domStyle){
        return declare("DCTypesVocab", [_WidgetBase, _TemplatedMixin], {        	
        	// Some default values for the triple
        	subject: "",
        	property: "",
        	object: "",
        	
        	// Our template - important!
        	templateString: template,
        	
        	// A class to be applied to the root node in our template
            baseClass: "SimpleWidget",
            
            
         // postCreate is called once our widget's DOM is ready,
			// but BEFORE it's been inserted into the page!
			// This is far and away the best point to put in any special work.
			postCreate: function(){
				// Get a DOM node reference for the root of our widget
				var domNode = this.domNode;

				// Run any parent postCreate processes - can be done at any point
				this.inherited(arguments);

				domStyle.set(this.dcuri, "display", "");	
				domStyle.set(this.dctextarea, "display", "none");
			},
			
			update: function(evt) {
				if (evt.currentTarget.value == "http://purl.org/dc/dcmitype/Text") {
					domStyle.set(this.dcuri, "display", "none");	
					domStyle.set(this.dctextarea, "display", "");
				} else {
					domStyle.set(this.dcuri, "display", "");	
					domStyle.set(this.dctextarea, "display", "none");
				}
			},
			
			assert: function() {
				return "a dctypes:" + this.dctype[this.dctype.selectedIndex].text;
			}
        });
});