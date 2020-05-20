#!/usr/bin/env python3
"""Send REST request specified on the command line to S3 services, like
   curl + S3v4 signing

   __author__     = "Ugo Varetto"
   __credits__    = ["Ugo Varetto", "Luca Cervigni"]
   __license__    = "MIT"
   __version__    = "0.5"
   __maintainer__ = "Ugo Varetto"
   __email__      = "ugovaretto@gmail.com"
   __status__     = "Development"

    run with --help to see all options

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

    Main command line switches (run with --help for full list).

    -c <json config file>
    -m [head | get | put | post | delete] request method
    -b [bucket name]
    -k [key name] Only valid if -b present
    -p [payload] Payload as text on the command line or filename if -f present
    -f [] interpret payload as file name
    -n [filename] dump content to file
    -t ["key1=value1;key2=value2..."] URI request parameters
    -e ["Header-1:Value1;Header-2;Value2..."] Headers
    -l [ERROR | WARN | INFO | DEBUG | RAW | MUTE] log level:
        ERROR | WARN | INFO | DEBUG --> passed to loggin module
        RAW: simply print STATUS CODE, HEADERS and CONTENT to STDOUT

    response content and headers can be searched:
        headers:
            -H / --search-header= "<header key1>:<value1>;<header key 2>:..."
        xml content through XPath query:
            -X / --search-xml=".//aws:TAGNAME"
            "aws:" indentifies the AWS XML namespace and shall always be
            specified when searching for standard reponse tags such as
            '<UploadId>'
"""
import s3v4_rest as s3
import requests
import sys
import argparse
import time
import json
import logging
import xml.dom.minidom  # better than ET for pretty printing
import xml.etree.ElementTree as ET


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Send REST request to S3 service')
    parser.add_argument('-b', '--bucket', dest='bucket', type=str,
                        required=False,
                        help='the S3 bucket name')
    parser.add_argument('-k', '--key', dest='key', type=str, required=False,
                        help='key name')
    parser.add_argument('-m', '--method', dest='method', type=str,
                        required=False, default='get',
                        help='method: get, put, post', action='store')
    parser.add_argument('-c', '--config_file', dest='config_file',
                        required=True,
                        help='json configuration file', type=str)
    parser.add_argument('-p', '--payload', dest='payload', required=False,
                        help='request body', type=str)
    parser.add_argument('-f',
                        '--payload_is_file', dest='payload_is_file',
                        required=False, type=bool, const=True,
                        help='if true "payload" is interpreted as a file name',
                        nargs='?', default=False)
    parser.add_argument('-s',
                        '--sign_payload', dest='sign_payload', required=False,
                        help='if true "payload" is interpreted as a file name',
                        nargs='?', type=bool, default=False, const=True)
    parser.add_argument('-t', '--parameters', dest='parameters',
                        required=False, type=str,
                        help="';' separated list of key=value pairs")
    parser.add_argument('-e', '--headers', dest='headers', required=False,
                        type=str,
                        help="';' separated list of key=value pairs")
    parser.add_argument('-n', "--save_content_to_file", dest="content_file",
                        required=False, help="save response content to file")
    parser.add_argument('-x', "--substitute_parameters", type=str,
                        dest="subst_params",
                        help="';' separated list of key=value pairs, " +
                             "substitutes key with value in request body",
                        required=False)
    parser.add_argument('-o', '--output', type=str, dest='output_type',
                        help="content output type: xml | text | binary",
                        default="xml", required=False)
    parser.add_argument('-O', '--override-configuration', type=str,
                        dest="override_config",
                        help="replaces configuration parameters, " +
                             "key=value ';' separated list",
                        required=False)
    parser.add_argument('-P', '--proxy-endpoint', type=str, dest="proxy",
                        help='send request to proxy instead, but sign ' +
                             'header using actual endpoint', required=False)
    parser.add_argument('-X', '--xml-query', type=str,
                        dest='xml_query',
                        help='search tag value in xml response with XPath ' +
                             'expressions, e.g: ".//aws:UploadId" ' +
                             '"aws" represents the aws namespace and must ' +
                             'always be added', required=False)
    parser.add_argument('-H', '--search-headers-keys', type=str,
                        dest='header_keys',
                        help="search header key in response header",
                        required=False)
    parser.add_argument('-l', '--log-level', type=str, required=False,
                        help='log level passed to log module: ERROR | WARN ' +
                             '| INFO | DEBUG | RAW or MUTE for no output',
                             default="INFO",
                             dest="log_level")

    args = parser.parse_args()

    if args.log_level.upper() != "RAW":
        if args.log_level.upper() == "MUTE":
            logging.getLogger().propagate = False
        else:
            logging.basicConfig(level=args.log_level)
            print()

    params = None
    if args.parameters:
        params = dict([x.split("=", 1) for x in args.parameters.split(";")])

    headers = None
    if args.headers:
        headers = dict([x.split(":", 1) for x in args.headers.split(";")])

    # if parameter substitution is required and payload is file name
    # then payload must be read from file, substitutions applied and
    # payload_is_file set to False, since substituted content needs to
    # be passed instead
    payload_is_file = args.payload_is_file
    payload = args.payload
    if args.payload and args.payload_is_file and args.subst_params:
        with open(args.payload) as f:
            payload = f.read()
            payload = payload.replace("\n", "")
            subst_dict = dict([x.split("=")
                               for x in args.subst_params.split(";")])
            for (k, v) in subst_dict.items():
                payload = payload.replace(k, v)
        payload_is_file = False

    config = None
    with open(args.config_file, 'r') as j:
        config = json.loads(j.read())

    if args.override_config:
        oc = dict([x.split("=", 2) for x in args.override_config.split(";")])
        config.update(oc)

    response = s3.send_s3_request(
                           config=config,
                           req_method=args.method,
                           parameters=params,
                           payload=payload,
                           sign_payload=args.sign_payload,
                           payload_is_file_name=payload_is_file,
                           bucket_name=args.bucket,
                           key_name=args.key,
                           additional_headers=headers,
                           content_file=args.content_file,
                           proxy_endpoint=args.proxy)

    if args.log_level.upper() == "RAW":
        print("STATUS CODE: " + str(response.status_code) + "\n")
        print("HEADERS:\n")
        print(response.headers)
        if response.content:
            msg = "RESPONSE CONTENT\n" + 20 * "=" + '\n'
            if "Content-Type" in response.headers.keys():
                if (response.headers["Content-type"] == "application/json" or
                        response.headers["Content-type"] == "text/plain"):
                    msg += response.content.decode('utf-8')
                elif (response.headers["Content-type"] == "text/html" or
                        response.headers["Content-type"] == "application/xml"):
                    dom = xml.dom.minidom.parseString(
                            response.content.decode('utf-8'))
                    pretty = dom.toprettyxml(indent="   ")
                    msg += pretty
            else:
                msg += response.content[:1024].decode('utf-8')
            print(msg)

    if args.xml_query and response.text:
        ns = {"aws": "http://s3.amazonaws.com/doc/2006-03-01/"}
        root = ET.fromstring(response.content)
        n = root.findall(args.xml_query, ns)
        for i in n:
            print(i.text)

    if args.header_keys and response.headers:
        keys = args.header_keys.split(",") if "," in args.header_keys \
                                           else args.header_keys
        if keys and type(keys) == str and keys in response.headers.keys():
            print(f"{keys}: {response.headers[keys]}")
        else:
            for k in keys:
                if k in response.headers.keys():
                    print(f"{k}: {response.headers[k]}")
