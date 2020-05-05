#!/usr/bin/env python3

# Pure REST request to S3/Ceph backend
# List buckets
# Code modified from the AWS EC2 API reference documentation

import urllib
import hashlib
import datetime
import base64
import hmac
import requests
import json


def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def get_signature(key, dateStamp, regionName, serviceName):
    kDate = sign(('AWS4' + key).encode('utf-8'), dateStamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, 'aws4_request')
    return kSigning


if __name__ == "__main__":

    with open("s3-credentials.json", "r") as f:
        credentials = json.loads(f.read())
    access_key = credentials['access_key']
    secret_key = credentials['secret_key']

    method = 'GET'
    service = 's3'
    host = 'nimbus.pawsey.org.au'
    region = 'us-east-1'
    # endpoint =  'http://localhost:8000'
    endpoint = 'https://nimbus.pawsey.org.au:8080'
    # ListBuckets
    # GET / HTTP/1.1
    request_parameters = ''

    # dates for headers credential string
    t = datetime.datetime.utcnow()
    amzdate = t.strftime('%Y%m%dT%H%M%SZ')
    datestamp = t.strftime('%Y%m%d')  # Date w/o time, used in credential scope

    # canonical URI
    canonical_uri = '/'
    canonical_querystring = request_parameters

    # payload, empty in this case
    payload_hash = hashlib.sha256(('').encode('utf-8')).hexdigest()

    # headers: canonical and singned header list
    canonical_headers = 'host:' + host + '\n' + "x-amz-content-sha256:" + \
        payload_hash + '\n' + 'x-amz-date:' + amzdate + '\n'

    signed_headers = 'host;x-amz-content-sha256;x-amz-date'

    # canonical request
    canonical_request = method + "\n" + canonical_uri + '\n' + canonical_querystring + \
        '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash

    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = datestamp + '/' + region + \
        '/' + service + '/' + 'aws4_request'

    # string to sign
    string_to_sign = algorithm + '\n' + amzdate + '\n' + credential_scope + \
        '\n' + hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()

    signing_key = get_signature(secret_key, datestamp, region, service)

    # sign string with signing key
    signature = hmac.new(signing_key, (string_to_sign).encode(
        'utf-8'), hashlib.sha256).hexdigest()

    # build authorisaton header
    authorization_header = algorithm + ' ' + 'Credential=' + access_key + '/' + \
        credential_scope + ', ' + 'SignedHeaders=' + \
        signed_headers + ', ' + 'Signature=' + signature

    # build standard headers
    headers = {'Host': host, 'X-Amz-Content-SHA256': payload_hash,
               'X-Amz-Date': amzdate,  'Authorization': authorization_header}

    # build request
    request_url = endpoint + '?' + canonical_querystring

    # send request and print response
    print('Request URL = ' + request_url)
    print(headers)
    r = requests.get(request_url, headers=headers)

    print('\nResponse')
    print('Response code: %d\n' % r.status_code)
    print(r.text)
