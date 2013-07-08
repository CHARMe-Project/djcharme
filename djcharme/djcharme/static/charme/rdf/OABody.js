define(["dojo/_base/declare", "dijit/form/Select", "rdf/TextualBody", "dijit/form/TextBox", 
        "dijit/_WidgetBase", "dijit/_TemplatedMixin", "dijit/_WidgetsInTemplateMixin",
        "dojo/text!./templates/OABody.html",  "dojo/dom-style", ], 
    function(declare, select, textualBody, textBox, _WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin, template, domStyle){
        return declare("OABody", [_WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin], {        	
        	// Some default values for the triple
        	type: "",
        	
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

				domStyle.set(this.bodyuri, "display", "");	
				domStyle.set(this.bodytext, "display", "none");
				this.type = 'URI';
			},
			
			update: function(evt) {
				if (evt.currentTarget.value == "Text") {
					domStyle.set(this.bodyuri, "display", "none");	
					domStyle.set(this.bodytext, "display", "");
					this.type = 'Text';
				} else {
					domStyle.set(this.bodyuri, "display", "");	
					domStyle.set(this.bodytext, "display", "none");
					this.type = 'URI';
				}
			},
			
			generate: function() {
				var description = {}
				var ret = "body ";
				switch (this.type) {
					case "Text":
						description.uri = "anno:b_" + new Date().getTime();
						description.detail = description.uri + "\n" + this.body_text.generate();  
						break;
					case "URI":
						description.uri = "<" + this.body_uri.value + ">";
						description.detail = description.uri + "\n" + 'dc:format "text/html"';
						break;
				}
				console.log("OABody description uri: " + description.uri);
				console.log("OABody description detail: " + description.detail);
				return description;
			}
        });
});