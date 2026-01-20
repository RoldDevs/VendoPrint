#!/usr/bin/env python3
"""
Simple HTTP redirect server for port 80
Redirects all HTTP requests to the Flask app on port 5000
This enables captive portal detection
"""

import http.server
import socketserver
import urllib.parse

class RedirectHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Parse the request path
        parsed_path = urllib.parse.urlparse(self.path)
        
        # Redirect to Flask app on port 5000
        redirect_url = f"http://{self.server.server_address[0]}:5000{parsed_path.path}"
        if parsed_path.query:
            redirect_url += f"?{parsed_path.query}"
        
        # Send redirect response
        self.send_response(302)
        self.send_header('Location', redirect_url)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        
        # Send a simple HTML redirect page
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0; url={redirect_url}">
    <title>Redirecting to VendoPrint...</title>
</head>
<body>
    <p>Redirecting to <a href="{redirect_url}">VendoPrint</a>...</p>
    <script>window.location.href = "{redirect_url}";</script>
</body>
</html>"""
        self.wfile.write(html.encode())
    
    def do_POST(self):
        # For POST requests, also redirect
        self.do_GET()
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

def run_redirect_server(host='0.0.0.0', port=80, silent=False):
    """Run the HTTP redirect server
    
    Args:
        host: Host to bind to
        port: Port to bind to (default 80)
        silent: If True, don't print messages (used when run from app.py thread)
    """
    try:
        with socketserver.TCPServer((host, port), RedirectHandler) as httpd:
            if not silent:
                print(f"HTTP redirect server running on http://{host}:{port}")
                print(f"Redirecting all requests to http://{host}:5000")
            httpd.serve_forever()
    except PermissionError:
        if not silent:
            print(f"ERROR: Permission denied. Port {port} requires root privileges.")
            print("Please run with sudo: sudo python3 http_redirect_server.py")
        # Re-raise if not silent so app.py can catch it
        if silent:
            raise
    except OSError as e:
        if not silent:
            if e.errno == 98:  # Address already in use
                print(f"ERROR: Port {port} is already in use.")
                print("Another service may be running on port 80.")
            else:
                print(f"ERROR: {e}")
        # Re-raise if silent so app.py can catch it
        if silent:
            raise

if __name__ == '__main__':
    run_redirect_server()
