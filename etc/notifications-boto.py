#!/usr/bin/env python

import argparse
import sys

try:
    import boto3
except ImportError:
    print('Please install boto3 to use this tool')
    sys.exit(1)


def main(bucket, topics, queues, lambdas, events):
    data = {}
    if topics:
        data['TopicConfigurations'] = [
            {
                'TopicArn': topic,
                'Events': events
            }
            for topic in topics if topic
        ]

    if queues:
        data['QueueConfigurations'] = [
            {
                'QueueArn': queue,
                'Events': events
            }
            for queue in queues if queue
        ]

    if lambdas:
        data['LambdaFunctionConfigurations'] = [
            {
                'LambdaFunctionArn': _lambda,
                'Events': events
            }
            for _lambda in lambdas if _lambda
        ]

    if data:
        print(data)
        s3 = boto3.resource('s3')
        bucket_notification = s3.BucketNotification(bucket)
        response = bucket_notification.put(NotificationConfiguration=data)
        print('Bucket notification updated successfully')
    else:
        print('No bucket notifications were specified')
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Manage S3 bucket notifications')
    parser.add_argument('--bucket', dest='bucket', required=True,
                        help='the S3 bucket name')
    parser.add_argument('--topic', dest='topics', nargs='*',
                        help='SNS topic ARN')
    parser.add_argument('--queue', dest='queues', nargs='*',
                        help='SQS queue ARN')
    parser.add_argument('--lambda', dest='lambdas', nargs='*',
                        help='Lambda ARN')
    parser.add_argument('--event', dest='events', nargs='*',
                        help='an event to respond to')
    args = parser.parse_args()

    main(args.bucket, args.topics, args.queues, args.lambdas, args.events)