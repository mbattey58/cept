#!/usr/bin/env python3
"""Send REST request specified on the command line to S3 services.

   __author__     = "Ugo Varetto"
   __license__    = "MIT"
   __version__    = "0.2"
   __maintainer__ = "Ugo Varetto"
   __email__      = "ugovaretto@gmail.com"
   __status__     = "Development"

    run withouth command line parameters to see help.

    example:

        s3-rest.py --method=get --config_file=config/s3-credentials2.json \
                   --bucket=uv-bucket-3 --parameters="versions=''
        
        will print all the version information associated to a bucket

        s3-rest.py --method=get  --config_file=config/s3-credentials2.json

        lists all the buckets associated to a specific access+secret key

    credentials and endpoint information are read from a json file which
    must include the following information:
    
    {
        ...
        "access_key": "00000000000000000000000000000000",
        "secret_key": "11111111111111111111111111111111",
        "protocol"  : "http",
        "host"      : "localhost",
        "port"      : 8000
        ...
    }

    url parameters can be passed on the command line as ';' separated
    key=value pairs and will be properly urlencoded

    additional headers can be passes as well on the command line as ';'
    separated key=value pairs

    parameters and headers must *always* include key=value pairs, use "key=''"
    for missing values

    reponse status code, headers, textual and parsed xml body is printed
    to either standard output (200 status) or standard error (non 200 status)
"""
import s3v4_rest as s3
import requests
import sys
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Send REST request to S3 service')
    parser.add_argument('--bucket', dest='bucket', type=str, required=False,
                        help='the S3 bucket name')
    parser.add_argument('--key', dest='key', type=str, required=False,
                        help='key name')
    parser.add_argument('--action', dest='action', type=str, required=False,
                        help='action name')
    parser.add_argument('--method', dest='method', type=str, required=True,
                        help='method: get, put, post', action='store')
    parser.add_argument('--config_file', dest='config_file', required=True,
                        help='json configuration file', type=str)
    parser.add_argument('--payload', dest='payload', required=False,
                        help='request body', type=str)
    parser.add_argument(
                    '--payload_is_file', dest='payload_is_file',
                    required=False,
                    help='if true "payload" is interpreted as a file name',
                    nargs='?', type=bool, default=True)
    parser.add_argument(
                    '--sign_payload', dest='sign_payload', required=False,
                    help='if true "payload" is interpreted as a file name',
                    nargs='?', type=bool, default=True)
    parser.add_argument('--parameters', dest='parameters', required=False,
                        type=str,
                        help="';' separated list of key=value pairs")
    parser.add_argument('--headers', dest='headers', required=False,
                        type=str,
                        help="';' separated list of key=value pairs")

    args = parser.parse_args()
    print(args.method)

    params = None
    if args.parameters:
        params = dict([x.split("=") for x in args.parameters.split(";")])
    headers = None
    if args.headers:
        headers = dict([x.split("=") for x in args.headers.split(";")])

    response = s3.send_s3_request(
                           config=args.config_file,
                           req_method=args.method,
                           parameters=params,
                           payload=args.payload,
                           sign_payload=args.sign_payload,
                           payload_is_file_name=args.payload_is_file,
                           bucket_name=args.bucket,
                           key_name=args.key,
                           action=args.action,
                           additional_headers=headers)

    outfile = sys.stdout if response.status_code == 200 else sys.stderr
    print(f"Response status: {response.status_code}", file=outfile)
    print(f"Response headers: {response.headers}", file=outfile)
    if response.text:
        print(f"Response body: {response.text}", file=outfile)
        print(s3.xml_to_text(response.text))
