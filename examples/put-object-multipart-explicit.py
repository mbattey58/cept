#!/usr/bin/env python3
"""Simple multipart data upload through S3 using raw REST requests

   __author__ = "Ugo Varetto"

   Send multipart upload requests reading data from files or memory.

    1. read credentials (keys and endpoint information)
    2. initiate transfer through multipart POST request and record
       returned UploadId, this is the transaction idenfier
    3. send each chunck with PUT requests, recording part # and ETag id
       returned by server
    4. finish transfer by sending a final POST request containing:
       * UploadId identifying upload transaction
       * list of (part number, ETag) entried of uploaded files

    Payload signing/hashing is not applied to individual payloads, probably
    better to compute MD5/hashing on data externally at data creationd time
    and submit checksum/hash as metadata.

    Ceph supports parallel upload of multipart data, which in this case is
    files, but does not have to be, multiplart can be used to store e.g.
    streaming data (in this case signing/hashing has to be handled
    differently).

    generate 'tmp-blob' file with:
        d if=/dev/zero of=tmp-blob bs=1024 count=$((1024*8))
    split file with:
        split -n 4 -a 1 --numeric-suffixes=1 tmp-blob tmp-blob

    WARNING: depending on the server-side configuration you might end up
    getting an "EntityTooSmall" error if the chunk size is e.g. smaller than
    a specific size (have seen 5 MB on some platforms).
    """

import s3v4_rest as s3
import requests
import json
import os
from array import array


def bytes_from_file(fname):
    """Use this function to read bytes from files when using 'data' instead of
       'files' in requests.* functions
    """
    data = array('B')

    with open(fname, 'rb') as f:
        data.fromfile(f, os.stat(fname).st_size)

    return data.tobytes()


if __name__ == "__main__":
    # read configuration information
    with open("config/s3-credentials2.json", "r") as f:
        credentials = json.loads(f.read())

    bucket_name = "uv-bucket-3"
    key_name = "key-multipart-test10"

    # request #1 initiate multipart upload

    # 1 BEGIN UPLOAD: send post request, get back request id
    # identifying transaction
    request_url, headers = s3.build_request_url(
        config=credentials,
        req_method="POST",
        parameters={"uploads": ''},
        payload_hash=s3.UNSIGNED_PAYLOAD,
        payload_length=0,
        uri_path=f"/{bucket_name}/{key_name}",
    )

    print("Sending begin upload request...")
    r = requests.post(request_url, '', headers=headers)
    print(f"Status code: {r.status_code}")
    if r.status_code != 200:
        print(r.text)
        print(r.headers)
    request_id = s3.get_upload_id(r.text)
    print(f"UploadId: {request_id}")
    print("Sending multi-part requests...")
    # 2 SEND PARTS:
    fname = "tmp-blob"  # prefix
    parts = []
    number_of_chunks = 2  # == number of files
    for part in range(1, number_of_chunks + 1):
        partname = fname + str(part)
        
        payload_size = os.stat(partname).st_size
        request_url, headers = s3.build_request_url(
            config=credentials,
            req_method="PUT",
            parameters={"partNumber": str(part), "uploadId": request_id},
            payload_hash=s3.UNSIGNED_PAYLOAD,
            payload_length=payload_size,
            uri_path=f"/{bucket_name}/{key_name}",
        )

        print(f"Sending part {part} of {number_of_chunks}")
        files = {'file': (partname, open(partname, 'rb'))}
        r = requests.put(request_url,
                         files=files,
                         headers=headers)
        print(f"status: {r.status_code}")
        if r.status_code != 200:
            print(r.text)
            print(r.headers)

        tag_id = s3.get_tag_id(r.headers)
        print(tag_id)
        parts.append((part, tag_id))

    # 3 END TRANSACTION
    # compose XML request with part list
    multipart_list = s3.build_multipart_list(parts)

    request_url, headers = s3.build_request_url(
        config=credentials,
        req_method="POST",
        parameters={"uploadId": request_id},
        payload_hash=s3.UNSIGNED_PAYLOAD,
        payload_length=len(multipart_list),
        uri_path=f"/{bucket_name}/{key_name}",
    )

    print("Sending end upload request...")
    r = requests.post(request_url,
                      data=multipart_list,
                      headers=headers)

    print(f"status: {r.status_code}")
    if r.status_code != 200:
        print(r.text)
        print(r.headers)
