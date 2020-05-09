#!/usr/bin/env python3

import sys
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
import typing as T

"""Minimal logging http server, uses 'logging' module

   __author__: Ugo Varetto

   Usage: ./log-web-requests.py <port>
"""


class RequestHandler(BaseHTTPRequestHandler):

    count: int = 0  # incremented at each request, cannot be an instance,
                    # cannot be an instance variable because a new instance
                    # is created at each http request received
            
    log_function: T.Callable = logging.info

    def __print_request_info(request, client_address, server):
        self._log(f"{request}, {client_address}, {server}")

    def __init__(self, request, client_address, server):
        super(RequestHandler, self).__init__(request, client_address, server)
        # RequestHandler.__print_request_info(request, client_address, server)

    def _log(self, msg):
        RequestHandler.log_function(msg)

    def _print_text_header(self):
        RequestHandler.count += 1
        self._log("\n" + "="*20)
        self._log(f"Request #: {RequestHandler.count}\n")
        self._log("HEADERS:")

    def _send_default_response(self, method=None):
        # method not currently used
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._print_text_header()
        self._log(self.headers)
        self._log("------REQUEST LINE:")
        self._log(self.requestline)
        self._send_default_response("GET")

    def do_HEAD(self):
        self._print_text_header
        self._log(self.headers)
        self._log("Request Type: 'HEAD'")
        self.send_response(200)

    def do_POST(self):
        self._print_text_header()
        self._log(self.headers)
        self._log("------REQUEST LINE:")
        self._log(self.requestline)
        self._log("------REQUEST_BODY")
        self._log(self.rfile.read(int(self.headers['Content-Length'])))
        self._send_default_response("POST")

    def do_PUT(self):
        self._print_text_header()
        self._log(self.headers)
        self._log("------REQUEST LINE:")
        self._log(self.requestline)
        self._log("------REQUEST_BODY")
        self._log(self.rfile.read(int(self.headers['Content-Length'])))
        self._send_default_response("PUT")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f'usage: {sys.argv[0]} <port>', sys.stderr)
        sys.exit(-1)
    port = int(sys.argv[1])
    server_address = ('', port)
    handler_class = RequestHandler
    httpd = HTTPServer(server_address, handler_class)
    print(f"Starting http server on port {port}...")
    logging.basicConfig(level=logging.INFO)
    httpd.serve_forever()
