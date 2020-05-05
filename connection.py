#!/usr/bin/env python3
import sys
import boto3
import json

#1) Read credential from file
#2) Create client connection OR
#3) Create resource proxy
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
        s3_resource = boto3.resource('s3',
                        endpoint_url=endpoint,
                        aws_access_key_id=access_key,
                        aws_secret_access_key=secret_key)
        print("OK")

    except Exception as e:
        print(f"{e}", file=sys.stderr)