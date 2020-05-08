#!/usr/bin/env python3
import s3v4_rest as s3
import requests
import json


# Notification request
# POST
# # Action=CreateTopic
# &Name=<topic-name>
# [&Attributes.entry.1.key=amqp-exchange&Attributes.entry.1.value=<exchange>]
# [&Attributes.entry.2.key=amqp-ack-level&Attributes.entry.2.value=none|broker|routable]
# [&Attributes.entry.3.key=verify-ssl&Attributes.entry.3.value=true|false]
# [&Attributes.entry.4.key=kafka-ack-level&Attributes.entry.4.value=none|broker]
# [&Attributes.entry.5.key=use-ssl&Attributes.entry.5.value=true|false]
# [&Attributes.entry.6.key=ca-location&Attributes.entry.6.value=<file path>]
# [&Attributes.entry.7.key=OpaqueData&Attributes.entry.7.value=<opaque data>]
# [&Attributes.entry.8.key=push-endpoint&Attributes.entry.8.value=<endpoint>]


if __name__ == "__main__":
    # read configuration information
    with open("config/s3-credentials2.json", "r") as f:
        credentials = json.loads(f.read())
    
    push_endpoint = "http://146.118.66.215:80"

    parameters = {"Action": "CreateTopic",
                  "Name": "storage",
                  "push_endpoint": "kafka://mycluster.kafka:9099",
                  "kafka-ack-level": "broker"}

    payload = s3.encode_url(parameters)

    bucket_name = "uv-bucket-3"

    # build request
    # NOTE: requests will send an application/x-www-form-urlencoded
    #       request automatically when data=Dict[str, str]
    #       POST urlencoded data is the urlencoded url which is sent as
    #       payload
    request_url, headers = s3.build_request_url(
        config=credentials,
        req_method="POST",
        parameters=None,
        payload_hash=s3.hash(payload), #s3.UNSIGNED_PAYLOAD,
        payload_length=len(payload),  # will be added by requests.post
        uri_path=f"/{bucket_name}",
        additional_headers={"Content-Type":
                            "application/x-www-form-urlencoded"})

    # send request and print response
    print("Request URL = " + request_url)
    print(headers)
    print(payload)
    r = requests.post(request_url, data=parameters, headers=headers)

    print("\nResponse")
    print("Response code: %d\n" % r.status_code)
    if r.text:
        print(r.text)
        # parse and print XML response
        print("\n")
        s3.print_xml(r.text)
        print("\n")
