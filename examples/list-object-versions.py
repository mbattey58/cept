#!/usr/bin/env python3
import s3v4_rest as s3
import requests
import sys

# ListObjectVersions GET/bucket_name?versions request)

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
                           parameters={"versions": ''},
                           sign_payload=False,
                           payload_is_file_name=False,
                           bucket_name=bucket_name,
                           key_name=None,
                           action=None)
    print('\nResponse')
    print(f'Response code: {r.status_code}\n')
    print(r.text)

    # parse and print XML response
    print("\n")
    print(s3.xml_to_text(r.text))
    print("\n")
