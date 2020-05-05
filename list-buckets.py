#!/usr/bin/env python3
import sys
import boto3
import json


def print_dict(d):
    for (k, v) in d.items():
        print(f"{k}: {v}")


# 1) Read credential from file
# 2) Create client connection
# 3) Retrieve and print received response and bucket information
if __name__ == "__main__":
    with open("s3-credentials.json", "r") as f:
        credentials = json.loads(f.read())
    endpoint = credentials['endpoint']
    access_key = credentials['access_key']
    secret_key = credentials['secret_key']
    try:
        s3_client = boto3.client('s3',
                                 endpoint_url=endpoint,
                                 aws_access_key_id=access_key,
                                 aws_secret_access_key=secret_key
                                 )
        response = s3_client.list_buckets()
        for b in response['Buckets']:
            print("="*10)
            print("RESPONSE")
            print_dict(b)
            print("-"*10)
            print("BUCKET")
            objs = s3_client.list_objects_v2(Bucket=b["Name"])
            print_dict(objs)
            print("-"*10)

    except Exception as e:
        print(f"{e}", file=sys.stderr)
