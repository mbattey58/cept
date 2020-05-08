#!/usr/bin/env python3

from sys import argv
from http.server import BaseHTTPRequestHandler, HTTPServer

"""Minimal logging http server, prints to stdout

   __author__: Ugo Varetto

   Usage: ./log-web-requests.py <port>
"""


class Server(BaseHTTPRequestHandler):

    count: int = 0

    def __print_request_info(request, client_address, server):
        print(f"{request}, {client_address}, {server}")

    def __init__(self, request, client_address, server):
        super(Server, self).__init__(request, client_address, server)
        # Server.__print_request_info(request, client_address, server)

    def _print_text_header(self):
        Server.count += 1
        print("\n" + "="*20)
        print(f"Request #: {Server.count}\n")
        print("HEADERS:")

    def _send_default_response(self, method):
        # method not currently used
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()

    def do_GET(self):
        self._print_text_header()
        print(self.headers)
        print("------REQUEST LINE:")
        print(self.requestline)
        self._send_default_response("GET")
       
    def do_HEAD(self):
        self._print_text_header
        print(self.headers)
        print("Request Type: 'HEAD'")
        self.send_response(200)

    def do_POST(self):
        self._print_text_header()
        print(self.headers)
        print("------REQUEST LINE:")
        print(self.requestline)
        print("------REQUEST_BODY")
        print(self.rfile.read(int(self.headers['Content-Length'])))
        self._send_default_response("POST")


if __name__ == "__main__":
    port = int(argv[1])
    server_address = ('', port)
    handler_class = Server
    httpd = HTTPServer(server_address, handler_class)
    print(f"Starting http server on port {port}...")
    httpd.serve_forever()
