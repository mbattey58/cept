# Ceph client connection examples

Various examples of how to send REST requests to S3 using only raw URLs + HTTP headers.

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

# ListObjects (GET/bucket_name request)

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
                           key_name=None,
                           action=None)
    print('\nResponse')
    print('Response code: %d\n' % r.status_code)
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

Copy content of file into object. Notice use of "-a" (action) to specify
key name.

```shell
./s3-rest.py -m put -p tmp/tmp-blob3 -f -b uv-bucket-3 \
             -a tmp-blobX3 -c config/s3-credentials2.json
```

Retrieve list of all uploads.

```shell
./s3-rest.py  -b uv-bucket-3  -t "uploads=" -c config/s3-credentials2.json
```

Download object to file, key name as action.
`GET` is the default method and does not have to be explicitly specified.

```shell
./s3-rest.py -c config/s3-credentials2.json -b uv-bucket-3 \
             -a tmp-blob1 -n tmp/tmp-download
```

Put object with metadata. Action = key name

```shell
./s3-rest.py  -m put -b uv-bucket-3 -a "some_text" \
              -c config/s3-credentials2.json -p "hello world" \
              -e "x-amz-meta-mymeta:My first metadata"
```

Retrieve metadata,  `x-amz-meta-`_metadata_lowecase_. Action = key name

```shell
./s3-rest.py -m head -b uv-bucket-3 -a some_text -c config/s3-credentials2.json

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

URI: /_bucket_name_/_action_name_?key1=value1&...

Use:

* `--bucket=bucket_name` or `-b`
* `--action=action_name` or `-a`
* `--parameters="key1=value1;key2=value2"` or `-t`

The (host, port) information is read from the configuration file.
Keys are specified as actions.

Use `key=` for keys with no values associated.
 
### Using templates

Any payload can be templated with variables substituted with values before
the content is sent to the `send_s3_request` function.
Use the `--substiture_parameters="var1=value1;var2=value2..."` or `-x` command
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
s3-rest.py -c config_file -p notification.xml -f -m get \
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
./s3-rest.py -m put -b uv-bucket-3 -a key-multipart-test10 -t "tagging=" \
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
./s3-rest.py -m get -b uv-bucket-3 -a key-multipart-test10 -t "tagging=" `
             -c config/s3-credentials2.json

...
Tagging: None
  TagSet: None
    Tag: None
      Key: MyTagKey <----
      Value: MyTagValue <----
```

## Web request logger

The repository includes `etc/log-web-requests.py` which implements a minimal
webserver which logs received web requests through a configurable logger,
`logging` module being the default, and answers with configurable responses,
default is an empty `200` (`OK`) status code. Useful to debug _REST_ requests
and e.g. compare them to the one sent by _boto3_ and similar toolkits.

## Status

Under development, will add more examples covering tagging and advanced features;
will also add an S3 web gateway proxy to filter, sign, log and change requests and
reponses on the fly.

Notifications have not been properly tested.

## References

[Ceph S3 requests](https://access.redhat.com/documentation/en-us/red_hat_ceph_storage/3/html/developer_guide/ceph-object-gateway-s3-api#s3-api-put-bucket-lifecycle)

[AWS S3 Requests](https://docs.aws.amazon.com/AmazonS3/latest/API/API_Operations.html)

[Notifications](https://medium.com/analytics-vidhya/automated-data-pipeline-using-ceph-notifications-and-kserving-5e1e9b996661)
