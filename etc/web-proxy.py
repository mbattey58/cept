#!/usr/bin/env python3

import sys
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import typing as T
from urllib.parse import parse_qs
from urllib.parse import urlparse
import json
import re

"""Minimal proxy http server, uses 'logging' module, forwards requests to
   remote endpoint.

   __author__: Ugo Varetto

   Usage: ./web-proxy.py <port> <endpoint>

   HTTPServer will be printing out a 'localhost - - [date] "Request" status -'
   at each request in addition to the data logged by the ProxyRequestHandler
   class.

   The web server accepts /__config/... URIs to remotely configure the
   environment, currently only /__config/endpoint=<endpoint> and
   /__config/download-chunk-size are supported
"""

# TODO:move all configuration parameters into _CONFIG dict and just call
# dict.update with content of JSON config request

_REMOTE_URL: str = ""
_DOWNLOAD_CHUNK_SIZE: int = 1 << 20
_MAX_LOG_CONTENT_LENGTH: int = 1 << 10

# NOTE: NOT IMPLEMENTED YET
# _AWS_V4_SIGNING = False
# _AWS_ACCESS_KEY = ""
# _AWS_SECRET_KEY = ""
# _REQUEST_TIMEOUT = 5
# _VERIFY_SSL = True
# _MAX_RETRIES = 1


class ProxyRequestHandler(BaseHTTPRequestHandler):

    # incremented at each request, cannot be an instance, because a new
    # instance is created at each http request received
    count: int = 0
    log_function: T.Callable = logging.info

    # Private interface ###################################################

    def log_message(self, format: str = "", *args):
        s = format
        for a in args:
            s = s.replace('%s', a, 1)
        ProxyRequestHandler.log_function(s)

    def _log(self, msg):
        self.log_message(msg)

    def _print_text_header(self):
        headers_text = ""
        for (k, v) in self.headers.items():
            headers_text += f'{k}: {v}\n'
        return headers_text

    def _print_reqline_and_headers(self):
        ProxyRequestHandler.count += 1
        return "\n===> " + ">"*20 + '\n' + \
               f"**REQUEST #: {ProxyRequestHandler.count}\n" + \
               "------REQUEST LINE:\n" + \
               self.requestline + "\n\n" + \
               "------HEADERS" + "\n" + \
               self._print_text_header()

    def _print_response(self, resp):
        return "\n" + "<"*20 + ' <===\n' + \
               f"**RESPONSE #: {ProxyRequestHandler.count}\n" + \
               "------STATUS: " + str(resp.status_code) + '\n' + \
               "------HEADERS" + "\n" + \
               str(resp.headers) + "\n" + \
               "------CONTENT\n" + resp.text

    def _send_default_response(self, method=None):
        # method not currently used
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.requestline()
        self.headers()

    def _inject_auth(self, headers):
        return headers

    def _parse_headers(self):
        headers = self.headers
        headers['Host'] = self.host
        return self._inject_auth(headers)

    def _send_headers(self, headers):
        for (k, v) in headers.items():
            self.send_header(k, v)

    def _url(self):
        r = requests.head(self.remote_url + self.path, allow_redirects=True)
        return r.url

    def _send_response(self, resp):
        msg = self._print_response(resp)
        self.send_response(resp.status_code)
        self.end_headers()
        count = 0
        size = 0
        for i in resp.iter_content(chunk_size=self.chunk_size):
            self.wfile.write(i)
            count += 1
            size = max(size, len(i))
        msg += f"\nNumber of chunks: {count}, max chunk size: {size} bytes\n\n"
        self._log(msg)

    def _handle_rest_request(self, json_content):
        config = json.loads(json_content)
        global _REMOTE_URL
        global _DOWNLOAD_CHUNK_SIZE
        result = "no recongnized parameter name in request"
        if "_REMOTE_URL" in config.keys():
            _REMOTE_URL = config["_REMOTE_URL"]
            result = "OK"
        if "_DOWNLOAD_CHUNK_SIZE" in config.keys():
            _DOWNLOAD_CHUNK_SIZE = config["_DOWNLOAD_CHUNK_SIZE"]
            result = "OK"
        if "get_config" in config.keys():
            result = f'{{"_REMOTE_URL": "{_REMOTE_URL}",' + \
                     f'"_DOWNLOAD_CHUNK_SIZE": "{_DOWNLOAD_CHUNK_SIZE}"' + \
                     "}}"
            return result

        return f'{{"result": "{result}"}}'

    def _read_content(self):
        r = re.compile("[Cc]ontent-[Ll]ength")
        cl = list(filter(r.match, self.headers.keys()))
        if len(cl) == 0:
            return None
        return self.rfile.read(int(self.headers[cl[0]]))

    # Public interface ###################################################

    def __init__(self, request, client_address, server):
        self.remote_url = _REMOTE_URL
        self.chunk_size = _DOWNLOAD_CHUNK_SIZE
        parsed_uri = urlparse(self.remote_url)
        self.host = parsed_uri.netloc
        super(ProxyRequestHandler, self).__init__(
            request, client_address, server)

    def do_GET(self):
        self._log(self._print_reqline_and_headers())
        if self.remote_url:
            req_headers = self._parse_headers()
            resp = requests.get(self._url(), headers=req_headers, stream=True)
            self._send_response(resp)
        else:
            self._send_default_response()

    def do_HEAD(self):
        self._log(self._print_reqline_and_headers())
        if self.remote_url:
            req_headers = self._parse_headers()
            resp = requests.head(self._url(), headers=req_headers, stream=True)
            self._send_response(resp)
        else:
            self._send_default_response()

    def do_POST(self):
        self._log(self._print_reqline_and_headers())
        from array import array
        content = self._read_content()
        global _MAX_LOG_CONTENT_LENGTH
        if len(content) < _MAX_LOG_CONTENT_LENGTH:
            log_msg = "------REQUEST_BODY" + "\n" + \
                      f"{str(content)}"
        self._log(log_msg)
        if self.remote_url:
            req_headers = self._parse_headers()
            resp = requests.put(self._url(), data=content, headers=req_headers,
                                stream=True)
            self._send_response(resp)
        else:
            self._send_default_response()

    def do_PUT(self):
        self._log(self._print_reqline_and_headers())
        from array import array
        content = self._read_content()
        global _MAX_LOG_CONTENT_LENGTH
        if len(content) < _MAX_LOG_CONTENT_LENGTH:
            log_msg = "------REQUEST_BODY" + "\n" + \
                      f"{str(content)}"
        self._log(log_msg)
        if "application/json" in [v.lower() for v in self.headers.values()]:
            ret = self._handle_rest_request(content)
            self.send_response(code=200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(ret.encode('utf-8'))
            return
        if self.remote_url:
            req_headers = self._parse_headers()
            resp = requests.put(self._url(), data=content, headers=req_headers,
                                stream=True)
            self._send_response(resp)
        else:
            self._send_default_response()

    def do_DELETE(self):
        self._log(self._print_reqline_and_headers())
        if self.remote_url:
            req_headers = self._parse_headers()
            resp = requests.delete(
                self._url(), headers=req_headers, stream=True)
            self._send_response(resp)
        else:
            self._send_default_response()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f'usage: {sys.argv[0]} <port> <remote url>', file=sys.stderr)
        sys.exit(-1)
    if len(sys.argv) == 3:
        # global _REMOTE_URL "annotated name can't be global" issue
        _REMOTE_URL = sys.argv[2]
    port = int(sys.argv[1])
    server_address = ('', port)
    handler_class = ProxyRequestHandler
    httpd = HTTPServer(server_address, handler_class)
    print(f"Starting http server on port {port}" +
          (f", forwarding requests to {_REMOTE_URL}" if _REMOTE_URL else ""))
    logging.basicConfig(level=logging.INFO)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\rexiting...")  # without '\r' '^C' is shown
        sys.exit(0)
    except Exception as e:
        print("Error: " + e, file=sys.stderr)
