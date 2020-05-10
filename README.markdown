# Ceph client connection examples

Various examples of how to send REST requests to S3 using only raw URLs + HTTP headers.

`s3v4_rest.py` is a module implementing a generic interface to `S3/Ceph`, taking care of building the signed request header and generating the REST URLs, MIT licensed. PEP8, static typing not fully applied everywhere, wont' pass `mypy` validation.

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

## S3 REST client

*s3-rest.py* is a generic S3 REST client which allows to send request directly
from the commend line.
Launch without parameters to see options.
Credentials are read from a configuration files wih the same structure as the
one described above.

### Examples

Retrieve bucket list.

```shell
s3-rest.py --method=get  --config_file=config/s3-credentials2.json
```

List objects with version information.

```shell
s3-rest.py --method=get --config_file=config/s3-credentials2.json \
                   --bucket=uv-bucket-3 --parameters="versions=''
```

## Web request logger

The repository includes `etc/log-web-requests.py` which implements a minimal
webserver which logs received web requests through a configurable logger,
`logging` module being the defaule, and answers with configurable responses,
default is an empty `200` (`OK`) status code. Useful to debug _REST_ requests
and e.g. compare them to the one sent by _boto3_ and similar toolkits.

## References

[Ceph S3 requests](https://access.redhat.com/documentation/en-us/red_hat_ceph_storage/3/html/developer_guide/ceph-object-gateway-s3-api#s3-api-put-bucket-lifecycle)

[AWS S3 Requests](https://docs.aws.amazon.com/AmazonS3/latest/API/API_Operations.html)

[Notifications](https://medium.com/analytics-vidhya/automated-data-pipeline-using-ceph-notifications-and-kserving-5e1e9b996661)
