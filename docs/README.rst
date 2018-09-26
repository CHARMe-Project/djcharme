Documentation and Examples
==========================

The `CHARMeNodeInstallation <https://github.com/CHARMe-Project/djcharme/blob/develop/djcharme/docs/CHARMeNodeInstallation.pdf>`_
provides details of installing the central node and the
`CHARMeNodeICD <https://github.com/CHARMe-Project/djcharme/blob/develop/djcharme/docs/CHARMeNodeICD.pdf>`_
provides details of the interface.

Using curl to Communicate with the Central Node
-----------------------------------------------

This directory contains some example ttl files, these are the examples from the
`CHARMeNodeICD <https://github.com/CHARMe-Project/djcharme/blob/develop/djcharme/docs/CHARMeNodeICD.pdf>`_.

Some of these example require you to be authenticated via a token (inserting, 
reporting and deleting annotations). Currently doing this using curl is a bit
clunky.

First setup the user specific values::

	# the dir containing the example ttl files
	export data_dir=</path/to/example/ttl/files/>
	# your username
	export username=<username>
	# your password
	export password=<password>
	# the CHARMe node
	export charme_node=https://charme-test.cems.rl.ac.uk
	# the client id, you need to register a client to obtain an id, but for
	# testing purposes you may use the client on the central test node
	export client_id=9803bd928f9f99844cfa

Now get a token via curl::

	mkdir /tmp/charme
	cd /tmp/charme
	curl ${charme_node}/accounts/login/ -c cookies.txt -b cookies.txt > /dev/null
	export csrftoken=`grep csrftoken cookies.txt | awk '{print $7}'`; echo $csrftoken
	curl -X POST ${charme_node}/accounts/login/ -c cookies.txt -b cookies.txt -d "username=${username}&password=${password}&a=1&csrfmiddlewaretoken=$csrftoken" -H "Referer: ${charme_node}/accounts/login/" > /dev/null
	curl -X GET ${charme_node}"/oauth2/authorize?client_id=${client_id}&response_type=token" -c cookies.txt -b cookies.txt -D /tmp/header -L  > /dev/null
	export access_token=`grep access_token /tmp/header | cut -d'=' -f2 | cut -d'&' -f1`;echo ${access_token}

This access_token can then be used in the examples below that use curl to make calls to the central node.

Inserting Annotations
~~~~~~~~~~~~~~~~~~~~~

To insert an annotation::

	export anno_uri=`curl -X POST ${charme_node}/insert/annotation -d@${data_dir}/05_textAnnotation.ttl -H "Authorization: Token ${access_token}" -D /tmp/header -H 'Content-Type: text/turtle'`;echo $anno_uri

Viewing Annotations
~~~~~~~~~~~~~~~~~~~

You can view an annotation via a web browser or you can programmatically
retrieve it::

	curl -X GET $anno_uri -D header  -H 'Accept: json-ld' -L
	
You can specify the format or the returned data and the ``depth``, the number of
links to follow when retrieving the graph::

	curl -X GET $anno_uri?depth=1 -D header  -H 'Accept: text/turtle' -L
	
See the
`CHARMeNodeICD <https://github.com/CHARMe-Project/djcharme/blob/develop/djcharme/docs/CHARMeNodeICD.pdf>`_
for more details

Reporting An Annotation
~~~~~~~~~~~~~~~~~~~~~~~

An annotation can be reported to a moderator. This will be the owner of the
client with which the annotation was made::

	curl -X PUT $anno_uri/reporttomoderator/ -H "Authorization: Token $access_token" -D header -L  -d@${data_dir}moderator.txt; grep HTTP header

Deleting An Annotation
~~~~~~~~~~~~~~~~~~~~~~

If you created an annotation or you are a moderator for an annotation then you
will have permission to delete it. **N.B.** This is a logical delete::

	curl -X DELETE $anno_uri -H 'Accept: text/html' -H "Authorization: Token $access_token" -D header; grep HTTP header
	
The Open Search Interface
-------------------------

These examples are designed to be used with a web browser although they can be
adapted to be used programmatically.

The Suggest Option
~~~~~~~~~~~~~~~~~~

The *suggest* call was developed for use by a faceted search tool. Using
*suggest* you can retrieve lists of values for *bodyType, citingType,
dataType, domainOfInterest, motivation* and *organization*. The results can be
restricted by the use of filters, see the 
`CHARMeNodeICD <https://github.com/CHARMe-Project/djcharme/blob/develop/djcharme/docs/CHARMeNodeICD.pdf>`_
for a full list of options. 

To find the list of values used for *motivation*::

	https://charme-test.cems.rl.ac.uk/suggest/atom?depth=1&status=submitted&q=motivation

Then to find the list of values used for *organization* that have annotations
with a *motivation* of *linking*::

	https://charme-test.cems.rl.ac.uk/suggest/atom?depth=1&status=submitted&q=organization&motivation=http://www.w3.org/ns/oa%23linking

The Search Option
~~~~~~~~~~~~~~~~~

Some example searches::

	https://charme-test.cems.rl.ac.uk/search/atom?depth=1&status=submitted&dataType=http://purl.org/dc/dcmitype/Dataset
	https://charme-test.cems.rl.ac.uk/search/atom?depth=1&status=submitted&motivation=http://www.w3.org/ns/oa%23tagging

See the
`CHARMeNodeICD <https://github.com/CHARMe-Project/djcharme/blob/develop/djcharme/docs/CHARMeNodeICD.pdf>`_
for a full list of options.

SPARQL Interface
----------------

A SPARQL endpoint is provided at::

	https://charme-test.cems.rl.ac.uk/sparql

Alternatively you can use the SPARQL web interface::

	https://charme-test.cems.rl.ac.uk/sparql.html
