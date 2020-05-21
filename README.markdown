# Ceph client connection examples

Various examples of how to send REST requests to S3 using only raw URLs + HTTP headers. Used to test Ceph, can be used with any S3-compliant server, or any
service which uses the AWS header signing algorithm.

`s3v4_rest.py` is a module implementing a generic interface to `S3/Ceph`,
taking care of building the signed request header and generating the REST URLs,
MIT licensed. PEP8 compliant, static typing not fully applied everywhere, wont' pass `mypy` validation.

In the examples authentication and endpoint information is read from json files with the following format:

```json
{
    "version"    : "2",
    "access_key": "FFFFFFF",
    "secret_key": "FFFFFFF",
    "protocol"  : "https",
    "host"      : "aaa.bbb.com",
    "port"      : 8888
}
```

Tested on Python 3.7 and 3.8.

Dependencies

```python
from urllib.parse import urlencode
import hashlib
import datetime
import hmac
import xml.etree.ElementTree as ET
import json
import requests
import logging
import time
import xml.dom.minidom  # better than ET for pretty printing
from typing import Dict, Tuple, List, Union, ByteString, Callable
```

There are two functions you can use to send requests, one takes care of
configuring everything and sending the request, the other only returns
headers and URL and requires the client code to send the request to the
server; this last method is required when dealing with multi-stage requests
like multi-part uploads (example code provided).

E.g. list objects version 2:

```python
#!/usr/bin/env python3
import s3v4_rest as s3
import requests
import sys

# ListObjects V2 (GET/bucket_name request)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <json configuration file> <bucket name>",
              file=sys.stderr)
        sys.exit(-1)
    config_file = sys.argv[1]
    bucket_name = sys.argv[2]
    bucket_name = "uv-bucket-3"
    r = s3.send_s3_request(config=config_file,
                           req_method='GET',
                           parameters={"list-type": "2"},  #WORKS with Ceph
                           payload=None,
                           sign_payload=False,
                           payload_is_file_name=False,
                           bucket_name=bucket_name,
                           key_name=None)
    print('\nResponse')
    print(f"Response code: {r.status_code}\n")
    print(r.text)

    # parse and print XML response
    print("\n")
    print(s3.xml_to_text(r.text))
    print("\n")

```

## S3 REST client

*s3-rest.py* is a generic S3 REST client which allows to send requests directly
from the command line.
Launch without parameters to see options.
Credentials are read from a configuration file wih the same structure as the
one described above.
Request content can be both passed on the command line or read from file.
Content signing is currently not supported for payloads read from file.

### Examples

Retrieve bucket list.

```shell
s3-rest.py --method=get --config_file=config/s3-credentials2.json
```

List objects with version information.

```shell
s3-rest.py --method=get --config_file=config/s3-credentials2.json \
           --bucket=uv-bucket-3 --parameters="versions="
```

Copy content of file into object.

```shell
./s3-rest.py -m put -p tmp/tmp-blob3 -f -b uv-bucket-3 \
             -k tmp-blobX3 -c config/s3-credentials2.json
```

Retrieve list of all multi-part uploads.

```shell
./s3-rest.py  -b uv-bucket-3  -t "uploads=" -c config/s3-credentials2.json
```

Download object to file.
`GET` is the default method and does not have to be explicitly specified.

```shell
./s3-rest.py -c config/s3-credentials2.json -b uv-bucket-3 \
             -k tmp-blob1 -n tmp/tmp-download
```

Put object with metadata.

```shell
./s3-rest.py  -m put -b uv-bucket-3 -k "some_text" \
              -c config/s3-credentials2.json -p "hello world" \
              -e "x-amz-meta-mymeta:My first metadata"
```

Retrieve metadata,  `x-amz-meta-`_metadata_lowecase_.

```shell
./s3-rest.py -m head -b uv-bucket-3 -k some_text -c config/s3-credentials2.json

Response headers: {'Content-Length': '11', ...,
                   'x-amz-meta-mymeta': 'My first metadata', <==
                   'x-amz-request-id': ...
                  }
```

Override configuration read from json file using the `--override_configuration`
(or `-O`) command line switch.
Metadata search through Ceph/elasticsearch, need to use different address.

```shell
./s3-rest.py -b uv-bucket-3 -c config/s3-credentials2.json -b uv-bucket-3 \
             -t"query=name==text_message" -O "port=8002"
```

### Specifying URIs

URI: /_bucket_name_/_key_name_?key1=value1&...

Use:

* `--bucket=bucket_name` or `-b`
* `--key=key_name` or `-k`
* `--parameters="key1=value1;key2=value2"` or `-t`

The (host, port) information is read from the configuration file.

Use `key=` for parameter keys with no associated value.

### Using templates

Any payload can be templated with variables substituted with values before
the content is sent to the `send_s3_request` function.
Use the `--substitute_parameters="var1=value1;var2=value2..."` or `-x` command
line switch to specify the parameters to replace.

E.g. reading an xml request from file:

XML request:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<NotificationConfiguration xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
   <TopicConfiguration>
      <Event>@event</Event>
      <Id>@id</Id>
      <Topic>@topic</Topic>
   </TopicConfiguration>
</NotificationConfiguration>
```

Command line invocation:

```shell
s3-rest.py -c config_file -p notification.xml -f -m post \
           -x "@event=s3:ObjectCreated:*;@id=ObjectCreatedId;@topic=Storage"
```

* `-c config_file` json configuration file
* `-p notification.xml` file name as payload
* `-f` treat payload as filename and read content from file
* `-m get` `GET` method
* `-x ...` replace keys with values in file specified as payload before sending

### Example: adding and reading tags

**Tag request** (file `xml/PutObjectTagging-template.xml`):

```xml
<Tagging xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
   <TagSet>
      <Tag>
         <Key>@key</Key>
         <Value>@value</Value>
      </Tag>
   </TagSet>
</Tagging>
```

**Add tag reading from xml file and subsituting values**:

```shell
./s3-rest.py -m put -b uv-bucket-3 -k key-multipart-test10 -t "tagging=" \
             -c config/s3-credentials2.json \
             -p xml-requests/PutObjectTagging-template.xml \
             -f -x"@key=MyTagKey;@value=MyTagValue"

Elapsed time: 0.3629160429991316 (s)
Response status: 200
Response headers: {'x-amz-request-id':
'tx00000000000000045b60c-005eba4e8f-7623f06d-objectstorage',
'Content-Type': 'application/xml',
'Content-Length': '0',
'Date': 'Tue, 12 May 2020 07:21:52 GMT', 'Connection': 'Keep-Alive'}
```

* `-p` payload (a filename in this case)
* `-f` specify that payload is filename and contente has to be read from file
* `-x` substitute keys with values in payload (content read from file in this case)

Note that you can set more that one tag at once, just add more tags into
`TagSet`.

**Retrieve and print tags associated with key**:

```shell
./s3-rest.py -m get -b uv-bucket-3 -k key-multipart-test10 -t "tagging=" `
             -c config/s3-credentials2.json

...
Tagging: None
  TagSet: None
    Tag: None
      Key: MyTagKey <----
      Value: MyTagValue <----
```

### Example: appending/streaming data into an object

In order to create appendable object the object must be created with an
append action, appending data at position zero.

```shell
./s3-rest.py -c config/s3-credentials2.json -b append-bucket \
             -k object-5 -m put -t"append=;position=0" -p "Hello" \
             -H "x-rgw-next-append-position"

RESPONSE STATUS CODE: 200
RESPONSE HEADERS
====================
Content-Length: 0
ETag: "6e6bc4e49dd477ebc98ef4046c067b5f"
Accept-Ranges: bytes
x-rgw-next-append-position: 4 <======
x-amz-request-id: tx00000000000000003c54d-005ec3e01b-76c8018f-objectstorage
Date: Tue, 19 May 2020 13:33:15 GMT
Connection: Keep-Alive

x-rgw-next-append-position: 4
```

`-H` searches for a header in the response and prints header name and value.

Notice the `x-rgw-next-append-position: 4` header which returns the append
position to use in the next append request to append data to the object.

To append:

```shell
./s3-rest.py -c config/s3-credentials2.json -b append-bucket -k object-5 \
             -m put -t"append=;position=4" -p "\n how are you?" \
             -H "x-rgw-next-append-position"

INFO:root:
RESPONSE STATUS CODE: 200
RESPONSE HEADERS
====================
Content-Length: 0
ETag: "b9b0be753cd84dc7c34c2fd7539ae588"
Accept-Ranges: bytes
x-rgw-next-append-position: 19
x-amz-request-id: tx000000000000000053eea-005ec3e04e-76c9b5d1-objectstorage
Date: Tue, 19 May 2020 13:34:06 GMT
Connection: Keep-Alive

x-rgw-next-append-position: 19
```

The next append position is simply the object size.
Note that `\n` are intepreted as two characters.

After another few additions, if you `stat` the object it will look like:

```shell
./s3-rest.py -c config/s3-credentials2.json -b append-bucket -k object-5 -m head

INFO:root:
RESPONSE STATUS CODE: 200
RESPONSE HEADERS
====================
Content-Length: 25
Accept-Ranges: bytes
Last-Modified: Tue, 19 May 2020 13:38:03 GMT
x-rgw-object-type: Appendable
x-rgw-next-append-position: 25
ETag: "fd7a16b1ec3f67458d0e887aca84b682-4"
x-amz-request-id: tx000000000000000069fff-005ec3e6c1-76c9b5d1-objectstorage
Content-Type: binary/octet-stream
Date: Tue, 19 May 2020 14:01:37 GMT
Connection: Keep-Alive
```

Notice the `x-rgw-object-type: Appendable` property, only object created from
the beginning with an append action can be appended to.

...and you can add meta data to the object in the process:

```shell
./s3-rest.py -c config/s3-credentials2.json -b append-bucket -k object-5 \
             -p "..." -t"append=;position=25" -m put \
             -H "x-rgw-next-append-position" 
             -e"x-amz-meta-some_meta_data_key:some meta data value"

./s3-rest.py -c config/s3-credentials2.json -b append-bucket -k object-5 -m head

Content-Length: 28
Accept-Ranges: bytes
Last-Modified: Tue, 19 May 2020 14:04:57 GMT
x-rgw-object-type: Appendable
x-rgw-next-append-position: 28
ETag: "e16fd5bd6cb1c49a463a174435a7f799-5"

x-amz-meta-some-meta-data-key: some meta data value <=====

x-amz-request-id: tx00000000000000004e698-005ec3e791-76c80189-objectstorage
Content-Type: binary/octet-stream
Date: Tue, 19 May 2020 14:05:05 GMT
Connection: Keep-Alive
```

And you can easily change any meta-data: just submit a request with a
zero-length payload:

```shell
./s3-rest.py -c config/s3-credentials2.json -b append-bucket -k object-5 \
             -p "" -t"append=;position=28" -m put  \
             -e"x-amz-meta-some_meta_data_key:CHANGED!"

./s3-rest.py -c config/s3-credentials2.json -b append-bucket -k object-5 -m head
...
x-rgw-object-type: Appendable
x-rgw-next-append-position: 28
ETag: "36982f73df7796f52d87ec5b85e1ce18-6"
x-amz-meta-some-meta-data-key: CHANGED! <=====
```

Notice how the meta-data has actually changed but the size has not.

**Caveat**: you cannot use versioning with appendable objects.

Note that the appended data can be of completely unrelated types with the
mime-type and position and size (which can also be computed), stored as metadata.
Individual pieces can then just be easily retrieved using the "Range=bytes=..."
request header.

Look at `webcam-stream-to-object.py` for an example of how to stream frames
from a webcam directly into a ceph object and retrieve individual frames.

## Web request logger and proxy

The repository includes `etc/log-web-requests.py` which implements a minimal
webserver which logs received web requests through a configurable logger,
`logging` module being the default, and answers with configurable responses,
default is a copy of the received request.
The web request logger also works as a proxy logging requests received from
a client and responses received from the server.

## Status

Under development. Version 0.5.

Notifications have not been properly tested.

## References

[Ceph S3 requests](https://access.redhat.com/documentation/en-us/red_hat_ceph_storage/3/html/developer_guide/ceph-object-gateway-s3-api#s3-api-put-bucket-lifecycle)

[AWS S3 Requests](https://docs.aws.amazon.com/AmazonS3/latest/API/API_Operations.html)

[Notifications](https://medium.com/analytics-vidhya/automated-data-pipeline-using-ceph-notifications-and-kserving-5e1e9b996661)
