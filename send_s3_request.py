import s3v4_rest
import requests

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
        additiona_headers (Dic[str,str]): additional custom header, the
                                          ones starting with 'x-amz-'
                                          are added to the singed list
    Returns:
        Tuple[URL, Headers

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