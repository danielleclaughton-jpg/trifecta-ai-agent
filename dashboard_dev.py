"""Simple static file server for the dev dashboard.
Run this alongside the Flask API (which should run on http://localhost:5000).
This serves dashboard_index.html from the repository root on http://localhost:3015/
"""
import http.server
import socketserver
import os

PORT = 3015

BASE_DIR = os.path.dirname(__file__)
INDEX_FILE = 'dashboard_index.html'

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve the dashboard_index.html at the root path
        if self.path == '/' or self.path == '':
            self.path = '/' + INDEX_FILE
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

os.chdir(BASE_DIR)
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving dashboard at http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Shutting down')
        httpd.server_close()
