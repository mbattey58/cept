#!/usr/bin/env python3
import sys
import boto3
import json
import random
import string


def print_dict(d):
    for (k, v) in d.items():
        print(f"{k}: {v}")


def random_text(length=20):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(length))

# 1) Read credential from file
# 2) Resource throuh Object request
# 3) Retrieve and print metadata
# 4) Update metadata
# 5) Print updated metadata
if __name__ == "__main__":
    
    with open("s3-credentials.json", "r") as f:
        credentials = json.loads(f.read())
    endpoint = credentials['endpoint']
    access_key = credentials['access_key']
    secret_key = credentials['secret_key']
    try:
        s3 = boto3.resource('s3',
                        endpoint_url=endpoint,
                        aws_access_key_id=access_key,
                        aws_secret_access_key=secret_key
                        )
        bucket_name = "uv-bucket-1"
        key_name = "ceph-file1"
        obj = s3.Object(bucket_name, key_name)
        metadata = random_text()
        if len(sys.argv) > 1:
            metadata = argv[1]
        print("Old metadata")
        print_dict(obj.metadata)
        print("updating metadata...")
        obj.metadata.update({"comment": metadata})
        obj.copy_from(CopySource={'Bucket': 'uv-bucket-1', 'Key': 'ceph-file1'},
                    Metadata=obj.metadata, MetadataDirective='REPLACE')
        print("New metadata")
        print_dict(obj.metadata)

    except Exception as e:
        print(f"{e}", file=sys.stderr)
