# Ceph client connection examples

`s3v4_rest.py` is a module implementing a generic interface to S3, taking care of building the signed request header and generating the REST URLs, MIT licensed.

Authentication and endpoint information is read from json files with the following format:

```json
{
    "version"    : "2",
    "access_key": "FFFFFFF",
    "secret_key": "FFFFFFF",
    "protocol"  : "https",
    "host"      : "aaa.bbb.com",
    "port"      : 8888
}
```

[Ceph S3 requests](https://access.redhat.com/documentation/en-us/red_hat_ceph_storage/3/html/developer_guide/ceph-object-gateway-s3-api#s3-api-put-bucket-lifecycle)

[AWS S3 Requests](https://docs.aws.amazon.com/AmazonS3/latest/API/API_Operations.html)
