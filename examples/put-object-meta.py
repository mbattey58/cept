#!/usr/bin/env python3
import s3v4_rest as s3
import requests
import sys

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(f"usage: {sys.argv[0]} <json configuration file>" +
              " <bucket name> <file name> <key name>",
              file=sys.stderr)
        sys.exit(-1)
    config_file = sys.argv[1]
    bucket_name = sys.argv[2]
    filename = sys.argv[3]
    key_name = sys.argv[4]
    r = s3.send_s3_request(config=config_file,
                           req_method='PUT',
                           parameters=None,
                           payload=filename,
                           sign_payload=False,
                           payload_is_file_name=True,
                           bucket_name=bucket_name,
                           key_name=key_name,
                           action=None)
    print(f"Response code: {r.status_code}\n")
    if r.text:
        print(r.text)
        # parse and print XML response
        print("\n")
        print(s3.xml_to_text(r.text))
        print("\n")

    print(r.headers)
