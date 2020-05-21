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

# look at returned x-amz-version-id, launching the same copy multiple times
# 1st PUT
#{'Content-Length': '0', 'ETag': '"d07f12f02a2c5e983dc11c226a857ea8"', 'Accept-Ranges': 'bytes', 'x-amz-version-id': 'xTSL2YelG28ZiawKH8CbcjRQeKvuev9', 'x-amz-request-id': 'tx00000000000000038bf5f-005eb810d7-75cdbf74-objectstorage', 'Date': 'Sun, 10 May 2020 14:34:04 GMT', 'Connection': 'Keep-Alive'}
# 2nd PUT
#{'Content-Length': '0', 'ETag': '"36cf6e1715ca311ec7d7b55128f72098"', 'Accept-Ranges': 'bytes', 'x-amz-version-id': 'MQEzBgAr-umlgLWlzHUO.m8CjbJZcEc', 'x-amz-request-id': 'tx000000000000000283082-005eb810ec-75d0484b-objectstorage', 'Date': 'Sun, 10 May 2020 14:34:25 GMT', 'Connection': 'Keep-Alive'}