#!/usr/bin/env python3

# Pure REST request to S3/Ceph backend
# List buckets
# Code modified from the AWS EC2 API reference documentation
# Author: Ugo Varetto

from urllib.parse import urlencode
import hashlib
import datetime
import hmac
import xml.etree.ElementTree as ET
from typing import Dict, Tuple

# standard signing functions from AWS
def _sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def _get_signature(key, date_stamp, region_same, service_name):
    date_k = _sign(('AWS4' + key).encode('utf-8'), date_stamp)
    region_k = _sign(date_k, region_same)
    service_k = _sign(region_k, service_name)
    signing_key = _sign(service_k, 'aws4_request')
    return signing_key

# ElementTree prefixes tags with a namespace if present
def _clean_xml_tag(tag):
    closing_brace_index = tag.index('}')
    return tag if not closing_brace_index else tag[closing_brace_index+1:]


#note: Python as a limit on the recursion level it can handle,
#      this is just implemented like this without returning functions
#      or using stacks to keep the code simple
def _print_xml_tree(node, indentation_level=0, filter=lambda t: True):
    BLANKS = 2
    indent = indentation_level * BLANKS
    if filter(node.tag):
        print(" "*indent + f"{_clean_xml_tag(node.tag)}: {node.text}")
    for child in node:
        _print_xml_tree(child, indentation_level + 1)

def print_xml_response(text: str):
    tree = ET.fromstring(text)
    _print_xml_tree(tree)

# Type declarations
S3Config = Dict[str, str]
RequestMethod = str
RequestParameters = Dict[str, str]
Headers = Dict[str, str]
URL = str
Request = Tuple[URL, Headers]
# return tuple(request url, headers)
def build_request_url(config: S3Config, 
                      req_method: RequestMethod,
                      parameters: RequestParameters,
                      payload_hash: str):
    
    protocol   = config['protocol']
    host       = config['host']
    port       = config['port']
    access_key = config['access_key']
    secret_key = config['secret_key']

    method = req_method
    service = 's3'
    region = 'us-east-1' #works with Ceph, any region might work actually
    endpoint = protocol + '://' + host + (f":{port}" if port else '')

    request_parameters = urlencode(parameters)

     # canonical URI
    canonical_uri = '/'
    canonical_querystring = request_parameters

    # dates for headers credential string
    dt = datetime.datetime.utcnow()
    amzdate = dt.strftime('%Y%m%dT%H%M%SZ')
    datestamp = dt.strftime('%Y%m%d')  # Date w/o time, used in credential scope

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

    signing_key = _get_signature(secret_key, datestamp, region, service)

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

    return request_url, headers