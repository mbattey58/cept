#!/usr/bin/env python3

# Pure REST request to S3/Ceph backend
# List buckets
# Code modified from the AWS EC2 API reference documentation
# Author: Ugo Varetto

import urllib
import hashlib
import datetime
import base64
import hmac
import requests
import json
import xml.etree.ElementTree as ET


# standard signing functions from AWS
def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def get_signature(key, dateStamp, regionName, serviceName):
    kDate = sign(('AWS4' + key).encode('utf-8'), dateStamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, 'aws4_request')
    return kSigning


# ElementTree prefixes tags with a namespace if present
def clean_xml_tag(tag):
    closing_brace_index = tag.index('}')
    return tag if not closing_brace_index else tag[closing_brace_index+1:]


# note: Python as a limit on the recursion level it can handle,
#      this is just implemented like this without returning functions
#      or using stacks to keep the code simple
def print_xml_tree(node, indentation_level=0, filter=lambda t: True):
    BLANKS = 2
    indent = indentation_level * BLANKS
    if filter(node.tag):
        print(" "*indent + f"{clean_xml_tag(node.tag)}: {node.text}")
    for child in node:
        print_xml_tree(child, indentation_level + 1)


if __name__ == "__main__":

    # read configuration information
    with open("config/s3-credentials2.json", "r") as f:
        credentials = json.loads(f.read())

    protocol = credentials['protocol']
    host = credentials['host']
    port = credentials['port']
    access_key = credentials['access_key']
    secret_key = credentials['secret_key']

    method = 'GET'
    service = 's3'
    region = 'us-east-1'  # works with Ceph, any region might work actually
    # endpoint =  'http://localhost:8000'
    endpoint = protocol + '://' + host + (f":{port}" if port else '')

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
    canonical_headers = \
        'host:' + host + '\n' + \
        "x-amz-content-sha256:" + payload_hash + '\n' + \
        'x-amz-date:' + amzdate + '\n'

    signed_headers = 'host;x-amz-content-sha256;x-amz-date'

    # canonical request
    canonical_request = \
        method + "\n" +  \
        canonical_uri + '\n' +  \
        canonical_querystring + '\n' + \
        canonical_headers + '\n' +  \
        signed_headers + '\n' +  \
        payload_hash

    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = \
        datestamp + \
        '/' + \
        region + \
        '/' + \
        service + \
        '/' + \
        'aws4_request'

    # string to sign
    string_to_sign = \
        algorithm + '\n' + \
        amzdate + '\n' + \
        credential_scope + '\n' + \
        hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()

    signing_key = get_signature(secret_key, datestamp, region, service)

    # sign string with signing key
    signature = hmac.new(signing_key, string_to_sign.encode(
        'utf-8'), hashlib.sha256).hexdigest()

    # build authorisaton header
    authorization_header = \
        algorithm + ' ' + 'Credential=' + \
        access_key + '/' + \
        credential_scope + ', ' + 'SignedHeaders=' + \
        signed_headers + ', ' + 'Signature=' + signature

    # build standard headers
    headers = {'Host': host,
               'X-Amz-Content-SHA256': payload_hash,
               'X-Amz-Date': amzdate,
               'Authorization': authorization_header}

    # build request
    request_url = endpoint + '?' + canonical_querystring

    # send request and print response
    print('Request URL = ' + request_url)
    print(headers)
    r = requests.get(request_url, headers=headers)

    print('\nResponse')
    print('Response code: %d\n' % r.status_code)
    print(r.text)

    # parse and print XML response
    print("\n")
    tree = ET.fromstring(r.text)
    print_xml_tree(tree)
    print("\n")
