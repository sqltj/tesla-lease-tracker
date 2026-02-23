"""
Refresh the Tesla OAuth refresh token stored in Databricks secrets.

Usage:
    uv run python scripts/refresh_tesla_token.py

Steps:
1. Starts a local HTTP server on port 8080 to capture the OAuth callback
2. Opens the Tesla login page in your browser
3. You log in and approve access — Tesla redirects back automatically
4. The script exchanges the code for new tokens
5. Stores the new refresh token in Databricks secrets
"""

import asyncio
import base64
import secrets
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Event, Thread

import aiohttp
from databricks.sdk import WorkspaceClient

SECRET_SCOPE = "tesla-lease-tracker"
REDIRECT_URI = "http://localhost:8080/callback"
SCOPES = "openid vehicle_device_data offline_access"
AUTH_URL = "https://auth.tesla.com/oauth2/v3/authorize"
TOKEN_URL = "https://auth.tesla.com/oauth2/v3/token"


def get_secret(ws: WorkspaceClient, key: str) -> str:
    resp = ws.secrets.get_secret(SECRET_SCOPE, key)
    if resp.value is None:
        raise ValueError(f"Secret {SECRET_SCOPE}/{key} has no value")
    return base64.b64decode(resp.value).decode("utf-8")


def put_secret(ws: WorkspaceClient, key: str, value: str) -> None:
    ws.secrets.put_secret(SECRET_SCOPE, key, string_value=value)


def wait_for_callback() -> str:
    """Start a local HTTP server, block until Tesla redirects back, return the code."""
    received = {}
    done = Event()

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            received["code"] = query.get("code", [None])[0]
            received["error"] = query.get("error", [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h2>Authorization received. You can close this tab.</h2>")
            done.set()

        def log_message(self, *args):
            pass  # suppress request logs

    server = HTTPServer(("localhost", 8080), CallbackHandler)
    thread = Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    print("Waiting for Tesla to redirect back to localhost:8080...")
    done.wait(timeout=120)
    server.shutdown()

    if received.get("error"):
        raise RuntimeError(f"Tesla returned an error: {received['error']}")
    if not received.get("code"):
        raise RuntimeError("Timed out waiting for callback (120s). Try again.")
    return received["code"]


async def exchange_code(client_id: str, client_secret: str, code: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            TOKEN_URL,
            json={
                "grant_type": "authorization_code",
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": REDIRECT_URI,
            },
        ) as resp:
            body = await resp.text()
            if resp.status != 200:
                raise RuntimeError(f"Token exchange failed ({resp.status}): {body}")
            return await resp.json()


async def main() -> None:
    ws = WorkspaceClient()
    client_id = get_secret(ws, "tesla-client-id")
    client_secret = get_secret(ws, "tesla-client-secret")

    state = secrets.token_urlsafe(16)
    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "state": state,
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    print("\n=== Tesla OAuth Token Refresh ===\n")
    print("Opening Tesla login in your browser...")
    print(f"\nIf it doesn't open, visit:\n{auth_url}\n")
    webbrowser.open(auth_url)

    code = wait_for_callback()

    print("\nExchanging code for tokens...")
    token_data = await exchange_code(client_id, client_secret, code)

    refresh_token = token_data.get("refresh_token")
    if not refresh_token:
        raise ValueError(f"No refresh_token in response: {token_data}")

    print("Storing new refresh token in Databricks secrets...")
    put_secret(ws, "tesla-refresh-token", refresh_token)

    print("\n✓ Done! New refresh token stored in Databricks secrets.")
    print("Restart the dev server: uv run apx dev restart\n")


if __name__ == "__main__":
    asyncio.run(main())
