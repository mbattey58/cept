#!/usr/bin/env python3
import s3v4_rest as s3
import requests
import sys

# ListBucket (empty GET request)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <json configuration file>",
              file=sys.stderr)
        sys.exit(-1)
    config_file = sys.argv[1]

    # payload, empty in this case
    payload_hash = s3.hash('')

    # build request
    request_url, headers = s3.build_request_url(
        config=config_file,
        req_method='GET',
        parameters=None,
        payload_hash=payload_hash)

    # send request and print response
    print('Request URL = ' + request_url)
    print(headers)
    r = requests.get(request_url, headers=headers)

    print('\nResponse')
    print('Response code: %d\n' % r.status_code)
    print(r.text)

    # parse and print XML response
    print("\n")
    print(s3.xml_to_text(r.text))
    print("\n")
