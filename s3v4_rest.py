"""Send pure REST request to S3 v4 client

   Builds URL requests from
   * endpoint
   * access key
   * secret key
   * request parameters and content information

   __author__     = "Ugo Varetto"
   __license__    = "MIT"
   __version__    = "0.1"
   __maintainer__ = "Ugo Varetto"
   __email__      = "ugovaretto@gmail.com"
   __status__     = "Development"

"""

from urllib.parse import urlencode
import hashlib
import datetime
import hmac
import xml.etree.ElementTree as ET
from typing import Dict, Tuple

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
    closing_brace_index = tag.index('}')
    return tag if not closing_brace_index else tag[closing_brace_index+1:]


def _print_xml_tree(node, indentation_level=0, filter=lambda t: True):
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
    if filter(node.tag):
        print(" "*indent + f"{_clean_xml_tag(node.tag)}: {node.text}")
    for child in node:
        _print_xml_tree(child, indentation_level + 1)


###############################################################################
# Public interface


UNSIGNED_PAYLOAD = "UNSIGNED-PAYLOAD"  # identify payloads with no hash


def print_xml_response(text: str):
    """Print XML tree.

    Args:
        text (str): textual representation of XML tree
    Returns:
        None
    """
    tree = ET.fromstring(text)
    _print_xml_tree(tree)


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


def build_request_url(config: S3Config = None,
                      req_method: RequestMethod = "GET",
                      parameters: RequestParameters = None,
                      payload_hash: str = UNSIGNED_PAYLOAD,
                      payload_length: int = 0,
                      uri_path: str = '/') -> Request:

    """Build S3 REST request and headers

    S3Config type: Dict[str, str] with keys:
        protocol
        host
        port
        access_key
        secret_key

    Args:
        config (S3Config): dictionary containing endpoint info, access key,
                           secret key
        req_method (str): request method e.g. 'GET'
        parameters (RequestParameters): dictionary containing URI request
                                        parameters
        payload_hash (str): sha256-hash of payload, use 'UNSIGNED_PAYLOAD'
                            for non hashed payload
        payload_length (int): length of payload
        uri_path (str): path appended after protocol:hostname:port
    Returns:
        Tuple[URL, Headers
    """

    protocol = config['protocol']
    host = config['host']
    port = config['port']
    access_key = config['access_key']
    secret_key = config['secret_key']

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

    signed_headers = 'host;x-amz-content-sha256;x-amz-date'

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
               'Content-length': str(payload_length),
               'X-Amz-Content-SHA256': payload_hash,
               'X-Amz-Date': amzdate,
               'Authorization': authorization_header}

    # build request
    request_url = endpoint + canonical_uri
    if parameters:
        request_url += '?' + canonical_querystring

    return request_url, headers
