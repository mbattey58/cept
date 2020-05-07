# REST requests issues

Sometimes when sending a request I get the following error:

```bash
./rest-request.py
Request URL = https://nimbus.pawsey.org.au:8080?
{'Host': 'nimbus.pawsey.org.au', 'X-Amz-Content-SHA256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'X-Amz-Date': '20200506T011545Z', 'Authorization': 'AWS4-HMAC-SHA256 Credential=00a5752015a64525bc45c55e88d2f162/20200506/us-east-1/s3/aws4_request, SignedHeaders=host;x-amz-content-sha256;x-amz-date, Signature=70bc341ea2cfe742e058422455f8e0d88dc3f7f12d51a97dfe9dd11baacf3954'}
Traceback (most recent call last):
  File "/home/ugovaretto/anaconda3/lib/python3.7/site-packages/urllib3/contrib/pyopenssl.py", line 485, in wrap_socket
    cnx.do_handshake()
  File "/home/ugovaretto/anaconda3/lib/python3.7/site-packages/OpenSSL/SSL.py", line 1934, in do_handshake
    self._raise_ssl_error(self._ssl, result)
  File "/home/ugovaretto/anaconda3/lib/python3.7/site-packages/OpenSSL/SSL.py", line 1671, in _raise_ssl_error
    _raise_current_error()
  File "/home/ugovaretto/anaconda3/lib/python3.7/site-packages/OpenSSL/_util.py", line 54, in exception_from_error_queue
    raise exception_type(errors)
OpenSSL.SSL.Error: [('SSL routines', 'ssl3_get_record', 'wrong version number')]

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/ugovaretto/anaconda3/lib/python3.7/site-packages/urllib3/connectionpool.py", line 672, in urlopen
    chunked=chunked,
  File "/home/ugovaretto/anaconda3/lib/python3.7/site-packages/urllib3/connectionpool.py", line 376, in _make_request
    self._validate_conn(conn)
  File "/home/ugovaretto/anaconda3/lib/python3.7/site-packages/urllib3/connectionpool.py", line 994, in _validate_conn
    conn.connect()
  File "/home/ugovaretto/anaconda3/lib/python3.7/site-packages/urllib3/connection.py", line 360, in connect
    ssl_context=context,
  File "/home/ugovaretto/anaconda3/lib/python3.7/site-packages/urllib3/util/ssl_.py", line 370, in ssl_wrap_socket
    return context.wrap_socket(sock, server_hostname=server_hostname)
  File "/home/ugovaretto/anaconda3/lib/python3.7/site-packages/urllib3/contrib/pyopenssl.py", line 491, in wrap_socket
    raise ssl.SSLError("bad handshake: %r" % e)
ssl.SSLError: ("bad handshake: Error([('SSL routines', 'ssl3_get_record', 'wrong version number')])",)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/ugovaretto/anaconda3/lib/python3.7/site-packages/requests/adapters.py", line 449, in send
    timeout=timeout
  File "/home/ugovaretto/anaconda3/lib/python3.7/site-packages/urllib3/connectionpool.py", line 720, in urlopen
    method, url, error=e, _pool=self, _stacktrace=sys.exc_info()[2]
  File "/home/ugovaretto/anaconda3/lib/python3.7/site-packages/urllib3/util/retry.py", line 436, in increment
    raise MaxRetryError(_pool, url, error or ResponseError(cause))
urllib3.exceptions.MaxRetryError: HTTPSConnectionPool(host='nimbus.pawsey.org.au', port=8080): Max retries exceeded with url: / (Caused by SSLError(SSLError("bad handshake: Error([('SSL routines', 'ssl3_get_record', 'wrong version number')])")))

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "./rest-request.py", line 122, in <module>
    r = requests.get(request_url, headers=headers)
  File "/home/ugovaretto/anaconda3/lib/python3.7/site-packages/requests/api.py", line 75, in get
    return request('get', url, params=params, **kwargs)
  File "/home/ugovaretto/anaconda3/lib/python3.7/site-packages/requests/api.py", line 60, in request
    return session.request(method=method, url=url, **kwargs)
  File "/home/ugovaretto/anaconda3/lib/python3.7/site-packages/requests/sessions.py", line 533, in request
    resp = self.send(prep, **send_kwargs)
  File "/home/ugovaretto/anaconda3/lib/python3.7/site-packages/requests/sessions.py", line 646, in send
    r = adapter.send(request, **kwargs)
  File "/home/ugovaretto/anaconda3/lib/python3.7/site-packages/requests/adapters.py", line 514, in send
    raise SSLError(e, request=request)
requests.exceptions.SSLError: HTTPSConnectionPool(host='nimbus.pawsey.org.au', port=8080): Max retries exceeded with url: / (Caused by SSLError(SSLError("bad handshake: Error([('SSL routines', 'ssl3_get_record', 'wrong version number')])")))
```

However the following request always works:

```bash
./rest-request.py 
Request URL = https://nimbus.pawsey.org.au:8080?
{'Host': 'nimbus.pawsey.org.au', 'X-Amz-Content-SHA256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'X-Amz-Date': '20200506T011548Z', 'Authorization': 'AWS4-HMAC-SHA256 Credential=00a5752015a64525bc45c55e88d2f162/20200506/us-east-1/s3/aws4_request, SignedHeaders=host;x-amz-content-sha256;x-amz-date, Signature=8a8bd828a537ff3e2432c1b11c37bf1039233ed49f6b3a9b1fceade2182dba2f'}

Response
Response code: 200

<?xml version="1.0" encoding="UTF-8"?><ListAllMyBucketsResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Owner><ID>a13e4c5196ec45b8ada423123b9b0772$a13e4c5196ec45b8ada423123b9b0772</ID><DisplayName>ugo-demo</DisplayName></Owner><Buckets><Bucket><Name>uv-bucket-1</Name><CreationDate>2020-05-04T08:53:21.054Z</CreationDate></Bucket></Buckets></ListAllMyBucketsResult>
```
