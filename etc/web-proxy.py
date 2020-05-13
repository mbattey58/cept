#!/usr/bin/env python3

import sys
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import typing as T
from urllib.parse import parse_qs


"""Minimal proxy http server, uses 'logging' module, forwards requests to
   remote endpoint.

   __author__: Ugo Varetto

   Usage: ./web-proxy.py <port> <endpoint>

   HTTPServer will be printing out a 'localhost - - [date] "Request" status -'
   at each request in addition to the data logged by the ProxyRequestHandler
   class.

   The web server accepts /__config/... URIs to remotely configure the
   environment, currently only /__config/endpoint=<endpoint>  and 
   /__config/download-chunk-size are supported
"""

_REMOTE_URL: str = ""
_DOWNLOAD_CHUNK_SIZE: int = 1 << 20


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

    def _inject_auth(self):
        return self.headers

    def _parse_headers(self):
        return self._inject_auth()

    def _send_headers(self, headers):
        for (k, v) in headers.items():
            self.send_header(k, v)

    def _url(self):
        remote_path = self.path
        return self.remote_url + f"{remote_path}"

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

    def _send_config_response(self):
        self.send_response(code=200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        resp = "<html><head></head><body><h2>Configuration</h2>" + \
               f"<p>Remote URL: {self.remote_url}</p>" + \
               f"<p>Download buffer size: {self.chunk_size}</p>" + \
               "</body></html>"
        self.wfile.write(bytes(resp, 'UTF-8'))

    def _handle_configuration(self):
        req = parse_qs(self.path)
        k = list(req.keys())
        if len(k) == 0:
            return False
        if k[0][0:len("/__config/")] != "/__config/":
            return False
        k[0] = k[len("/__config/"):]
        v = list(req.values())
        req = dict(zip(k, v))
        if "endpoint" in k:
            global _REMOTE_URL
            _REMOTE_URL = req["endpoint"]
        if "download-chunk-size" in k:
            global _DOWNLOAD_CHUNK_SIZE
            _DOWNLOAD_CHUNK_SIZE = int(req["download-chunk-size"])
        self._send_config_response()
        return True

    # Public interface ###################################################

    def __init__(self, request, client_address, server):
        self.remote_url = _REMOTE_URL
        self.chunk_size = _DOWNLOAD_CHUNK_SIZE
        super(ProxyRequestHandler, self).__init__(
            request, client_address, server)

    def do_GET(self):
        if self._handle_configuration():
            self._send_default_response()
            return
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
        a = array('b', self.rfile.read(int(self.headers['Content-Length'])))
        log_msg = "------REQUEST_BODY" + "\n" + \
                  f"{a.tostring()}"
        self._log(log_msg)
        if self.remote_url:
            req_headers = self._parse_headers()
            data = self.rfile.read()  # int(self.headers['Content-Length']))
            resp = requests.post(self._url(), data=data, headers=req_headers,
                                 stream=True)
            self._send_response(resp)
        else:
            self._send_default_response()

    def do_PUT(self):
        self._log(self._print_reqline_and_headers())
        from array import array
        a = array('b', self.rfile.read(int(self.headers['Content-Length'])))
        log_msg = "------REQUEST_BODY" + "\n" + \
                  f"{a.tostring()}"
        self._log(log_msg)
        if self.remote_url:
            req_headers = self._parse_headers()
            data = self.rfile.read()  # int(self.headers['Content-Length']))
            resp = requests.put(self._url(), data=data, headers=req_headers,
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
