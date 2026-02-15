#!/usr/bin/env python3
"""Get Tesla refresh token via OAuth flow.

This script walks you through the Tesla OAuth authorization flow to obtain
an initial refresh token that can be stored in Databricks secrets.

Usage:
    uv run python scripts/get_tesla_refresh_token.py --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
"""

import argparse
import sys
import webbrowser
from urllib.parse import urlencode, parse_qs, urlparse

import requests


def get_tesla_refresh_token(client_id: str, client_secret: str) -> str:
    """Guide user through OAuth flow and return refresh token."""

    # Step 1: Build authorization URL
    auth_params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": "http://localhost:8080/callback",
        "scope": "openid email offline_access",
        "state": "tesla-lease-tracker",
    }
    auth_url = f"https://auth.tesla.com/oauth2/v3/authorize?{urlencode(auth_params)}"

    print("\n🔐 Tesla OAuth Authorization Flow")
    print("=" * 50)
    print("\n1. Opening Tesla authorization page...")
    print(f"   URL: {auth_url}\n")

    # Try to open in browser
    try:
        webbrowser.open(auth_url)
        print("   ✓ Opened in browser")
    except Exception as e:
        print(f"   ⚠️  Could not open browser: {e}")
        print(f"   Please visit manually: {auth_url}")

    print("\n2. Authorize the application in your browser")
    print("   You'll be redirected to http://localhost:8080/callback?code=...")

    # Step 2: Get authorization code from user
    callback_url = input("\n3. Paste the full redirect URL here: ").strip()

    # Parse authorization code from callback URL
    try:
        parsed = urlparse(callback_url)
        params = parse_qs(parsed.query)
        code = params.get("code", [None])[0]

        if not code:
            print("❌ No authorization code found in URL")
            sys.exit(1)

        print(f"   ✓ Got authorization code: {code[:20]}...")
    except Exception as e:
        print(f"❌ Failed to parse URL: {e}")
        sys.exit(1)

    # Step 3: Exchange authorization code for tokens
    print("\n4. Exchanging code for tokens...")

    try:
        token_response = requests.post(
            "https://auth.tesla.com/oauth2/v3/token",
            json={
                "grant_type": "authorization_code",
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": "http://localhost:8080/callback",
            },
            timeout=10,
        )

        if token_response.status_code != 200:
            print(f"❌ Token exchange failed: {token_response.text}")
            sys.exit(1)

        tokens = token_response.json()
        refresh_token = tokens.get("refresh_token")

        if not refresh_token:
            print("❌ No refresh token in response")
            print(f"Response: {tokens}")
            sys.exit(1)

        print("   ✓ Token exchange successful!")

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        sys.exit(1)

    return refresh_token


def main():
    parser = argparse.ArgumentParser(
        description="Get Tesla refresh token via OAuth flow"
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

    try:
        refresh_token = get_tesla_refresh_token(args.client_id, args.client_secret)

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

    except KeyboardInterrupt:
        print("\n❌ Cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
