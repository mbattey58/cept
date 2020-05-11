#!/usr/bin/env python3
import s3v4_rest as s3
import requests
import json
# mdsearch
if __name__ == "__main__":
    # read configuration information - OBJECT
    with open("config/magenta-object.json", "r") as f:
        credentials = json.loads(f.read())
    # payload, empty in this case
    payload_hash = s3.hash('')
    bucket_name = "test2"
    # https://documentation.suse.com/ses/6/html/ses-all/cha-ceph-gw.html
    # enable indexing
    search_header = {'x-amz-meta-search': "x-amz-meta-key1;string"}
    # build request
    request_url, headers = s3.build_request_url(
        config=credentials,
        req_method='GET',
        parameters={'mdsearch': ''},
        payload_hash=s3.UNSIGNED_PAYLOAD,
        payload_length=0,
        uri_path=f"/{bucket_name}",
        additional_headers=search_header
    )
    # read configuration information - METADATA
    with open("config/magenta-metadata.json", "r") as f:
        credentials = json.loads(f.read())
    # send request and print response
    print('Request URL = ' + request_url)
    print(headers)
    r = requests.get(request_url, headers=headers)
    print('\nResponse')
    print('Response code: %d\n' % r.status_code)
    print(r.text)
    # build request
    request_url, headers = s3.build_request_url(
        config=credentials,
        req_method='GET',
        parameters={"query": "name==file-020"},
        payload_hash=s3.UNSIGNED_PAYLOAD,
        payload_length=0,
        uri_path=f"/{bucket_name}"
    )
    # send request and print response
    print('Request URL = ' + request_url)
    print(headers)
    r = requests.get(request_url, headers=headers)
    print('\nResponse')
    print('Response code: %d\n' % r.status_code)
    print(r.text)
    # parse and print XML response
    print("\n")
    s3.print_xml(r.text)
    print("\n")