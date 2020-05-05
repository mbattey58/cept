#!/usr/bin/env python3
import urllib
import hashlib
import datetime
import base64
import os
import sys
import sys
import os
import base64
import datetime
import hashlib
import hmac
import requests 


method = 'GET'
service = 's3'
host = 'nimbus.pawsey.org.au:8080'
region = 'us-east-1'
endpoint =  'http://localhost:8000'
#endpoint = 'https://nimbus.pawsey.org.au:8080'
#ListBuckets
#GET / HTTP/1.1
request_parameters = ''

def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def getSignatureKey(key, dateStamp, regionName, serviceName):
    kDate = sign(('AWS4' + key).encode('utf-8'), dateStamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, 'aws4_request')
    return kSigning

access_key = "00a5752015a64525bc45c55e88d2f162"
secret_key = "d1b8bdb35b7649deac055c3f77670f7f"

# Create a date for headers and the credential string
t = datetime.datetime.utcnow()
amzdate = t.strftime('%Y%m%dT%H%M%SZ')
datestamp = t.strftime('%Y%m%d')  # Date w/o time, used in credential scope

canonical_uri = '/'
canonical_querystring = request_parameters
payload_hash = hashlib.sha256(('').encode('utf-8')).hexdigest()
canonical_headers = 'host: ' + host + '\n' + "x-amz-content-sha256: " + payload_hash + '\n' + 'x-amz-date: ' + amzdate + '\n'

signed_headers = 'host;x-amz-content-sha256;x-amz-date'

canonical_request = method + "\n" + canonical_uri + '\n' + canonical_querystring + \
    '\n' + canonical_headers + '\n' + signed_headers + '\n'

algorithm = 'AWS4-HMAC-SHA256'
credential_scope = datestamp + '/' + region + \
    '/' + service + '/' + 'aws4_request'
string_to_sign = algorithm + '\n' + host + '\n' + payload_hash + '\n' + amzdate + '\n' + credential_scope + \
    '\n' + hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()   

signing_key = getSignatureKey(secret_key, datestamp, region, service)

# Sign the string_to_sign using the signing_key
signature = hmac.new(signing_key, (string_to_sign).encode(
    'utf-8'), hashlib.sha256).hexdigest()

authorization_header = algorithm + ' ' + 'Credential=' + access_key + '/' + \
    credential_scope + ', ' + 'SignedHeaders=' + \
    signed_headers + ', ' + 'Signature=' + signature

headers = {'Host': host, 'X-Amz-Date': amzdate, 'X-Amz-Content-SHA256': payload_hash,   'Authorization': authorization_header}

# ************* SEND THE REQUEST *************
request_url = endpoint# + '?'# + canonical_querystring
print('Request URL = ' + request_url)
print(headers)
r = requests.get(request_url, headers=headers)

print('\nRESPONSE++++++++++++++++++++++++++++++++++++')
print('Response code: %d\n' % r.status_code)
print(r.text)