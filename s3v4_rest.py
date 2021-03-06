"""Send REST requests to S3 using protocol version 4

   Signs headers and builds URL requests from
   * endpoint
   * access key
   * secret key
   * request parameters and content information

   __author__     = "Ugo Varetto"
   __credits__    = ["Ugo Varetto", "Luca Cervigni"]
   __license__    = "MIT"
   __version__    = "0.5"
   __maintainer__ = "Ugo Varetto"
   __email__      = "ugovaretto@gmail.com"
   __status__     = "Development"

   See:
        https://docs.aws.amazon.com/AmazonS3/latest/API/sig-v4-header-based-auth.html

"""

from urllib.parse import urlencode
import hashlib
import datetime
import hmac
import xml.etree.ElementTree as ET
import json
import requests
import logging
import time
import xml.dom.minidom  # better than ET for pretty printing
from typing import Dict, Tuple, List, Union, ByteString, Callable

###############################################################################
# Private interface

# standard signing functions from AWS


def _sign(key, msg):
    """Sign string with key

    Args:
        key (str): key
        msg (str): test to sign
    """
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def _get_signature(key, date_stamp, region_name):
    """Create signature

    Args:
        key (str): starting key
        date_stamp (str): date
        region_name (str): AWS region e.g. 'us-east-1'
    Returns:
        str: signature

    """
    date_k = _sign(('AWS4' + key).encode('utf-8'), date_stamp)
    region_k = _sign(date_k, region_name)
    service_k = _sign(region_k, 's3')
    signing_key = _sign(service_k, 'aws4_request')
    return signing_key


def _clean_xml_tag(tag):
    """ElementTree prefixes tags with a namespace if present
       use this function to remove prefix.

    Args:
        tag (str): XML tag
    Returns:
        XML tag without {..} prefix
    """
    closing_brace_index = tag.find('}')
    return tag if closing_brace_index < 0 else tag[closing_brace_index+1:]


def _xml_to_text(node: ET,
                 indentation_level: int = 0,
                 filter: Callable = lambda t: True):
    """Recursively print xml tree

    note: Python as a limit on the recursion level it can handle,
          this is just implemented like this without returning functions
          or using stacks to keep the code simple

    Args:
        node (ElementTree.Element): a node in the XML tree
        indentaion_level (int): indendation level == nesting level in tree
        filter (function): ignore nodes for which function returns False
    Returns:
        None
    """
    BLANKS = 2
    indent = indentation_level * BLANKS
    text = ""
    if filter(node.tag):
        text += " "*indent + f"{_clean_xml_tag(node.tag)}: {node.text}\n"
    for child in node:
        text += _xml_to_text(child, indentation_level + 1)
    return text


_XML_NAMESPACE_PREFIX = "{http://s3.amazonaws.com/doc/2006-03-01/}"

###############################################################################
# Public interface

UNSIGNED_PAYLOAD = "UNSIGNED-PAYLOAD"  # identify payloads with no hash


def encode_url(params: Dict):
    """Forward to urlencode, since we are alrady importing urlib.parse here
       do not require client code to re-import it.

    Args:
        params (Dict): dictionary containing list of key, value pairs
    Returns:
        str: URL-encoded text
    """
    return urlencode(params)


def build_multipart_list(parts: List[Tuple[int, str]]) -> str:
    """Return XML multipart message with list of part numbers & ETags

    Args:
        parts (List[Tuple[int, str]]): list of (part num, ETag) tuples
    Returns:
        XML part list
    """
    begin = '<CompleteMultipartUpload>'
    body = ""
    for (partnum, etag) in parts:
        body += f"<Part><ETag>{etag}</ETag>"
        body += f"<PartNumber>{partnum}</PartNumber></Part>"

    end = "</CompleteMultipartUpload>"

    return begin + body + end


def get_upload_id(xml_response: str):
    """Extract UploadId value from xml response

    This function in mainly meant to be used when performing explicit
    multipart uploads to extract the request/transaction id after
    the first POST request to initiate the multipart upload.

    Args:
        xml_response (str): UploadId tag returned by S3 server
    Returns:
        str: request id

    """
    tree = ET.fromstring(xml_response)
    return tree.find(f"{_XML_NAMESPACE_PREFIX}UploadId").text


def get_tag_id(response_header: Dict[str, str]):
    """Extract ETag header field from response header

    This function in mainly meant to be used when performing explicit
    multipart uploads to extract the ETag id of each request to compose
    the final XML request to be sent when the transation if finalised.

    Args:
        response_header (Dict[str, str]): header returned by S3 server
    Returns:
        str: ETag id

    """
    return response_header['ETag']


def xml_to_text(text: str):
    """Print XML tree to text

    Args:
        text (str): textual representation of XML tree
    Returns:
        str: indented textual representation of XML tag hierarchy
    """
    if not text:
        return ""
    tree = ET.fromstring(text)
    return _xml_to_text(tree)


def hash(data):
    """SHA 256 hash of text or binary data

    Args:
        data (str or binary): data to hash
    Returns:
        str: textual hexadecimal representation of SHA 256-encoded data
    """
    if type(data) == str:
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    else:
        return hashlib.sha256(data).hexdigest()


# Type declarations
S3Config = Dict
RequestMethod = str
RequestParameters = Dict[str, str]
Headers = Dict[str, str]
URL = str
Request = Tuple[URL, Headers]


def build_request_url(config: Union[S3Config, str] = None,
                      req_method: RequestMethod = "GET",
                      parameters: RequestParameters = None,
                      payload_hash: str = UNSIGNED_PAYLOAD,
                      payload_length: int = 0,
                      uri_path: str = '/',
                      additional_headers: Dict[str, str] = None,
                      proxy_endpoint: str = None) -> Request:
    """Build S3 REST request and headers

    S3Config type: Dict[str, str] with keys:
        protocol
        host
        port
        access_key
        secret_key

    Args:
        config (Union[S3Config, str]): dictionary containing endpoint info,
                                       access key, secret key OR file path
                                       to json configuration file
        req_method (str): request method e.g. 'GET'
        parameters (RequestParameters): dictionary containing URI request
                                        parameters
        payload_hash (str): sha256-hash of payload, use 'UNSIGNED_PAYLOAD'
                            for non hashed payload
        payload_length (int): length of payload, in case of 'None' no
                              'Content-Length" header is added
        uri_path (str): path appended after protocol:hostname:port
        additional_headers (Dict[str,str]): additional custom headers, the
                                            ones starting with 'x-amz-'
                                            are added to the singed list
        proxy_endpoint (str): in cases where the request is sent to a proxy
                              do use this endpoint to compose the url
    Returns:
        Tuple[URL, Headers]

    Example of json configuration file in case a string is passed as 'config'
    parameters:

    {
        "access_key": "00000000000000000000000000000000",
        "secret_key": "11111111111111111111111111111111",
        "protocol"  : "http",
        "host"      : "localhost",
        "port"      : 8000
    }

    """
    start = time.perf_counter()
    # TODO: raise excpetion if any key in 'additional_headers' matches keys
    # in headers dictionary ??
    if type(config) == dict:
        conf = config
    else:  # interpret as file path
        with open(config, "r") as f:
            conf = json.loads(f.read())

    req_method = req_method.upper()
    # no explicit rasing of exceptions because the run-time will already
    # raise the relevant ones should something fail e.g. in case keys
    # are not found in config dictionary a KeyError exception is thrown.

    payload_hash = payload_hash or UNSIGNED_PAYLOAD  # in case its None
    protocol = conf['protocol']
    port = conf['port'] if 'port' in conf.keys() else None
    host = conf['host']
    access_key = conf['access_key']
    secret_key = conf['secret_key']

    service = 's3'
    method = req_method
    region = 'us-east-1'  # works with Ceph, any region might work actually
    endpoint = protocol + '://' + host + (f":{port}" if port else '')

    request_parameters = urlencode(parameters) if parameters else ''

    # canonical URI
    canonical_uri = uri_path
    canonical_querystring = request_parameters

    # dates for headers credential string
    dt = datetime.datetime.utcnow()
    amzdate = dt.strftime('%Y%m%dT%H%M%SZ')
    # Date w/o time, used in credential scope
    datestamp = dt.strftime('%Y%m%d')

    default_headers = {'Host': host + (f":{port}" if port else ''),
                       'X-Amz-Content-SHA256': payload_hash,
                       'X-Amz-Date': amzdate}

    x_amz_headers = {}
    if additional_headers:
        x_amz_headers = {k.strip(): additional_headers[k]
                         for k in additional_headers.keys()
                         if k.lower().strip()[:len('x-amz')] == 'x-amz'}

    all_headers = default_headers.copy()
    all_headers.update(x_amz_headers)
    canonical_headers = "\n".join(
        [f"{k.lower().strip()}:{all_headers[k].strip()}"
         for k in sorted(all_headers.keys())]) + "\n"

    # add all x-amz-* headers, sort and add to signed headers list
    signed_headers_list = ['host', 'x-amz-content-sha256', 'x-amz-date']
    if x_amz_headers:
        signed_headers_list.extend([x.lower().strip()
                                    for x in x_amz_headers.keys()])

    # keys are already unique since all (key, value) pairs are stored in
    # dictionary with unique keys, this means the case of multiple headers
    # with the same key is not supported
    signed_headers_list.sort()

    # build signed header string
    signed_headers = ";".join(signed_headers_list)

    # canonical request
    canonical_request = \
        method + "\n" +  \
        canonical_uri + '\n' +  \
        canonical_querystring + '\n' + \
        canonical_headers + '\n' +  \
        signed_headers + '\n' +  \
        payload_hash

    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = \
        datestamp + \
        '/' + \
        region + \
        '/' + \
        service + \
        '/' + \
        'aws4_request'

    # string to sign
    string_to_sign = \
        algorithm + '\n' + \
        amzdate + '\n' + \
        credential_scope + '\n' + \
        hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()

    signing_key = _get_signature(secret_key, datestamp, region)

    # sign string with signing key
    signature = hmac.new(signing_key, string_to_sign.encode(
        'utf-8'), hashlib.sha256).hexdigest()

    # build authorisaton header
    authorization_header = \
        algorithm + ' ' + 'Credential=' + \
        access_key + '/' + \
        credential_scope + ', ' + 'SignedHeaders=' + \
        signed_headers + ', ' + 'Signature=' + signature

    # build standard headers
    headers = default_headers

    if additional_headers:
        headers.update(additional_headers)

    if payload_length:  # client might decide to non send content-length at all
        headers.update({"Content-Length": str(payload_length)})

    headers.update({'Authorization': authorization_header})

    if logging.getLogger().level == logging.DEBUG:
        elapsed = time.perf_counter() - start
        logging.debug(f"Header signing time (us): {int(elapsed * 1E6)}")

    # build request
    endpoint = proxy_endpoint or endpoint
    request_url = endpoint + canonical_uri
    if parameters:
        request_url += '?' + canonical_querystring

    if logging.getLogger().level == logging.DEBUG:
        n = '\n'
        msg = "CANONICAL REQUEST\n" + 20 * "=" + n
        msg += "Method: " + method + n + \
               "Canonical URI: " + canonical_uri + n + \
               "Canonical querystring: " + canonical_querystring + n + \
               "Canonical headers: " + n
        chl = canonical_headers.split("\n")
        for h in chl:
            msg += "\t" + h + n
        msg += "Payload hash: " + (payload_hash or "")
        logging.debug(msg)

    if logging.getLogger().level == logging.INFO:
        msg = "REQUEST HEADERS\n" + 20 * "=" + '\n'
        for k, v in headers.items():
            msg += f"{k}: {v}\n"
        msg += "\n" + "REQUEST URL: " + request_url + '\n'

    return request_url, headers


_REQUESTS_METHODS = {"get": requests.get,
                     "put": requests.put,
                     "post": requests.post,
                     "delete": requests.delete,
                     "head": requests.head}


def _find_key(d: Dict, key: str):
    k = [x for x in d.keys() if x.lower() == key.lower()]
    return k[0] if len(k) else None


def send_s3_request(config: Union[S3Config, str] = None,
                    req_method: RequestMethod = "GET",
                    parameters: RequestParameters = None,
                    payload: Union[str, ByteString] = None,
                    payload_is_file_name: bool = False,
                    sign_payload: bool = False,
                    bucket_name: str = None,
                    key_name: str = None,
                    additional_headers: Dict[str, str] = None,
                    content_file: str = None,
                    proxy_endpoint: str = None,
                    chunk_size: int = 1 << 20) \
        -> requests.Request:
    """Send REST request with headers signed according to S3v4 specification

    S3Config type: Dict[str, str] with keys:
        protocol
        host
        port
        access_key
        secret_key

    Args:
        config (Union[S3Config, str]): dictionary containing endpoint info,
                                       access key, secret key OR file path
                                       to json configuration file
        req_method (str): request method e.g. 'GET'
        parameters (RequestParameters): dictionary containing URI request
                                        parameters
        payload (str or ByteString): string or bytes (e.g. array.to_bytes())
                                     if 'payload_is_file_name' equals 'True'
                                     then this parameter is interpreted
                                     as a filepath, and the file descriptor
                                     returned by 'open' will be passed to the
                                     'data' paramter of the
                                     requests.* functions
        sign_payload (bool): sign payload, not currently supported when
                             filepath specified
        bucket_name (str): name of bucket appended to URI: /bucket_name
        key_name (str): name of key appended to URI :/bucket_name/key_name
        action (str): name of actional appended to URI:
                      /bucket_name/key_name/action
        additiona_headers (Dic[str,str]): additional custom headers, the
                                          ones starting with 'x-amz-'
                                          are added to the singed list
        content_file (str): file to store received content
        proxy_endpoint: endpoint to which requests will be sent for further
                        forwarding to actual endpoint
    Returns:
        requests.Response

    Example of json configuration file in case a string is passed as 'config'
    parameters:

    {
        "access_key": "00000000000000000000000000000000",
        "secret_key": "11111111111111111111111111111111",
        "protocol"  : "http",
        "host"      : "localhost",
        "port"      : 8000
    }

    """
    start = time.perf_counter()
    payload_hash = None
    if sign_payload:
        if payload_is_file_name:
            raise NotImplementedError(
                "Signing of file content not supported yet")
        else:
            payload = payload or ""
            payload_hash = hash(payload)

    if req_method.lower() not in _REQUESTS_METHODS.keys():
        raise ValueError(f"ERROR - invalid request method: {req_method}")
    content_length = len(payload) if payload else 0

    if key_name and not bucket_name:
        raise ValueError("ERROR - empty bucket, \
                         key without bucket not supported")

    uri_path = "/" + \
               (f"{bucket_name}" if bucket_name else "") + \
               (f"/{key_name}" if key_name else "")

    if payload and payload_is_file_name:
        content_length = 0  # will be created by requests when uploading file

    # in case of url parameters, method == POST and empty payload, parameters
    # are urlencoded and passed in body automatically by requests and therefore
    # request is built with empty body and empty uri
    req_parameters = parameters
    _, headers = build_request_url(
        config=config,
        req_method=req_method,
        parameters=req_parameters,
        payload_hash=payload_hash,
        payload_length=content_length,
        uri_path=uri_path,
        additional_headers=additional_headers,
        proxy_endpoint=proxy_endpoint
    )

    request_url = None
    if proxy_endpoint:
        request_url = proxy_endpoint
    else:
        request_url = f"{config['protocol']}://{config['host']}"
        if 'port' in config.keys():
            request_url += ":" + str(config['port'])
    request_url += "/"
    if bucket_name:
        request_url += bucket_name
        if key_name:
            request_url += "/" + key_name

    response = None
    if payload and payload_is_file_name:
        response = _REQUESTS_METHODS[req_method.lower()](
            request_url,
            data=open(payload, 'rb'),
            params=parameters,
            headers=headers,
            stream=True)
        if logging.getLogger().level == logging.DEBUG:
            logging.debug("Payload: file " + payload + '\n')
    else:
        data = payload
        if parameters and not payload and req_method.lower() == 'post':
            data = parameters
        response = _REQUESTS_METHODS[req_method.lower()](url=request_url,
                                                         data=data,
                                                         params=parameters,
                                                         headers=headers,
                                                         stream=True)
        if logging.getLogger().level == logging.DEBUG:
            logging.debug("Payload: \n" + (payload or "") + '\n')

    def ok(code):
        return 200 <= code < 300

    def transfer_chunked(headers):
        for k in headers.keys():
            if k.lower() == "transfer-encoding":
                return headers[k].lower() == "chunked"
        return False

    chunked = transfer_chunked(response.headers)

    if content_file and ok(response.status_code) and response.content:
        with open(content_file, "wb") as of:
            if chunked:
                for i in response.iter_content(chunk_size=chunk_size):
                    of.write(i)
            else:
                of.write(response.content)

    logfun = logging.info if ok(response.status_code) else logging.error

    if logging.getLogger().level == logging.DEBUG:
        elapsed = time.perf_counter() - start
        digits = 4
        logfun("Request-reponse time (s): " +
               f"{int(elapsed * 10**digits)/10**digits}")

    if logging.getLogger().level == logging.INFO:
        msg = "\nRESPONSE STATUS CODE: " + str(response.status_code) + '\n'
        msg += "RESPONSE HEADERS\n" + 20 * "=" + '\n'
        for k, v in response.headers.items():
            msg += f"{k}: {v}\n"
        logfun(msg)

    def read_chunks():
        nonlocal response
        text = ""
        if chunked:
            for i in response.iter_content(chunk_size=chunk_size):
                text += i.decode('utf-8')
        else:
            text = response.content.decode('utf-8')
        return text

    content_type = None
    for k in response.headers.keys():
        if k.lower() == "content-type":
            content_type = response.headers[k]

    if response.content and not content_file:
        msg = "RESPONSE CONTENT\n" + 20 * "=" + '\n'
        if content_type:
            if ("application/json" in content_type or
                    "text/plain" in content_type):
                msg += read_chunks()
            elif ("text/html" in content_type or
                    "application/xml" in content_type):
                dom = xml.dom.minidom.parseString(read_chunks())
                pretty = dom.toprettyxml(indent="   ")
                msg += pretty
            else:
                msg += read_chunks()[:1024]
        else:
            msg += read_chunks()[:1024]
        logfun(msg)

    return response
