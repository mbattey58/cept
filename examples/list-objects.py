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
