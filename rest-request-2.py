#!/usr/bin/env python3
import s3v4_rest as s3
import requests
import json

#ListBucket (empty GET request)

if __name__ == "__main__":
    # read configuration information
    with open("s3-credentials2.json", "r") as f:
        credentials = json.loads(f.read())

    # payload, empty in this case
    payload_hash = s3.hash('')

    # build request
    request_url, headers = s3.build_request_url(credentials,
                                                'GET',
                                                None,
                                                payload_hash)

    # send request and print response
    print('Request URL = ' + request_url)
    print(headers)
    r = requests.get(request_url, headers=headers)

    print('\nResponse')
    print('Response code: %d\n' % r.status_code)
    print(r.text)

    # parse and print XML response
    print("\n")
    s3.print_xml_response(r.text)
    print("\n")
