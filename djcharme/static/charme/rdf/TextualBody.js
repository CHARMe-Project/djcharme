define(["dojo/_base/declare", "dijit/form/Textarea", "dijit/_WidgetBase", "dijit/_TemplatedMixin", 
        "dojo/text!./templates/TextualBody.html"], 
    function(declare, textarea, _WidgetBase, _TemplatedMixin, template, domStyle){
        return declare("TextualBody", [_WidgetBase, _TemplatedMixin], {        	
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
				var content = this.textual_body.value				
				var ret = 'a cnt:ContentAsText, dctypes:Text ;\n';
				ret += 'cnt:chars ' + '"' + content + '" ;\n';
				ret += 'dc:format "text/plain"';
				console.log("TextualBody: " + ret)
				return ret;
			}
        });
});

                    //[
                    //    "@type": [
                    //        "http://www.w3.org/2011/content#ContentAsText",
                    //        "http://purl.org/dc/dcmitype/Text"
                    //    ],
                    //    "http://purl.org/dc/elements/1.1/format": "text/plain",
                    //    "http://www.w3.org/2011/content#chars": "hello there!"
                    //]