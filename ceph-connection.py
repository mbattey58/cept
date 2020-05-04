#https://stackoverflow.com/questions/39596987/how-to-update-metadata-of-an-existing-object-in-aws-s3-using-python-boto3
#https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Object.wait_until_exists
#https://github.com/ceph/ceph/tree/master/examples/boto3
import boto3
import inspect
import json


def print_dict(d):
    for (k, v) in d.items():
        print(f"{k}: {v}")


def print_obj(obj):
    print("="*10)
    print(f"type: {type(obj)}")
    print_dict(inspect.getmembers(obj))
    print("="*10)



if __name__ == "__main__":

    with open("s3-credentials.json", "r") as f:
        credentials = json.loads(f.read())
    endpoint = credentials['endpoint']
    access_key = credentials['access_key']
    secret_key = credentials['secret_key']
    client = boto3.client('s3',
                          endpoint_url= endpoint,
                          aws_access_key_id=access_key,
                          aws_secret_access_key=secret_key
                          )
    response = client.list_buckets()
    for b in response['Buckets']:
        print_dict(b)
        objs = client.list_objects_v2(Bucket=b["Name"])
        print_dict(objs)

    s3 = boto3.resource('s3',
                        endpoint_url=endpoint,
                        aws_access_key_id=access_key,
                        aws_secret_access_key=secret_key
                        )
    obj = s3.Object("uv-bucket-1", "ceph-file1")
    print("Metadata")
    print_dict(obj.metadata)
    obj.metadata.update({"comment": "changed from 'comment'"})
    obj.copy_from(CopySource={'Bucket': 'uv-bucket-1', 'Key': 'ceph-file1'},
                  Metadata=obj.metadata, MetadataDirective='REPLACE')

    print("s3 waiters:")
    print(client.waiter_names)
    n = s3.BucketNotification("uv-bucket-1")
    print(dir(n))
    print(n)
    # response = n.put(
    #     NotificationConfiguration={'LambdaFunctionConfigurations': [
    #         {
    #             'TopicArn': 'arn:http://123.12',#aws:lambda:us-east-1:033333333:function:mylambda:staging',
    #             'Events': [
    #                 's3:ObjectCreated:*'
    #             ],

    #         },
    #     ]})

 