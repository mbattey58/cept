#!/usr/bin/env python3
import s3v4_rest as s3
import requests
import sys

# Enable Versioning on bucket
# Retrieve versioning information

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <json configuration file> <bucket name>",
              file=sys.stderr)
        sys.exit(-1)
    config_file = sys.argv[1]
    bucket_name = sys.argv[2]

    # enable versioning
    request_body = \
        """<?xml version="1.0" encoding="UTF-8"?>
           <VersioningConfiguration xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
             <MfaDelete>Disabled</MfaDelete>
             <Status>Enabled</Status>
           </VersioningConfiguration>
        """
    r = s3.send_s3_request(config=config_file,
                           req_method='PUT',
                           parameters={'versioning': ''},
                           payload=request_body,
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

    # retrieve versioning configuration
    r = s3.send_s3_request(config=config_file,
                           req_method='GET',
                           parameters={'versioning': ''},
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
