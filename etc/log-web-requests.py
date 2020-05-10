#!/usr/bin/env python3

import sys
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
import typing as T

"""Minimal logging http server, uses 'logging' module

   __author__: Ugo Varetto

   Usage: ./log-web-requests.py <port>

   HTTPServer will be printing out a 'localhost - - [date] "Request" status -'
   at each request in addition to the data logged by the RequestHandler class 
"""


class RequestHandler(BaseHTTPRequestHandler):

    # incremented at each request, cannot be an instance,
    # cannot be an instance variable because a new instance
    # is created at each http request received
    count: int = 0
    log_function: T.Callable = logging.info

    def __print_request_info(request, client_address, server):
        RequestHandler.log_function(f"{request}, {client_address}, {server}")

    def __init__(self, request, client_address, server):
        super(RequestHandler, self).__init__(request, client_address, server)
        # RequestHandler.__print_request_info(request, client_address, server)

    def _log(self, msg):
        RequestHandler.log_function(msg)

    def _print_text_header(self):
        headers_text = ""
        for (k, v) in self.headers.items():
            headers_text += f'{k}: {v}'
        return headers_text

    def _print_reqline_and_headers(self):
        RequestHandler.count += 1
        return "\n" + "="*20 + \
               f"Request #: {RequestHandler.count}\n" + \
               "------REQUEST LINE:\n" + \
               self.requestline + "\n\n" + \
               "------HEADERS" + "\n" + \
               self._print_text_header()

    def _send_default_response(self, method=None):
        # method not currently used
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._log(self._print_reqline_and_headers())
        self._send_default_response("GET")

    def do_HEAD(self):
        self._log(self._print_reqline_and_headers())
        self._send_default_response("HEAD")

    def do_POST(self):
        log_msg = "------REQUEST_BODY" + "\n" + \
                  self.rfile.read(int(self.headers['Content-Length']))
        self._log(self._print_reqline_and_headers() + "\n" + log_msg)
        self._send_default_response("POST")

    def do_PUT(self):
        log_msg = "------REQUEST_BODY" + "\n" + \
                  self.rfile.read(int(self.headers['Content-Length']))
        self._log(self._print_reqline_and_headers() + "\n" + log_msg)
        self._send_default_response("PUT")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f'usage: {sys.argv[0]} <port>', file=sys.stderr)
        sys.exit(-1)
    port = int(sys.argv[1])
    server_address = ('', port)
    handler_class = RequestHandler
    httpd = HTTPServer(server_address, handler_class)
    print(f"Starting http server on port {port}...")
    logging.basicConfig(level=logging.INFO)
    httpd.serve_forever()
