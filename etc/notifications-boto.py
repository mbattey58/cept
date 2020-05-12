#!/usr/bin/env python

import argparse
import sys
import boto3
import json


nc = {
    'TopicConfigurations': [
        {
            'Id': 'ID',
            'TopicArn': 'arn:aws:sns:us-east-2:444455556666:MyTopic',
            'Events': [
                's3:ObjectCreated:*',
            ]
        }
    ]
}


def main(bucket):
    data = {}
    # if topics:
    #     data['TopicConfigurations'] = [
    #         {
    #             'TopicArn': topic,
    #             'Events': events
    #         }
    #         for topic in topics if topic
    #     ]

    with open("config/s3-credentials.json", "r") as f:
        credentials = json.loads(f.read())
    endpoint = credentials['endpoint']
    access_key = credentials['access_key']
    secret_key = credentials['secret_key']
    bucket = "uv-bucket-3"
    try:
        s3_client = boto3.client('s3',
                                 endpoint_url=endpoint,
                                 aws_access_key_id=access_key,
                                 aws_secret_access_key=secret_key)

        response = s3_client.put_bucket_notification_configuration(
            Bucket=bucket,
            NotificationConfiguration=nc)
        print(response)

        if data:
            print(data)
            s3 = boto3.resource('s3')
            bucket_notification = s3.BucketNotification(bucket)
            response = bucket_notification.put(NotificationConfiguration=data)
            print('Bucket notification updated successfully')
        else:
            print('No bucket notifications were specified')
            sys.exit(1)
    except Exception as e:
        print(e)


if __name__ == '__main__':
    main("uv-bucket-3")