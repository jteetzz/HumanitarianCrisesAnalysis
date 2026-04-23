import http.server
import webbrowser
import os

PORT = 8080
DIR  = os.path.dirname(os.path.abspath(__file__))

os.chdir(DIR)

webbrowser.open(f"http://localhost:{PORT}")

handler = http.server.SimpleHTTPRequestHandler
with http.server.HTTPServer(("", PORT), handler) as httpd:
    print(f"  Serving at http://localhost:{PORT}")
    print(f"  Press Ctrl+C to stop.\n")
    httpd.serve_forever()
