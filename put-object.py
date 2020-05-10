#!/usr/bin/env python3
import s3v4_rest as s3
import requests
import json

# PutObject PUT /bucket/key + data in body and multipart upload
# generate 'tmp-blob' file with
# dd if=/dev/zero of=tmp-blob bs=1024 count=$((1024*8))

if __name__ == "__main__":
    # read configuration information
    with open("config/s3-credentials2.json", "r") as f:
        credentials = json.loads(f.read())

    bucket_name = "uv-bucket-1"
    key_name = "key-3"
    payload = "key-3 payload"

    # payload, empty in this case
    payload_hash = s3.hash(payload)

    # build request #1: text in body and payload hashing
    request_url, headers = s3.build_request_url(
        config=credentials,
        req_method="PUT",
        parameters=None,
        payload_hash=payload_hash,
        payload_length=len(payload),
        uri_path=f"/{bucket_name}/{key_name}",
    )

    # send request and print response
    print("Request URL = " + request_url)
    print(headers)
    r = requests.put(request_url, payload, headers=headers)

    print("\nResponse")
    print("Response code: %d\n" % r.status_code)
    if r.text:
        print(r.text)
        # parse and print XML response
        print("\n")
        print(s3.xml_to_text(r.text))
        print("\n")

    # build request #2: binary file read from filesytem, no hashing
    request_url, headers = s3.build_request_url(
        config=credentials,
        req_method="PUT",
        parameters=None,
        payload_hash=s3.UNSIGNED_PAYLOAD,
        payload_length=len(payload),
        uri_path=f"/{bucket_name}/{key_name}",
    )

    # send request and print response
    print("Request URL = " + request_url)
    print(headers)
    r = requests.put(request_url, data=open("tmp-blob", "rb"), headers=headers)

    print("\nResponse")
    print("Response code: %d\n" % r.status_code)
    if r.text:
        print(r.text)
        # parse and print XML response
        print("\n")
        print(s3.xml_to_text(r.text))
        print("\n")

    print(r.headers)
