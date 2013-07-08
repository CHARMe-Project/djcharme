define(["dojo/_base/declare", "dijit/form/TextBox", 
        "dijit/_WidgetBase", "dijit/_TemplatedMixin", "dijit/_WidgetsInTemplateMixin",
        "dojo/text!./templates/OATarget.html"], 
    function(declare, textBox, _WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin, template){
        return declare("OATarget", [_WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin], {        	       	
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
			},
						
			generate: function() {
				var description = {}
				description.uri = "<" + this.target_uri.value + ">"
				description.detail = description.uri + "\n" + 'dc:format "html/text" \n';  
				console.log("OATarget description uri: " + description.uri);
				console.log("OATarget description detail: " + description.detail);
				return description;
			}
        });
});