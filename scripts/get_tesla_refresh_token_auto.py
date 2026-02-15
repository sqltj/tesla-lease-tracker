#!/usr/bin/env python3
"""Get Tesla refresh token via OAuth flow with automatic callback capture.

This script starts a local server to capture the authorization callback
and automatically exchanges it for a refresh token.

Usage:
    uv run python scripts/get_tesla_refresh_token_auto.py \
      --client-id YOUR_CLIENT_ID \
      --client-secret YOUR_CLIENT_SECRET
"""

import argparse
import sys
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, parse_qs, urlparse
import threading
import requests


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler to capture OAuth callback."""

    auth_code = None

    def do_GET(self):
        """Handle GET request from OAuth callback."""
        parsed_path = urlparse(self.path)
        params = parse_qs(parsed_path.query)

        code = params.get("code", [None])[0]
        error = params.get("error", [None])[0]

        if error:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = f"<h1>Authorization Failed</h1><p>Error: {error}</p>"
            self.wfile.write(html.encode())
            CallbackHandler.auth_code = None
            return

        if code:
            CallbackHandler.auth_code = code
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = """
            <h1>✅ Authorization Successful!</h1>
            <p>You can close this window and return to the terminal.</p>
            """
            self.wfile.write(html.encode())
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = "<h1>❌ No authorization code received</h1>"
            self.wfile.write(html.encode())

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def main():
    parser = argparse.ArgumentParser(
        description="Get Tesla refresh token via automatic OAuth flow"
    )
    parser.add_argument(
        "--client-id",
        required=True,
        help="Tesla OAuth client ID from developer.tesla.com",
    )
    parser.add_argument(
        "--client-secret",
        required=True,
        help="Tesla OAuth client secret from developer.tesla.com",
    )

    args = parser.parse_args()

    print("\n🔐 Tesla OAuth Authorization Flow (Auto)")
    print("=" * 50)

    # Start local callback server
    print("\n1. Starting callback server on http://localhost:8080...")
    server = HTTPServer(("localhost", 8080), CallbackHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    print("   ✓ Server ready")

    # Build authorization URL
    auth_params = {
        "client_id": args.client_id,
        "response_type": "code",
        "redirect_uri": "http://localhost:8080/callback",
        "scope": "openid email offline_access vehicle_device_data",
        "state": "tesla-lease-tracker",
    }
    auth_url = f"https://auth.tesla.com/oauth2/v3/authorize?{urlencode(auth_params)}"

    print("\n2. Opening Tesla authorization page...")
    print(f"   URL: {auth_url}\n")

    try:
        webbrowser.open(auth_url)
        print("   ✓ Opened in browser")
    except Exception as e:
        print(f"   ⚠️  Could not open browser: {e}")
        print(f"   Please visit manually: {auth_url}")

    print("\n3. Waiting for authorization...")
    print("   Authorize the application in your browser...\n")

    # Wait for callback
    timeout = 300  # 5 minutes
    start_time = __import__("time").time()

    while __import__("time").time() - start_time < timeout:
        if CallbackHandler.auth_code:
            code = CallbackHandler.auth_code
            print(f"   ✓ Got authorization code: {code[:20]}...\n")
            break
        __import__("time").sleep(0.5)
    else:
        print("   ❌ Timeout waiting for authorization")
        sys.exit(1)

    server.shutdown()

    # Exchange code for tokens
    print("4. Exchanging code for tokens...")

    try:
        token_response = requests.post(
            "https://auth.tesla.com/oauth2/v3/token",
            json={
                "grant_type": "authorization_code",
                "client_id": args.client_id,
                "client_secret": args.client_secret,
                "code": code,
                "redirect_uri": "http://localhost:8080/callback",
            },
            timeout=10,
        )

        if token_response.status_code != 200:
            print(f"   ❌ Token exchange failed: {token_response.text}")
            sys.exit(1)

        tokens = token_response.json()
        refresh_token = tokens.get("refresh_token")

        if not refresh_token:
            print("   ❌ No refresh token in response")
            print(f"   Response: {tokens}")
            sys.exit(1)

        print("   ✓ Token exchange successful!")

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("✅ Refresh Token Obtained!")
    print("=" * 50)
    print(f"\nRefresh Token:\n{refresh_token}\n")
    print("Next steps:")
    print("1. Store this token securely (it won't be shown again)")
    print("2. Add it to Databricks secrets:")
    print(
        "   databricks secrets put-secret tesla-lease-tracker tesla-refresh-token"
    )
    print("3. Paste the refresh token when prompted\n")


if __name__ == "__main__":
    main()
