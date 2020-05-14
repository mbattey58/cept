#!/usr/bin/env python3
import sys
import boto3
import json


def print_dict(d):
    for (k, v) in d.items():
        print(f"{k}: {v}")

#1) Connect
#2) Retrieve object reference
#3) Extract data
if __name__ == "__main__":
    with open("config/s3-credentials-local.json", "r") as f:
        credentials = json.loads(f.read())
    endpoint = credentials['endpoint']
    access_key = credentials['access_key']
    secret_key = credentials['secret_key']
    try:
        s3_client = boto3.client('s3',
                                 endpoint_url=endpoint,
                                 aws_access_key_id=access_key,
                                 aws_secret_access_key=secret_key)
        bucket_name = "uv-bucket-1"
        key_name = "ceph-file1"
        byte_range="bytes=10-100"
        response = s3_client.get_object(Bucket=bucket_name,
                                        Key=key_name,
                                        Range=byte_range)
        print("="*10)
        print(f"Response size (bytes): {sys.getsizeof(response)}")
        print("Response")
        print_dict(response)
        print("-"*10)
        print(f"{byte_range}\n")
        bytes = response["Body"].read()
        print(bytes)
        print("="*10)
    except Exception as e:
        print(f"{e}", file=sys.stderr)

    # {'ResponseMetadata': {'RequestId': 'tx00000000000000000081e-005eb0c5c4-758b6a81-objectstorage', 'HostId': '', 'HTTPStatusCode': 200, 'HTTPHeaders': {'content-length': '16384', 'content-range': 'bytes 0-16383/16384', 'accept-ranges': 'bytes', 'last-modified': 'Mon, 04 May 2020 16:58:04 GMT', 'x-rgw-object-type': 'Normal', 'etag': '"ce338fe6899778aacfc28414f2d9498b"', 'x-amz-meta-comment': "changed from 'comment'", 'x-amz-meta-title': 'test file', 'x-amz-request-id': 'tx00000000000000000081e-005eb0c5c4-758b6a81-objectstorage', 'content-type': 'binary/octet-stream', 'date': 'Tue, 05 May 2020 01:47:48 GMT'}, 'RetryAttempts': 0}, 'AcceptRanges': 'bytes', 'LastModified': datetime.datetime(2020, 5, 4, 16, 58, 4, tzinfo=tzutc()), 'ContentLength': 16384, 'ETag': '"ce338fe6899778aacfc28414f2d9498b"', 'ContentRange': 'bytes 0-16383/16384', 'ContentType': 'binary/octet-stream', 'Metadata': {'comment': "changed from 'comment'", 'title': 'test file'}, 'Body': <botocore.response.StreamingBody object at 0x7fc6678d5910>}
