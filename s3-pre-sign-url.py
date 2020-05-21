#!/bin/env python3
"""Generate pre-singned URL to give access to data stored into S3 archive.

   __author__       = "Ugo Varetto"
   __credits__      = ["Ugo Varetto", "Luca Cervigni"]
   __license__      = "MIT"
   __version__      = "0.2"
   __maintainer__   = "Ugo Varetto"
   __email__        = "ugovaretto@gmail.com"
   __status__       = "Development"

   Run with --help to see options.

   Additional request parameters can be specified on the command line.
   When sending requests with curl make sure the method matches the one
   specified when generating the pre-signed URL.
"""
import hashlib
import hmac
import argparse
import datetime
from requests.utils import quote
from urllib.parse import urlparse
from urllib.parse import urlencode


def str_to_seconds(days=0, hours=0, minutes=0, seconds=0):
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def parse_time(t: str):
    return tuple(int(i) for i in t.split(":"))


def hash(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def create_signature_key(key, date_stamp, region, service):
    date_key = hash(('AWS4' + key).encode('utf-8'), date_stamp)
    region_key = hash(date_key, region)
    service_key = hash(region_key, service)
    signing_key = hash(service_key, 'aws4_request')
    return signing_key


def pre_sign_url(method, region, bucket_name, key_name,
                 endpoint, expiration, params):

    # canonical request
    time = datetime.datetime.utcnow()
    time_stamp = time.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = time.strftime('%Y%m%d')

    credentials = access_key + '/' + date_stamp + '/' + region + \
        '/s3/aws4_request'

    parameters = {'X-Amz-Algorithm': 'AWS4-HMAC-SHA256',
                  'X-Amz-Credential': credentials,
                  'X-Amz-Date': time_stamp,
                  'X-Amz-Expires': str(expiration),
                  'X-Amz-SignedHeaders': 'host'}
    if params:
        parameters.update(params)

    canonical_query_string_url_encoded = urlencode(parameters)

    canonical_resource = '/'
    if bucket_name:
        canonical_resource += bucket_name
        if key_name:
            canonical_resource += '/' + key_name
    # canonical_resource_url_encoded = quote(canonical_resource)

    payload_hash = 'UNSIGNED-PAYLOAD'
    canonical_headers = 'host:' + host
    signed_headers = 'host'

    canonical_request = (method + '\n' +
                         canonical_resource + '\n' +
                         canonical_query_string_url_encoded + '\n' +
                         canonical_headers + '\n' +
                         '\n' +
                         signed_headers + '\n' +
                         payload_hash).encode('utf-8')

    # text to sign
    hashing_algorithm = 'AWS4-HMAC-SHA256'
    credential_ctx = date_stamp + '/' + region + '/' + 's3' + '/' + \
        'aws4_request'
    string_to_sign = (hashing_algorithm + '\n' +
                      time_stamp + '\n' +
                      credential_ctx + '\n' +
                      hashlib.sha256(canonical_request).hexdigest())

    # generate the signature
    signature_key = create_signature_key(secret_key, date_stamp, region, 's3')
    signature = hmac.new(signature_key, string_to_sign.encode('utf-8'),
                         hashlib.sha256).hexdigest()

    request_url = (endpoint +
                   (('/' + bucket_name) if bucket_name else "") +
                   (('/' + key_name) if key_name else "") +
                   '?' +
                   canonical_query_string_url_encoded +
                   '&X-Amz-Signature=' +
                   signature)

    return request_url


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Generate pre-singed URL for distribution')
    parser.add_argument("-a", "--access_key", type=str, required=True,
                        dest="access_key", help="AWS access key")
    parser.add_argument("-s", "--secreat_key", type=str, required=True,
                        dest="secret_key", help="AWS secret key")
    parser.add_argument("-b", "--bucket", type=str, required=False,
                        dest="bucket", help="bucket name")
    parser.add_argument("-k", "--key", type=str, required=False,
                        dest="key", help="object key name")
    parser.add_argument("-t", "--expiration", type=str, required=True,
                        dest="expiration",
                        help="expiration, format: days:hours:minutes:seconds")
    parser.add_argument("-e", "--endpoint_url", type=str, required=True,
                        dest="endpoint",
                        help="endpoint url")
    parser.add_argument("-m", "--method", type=str, required=False,
                        default="GET", dest="method",
                        help="http method: get | put | post")
    parser.add_argument("-p", "--parameters", type=str, required=False,
                        dest="params",
                        help="request parameters to be added to the URI " +
                             "in the form of ';' list of 'key=value' pairs; " +
                              "use 'key=' for empty values")
    parser.add_argument("-P", "--print-parameters", type=str, required=False,
                        dest="print_params", nargs="?", const=True,
                        help="print request parameters")

    args = parser.parse_args()

    access_key = args.access_key
    secret_key = args.secret_key

    # request elements
    method = args.method.upper()
    region = 'us-east-1'
    bucket_name = args.bucket
    key_name = args.key
    endpoint = args.endpoint
    expiration = str_to_seconds(*parse_time(args.expiration))
    up = urlparse(args.endpoint)
    host = up.hostname + f":{up.port}" if up.port else ""
    params = None
    if args.params:
        params = dict(x.split('=') for x in args.params.split(';'))

    signed_url = pre_sign_url(method, region, bucket_name, key_name,
                              endpoint, expiration, params)

    print("\n" + signed_url + "\n")
    if args.print_params:
        print(params)
