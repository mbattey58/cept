"""Send pure REST requests to S3 using protocol version 4

   Builds URL requests from
   * endpoint
   * access key
   * secret key
   * request parameters and content information

   __author__     = "Ugo Varetto"
   __license__    = "MIT"
   __version__    = "0.2"
   __maintainer__ = "Ugo Varetto"
   __email__      = "ugovaretto@gmail.com"
   __status__     = "Development"

"""

from urllib.parse import urlencode
import hashlib
import datetime
import hmac
import xml.etree.ElementTree as ET
import json
import requests
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
S3Config = Dict[str, str]
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
                      additional_headers: Dict[str, str] = None) -> Request:

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
        additiona_headers (Dic[str,str]): additional custom headers, the
                                          ones starting with 'x-amz-'
                                          are added to the singed list
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
    # TODO: raise excpetion if any key in 'additional_headers' matches keys
    # in headers dictionary ??
    if type(config) == S3Config:
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
    host = conf['host']
    port = conf['port']
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

    # headers: canonical and singned header list
    canonical_headers = \
        'host:' + host + '\n' + \
        "x-amz-content-sha256:" + payload_hash + '\n' + \
        'x-amz-date:' + amzdate + '\n'

    # add additional headers
    if additional_headers:
        for k, v in additional_headers.items():
            canonical_headers += f"{k}:{v}" + '\n'

    # extract all x-amz-* headers, add defaults, sort and
    # add to signed headers list
    signed_headers_list = ['host', 'x-amz-content-sha256', 'x-amz-date']
    if additional_headers:
        xamz = [x for x in additional_headers.keys()
                if x.lower()[:5] == 'x-amz']
        lk = [x.lower() for x in xamz]
        signed_headers_list.extend(lk)
        # ensure unique keys for signing purposes
        signed_headers_list = list(set(signed_headers_list))

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
    headers = {'Host': host,
               'X-Amz-Content-SHA256': payload_hash,
               'X-Amz-Date': amzdate}

    if payload_length:  # client might decide to non send content-length at all
        headers.update({"Content-Length": str(payload_length)})

    if additional_headers:
        headers.update(additional_headers)

    headers.update({'Authorization': authorization_header})

    # build request
    request_url = endpoint + canonical_uri
    if parameters:
        request_url += '?' + canonical_querystring

    return request_url, headers


_REQUESTS_METHODS = {"get": requests.get,
                     "put": requests.put,
                     "post": requests.post,
                     "delete": requests.delete}


def send_s3_request(config: Union[S3Config, str] = None,
                    req_method: RequestMethod = "GET",
                    parameters: RequestParameters = None,
                    payload: Union[str, ByteString] = None,
                    payload_is_file_name: bool = False,
                    sign_payload: bool = False,
                    bucket_name: str = None,
                    key_name: str = None,
                    action: str = None,
                    additional_headers: Dict[str, str] = None) \
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
    # payload, empty in this case
    payload_hash = None
    sign_payload = sign_payload if payload else False
    if sign_payload:
        if payload_is_file_name:
            raise NotImplementedError(
                    "Signing of file content not supported yet")
        else:
            payload_hash = hash(payload)

    if req_method.lower() not in _REQUESTS_METHODS.keys():
        raise ValueError(f"ERROR - invalid request method: {req_method}")
    content_length = len(payload) if payload else 0

    if key_name and not bucket_name:
        raise ValueError("ERROR - empty bucket, \
                         key without bucket not supported")

    uri_path = "/" + \
               (f"{bucket_name}/" if bucket_name else "") + \
               (f"{key_name}/" if key_name else "") + \
               (f"{action}" if action else "")

    if payload and payload_is_file_name:
        content_length = 0  # will be created by requests when uploading file

    # build request #1: text in body and payload hashing
    request_url, headers = build_request_url(
        config=config,
        req_method=req_method,
        parameters=parameters,
        payload_hash=payload_hash,
        payload_length=content_length,
        uri_path=uri_path,
        additional_headers=additional_headers
    )

    if payload and payload_is_file_name:
        f = {'upload_file': open(payload, 'rb')}
        response = _REQUESTS_METHODS[req_method.lower()](request_url,
                                                         files=f,
                                                         headers=headers)
    else:
        response = _REQUESTS_METHODS[req_method.lower()](request_url,
                                                         data=payload,
                                                         headers=headers)

    return response
