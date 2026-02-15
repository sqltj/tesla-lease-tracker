#!/usr/bin/env python3
"""Register Tesla Fleet API account for this deployment.

This is a one-time setup step that must be completed before syncing Tesla data.
It registers your deployed app's domain with Tesla's Fleet API.

Usage:
    uv run python scripts/register_fleet_api.py

Prerequisites:
    1. Deploy the app to Databricks: uv run apx build && databricks bundle deploy
    2. Generate key pair: openssl ecparam -name prime256v1 -genkey -noout -out private-key.pem
    3. Host public key at: https://<your-domain>/.well-known/appspecific/com.tesla.3p.public-key.pem
    4. Set allowed_origins in Tesla Developer Console to your domain
    5. Run this script
"""

import argparse
import sys
import os
import json
import time
from pathlib import Path

import requests
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.compute import GetConfigResponse


def get_partner_token(client_id: str, client_secret: str, region: str) -> str:
    """Get partner authentication token from Tesla."""
    print(f"\n1. Requesting partner token for region: {region}")

    audience = f"https://fleet-api.prd.{region}.vn.cloud.tesla.com"

    try:
        response = requests.post(
            "https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token",
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "openid vehicle_device_data",
                "audience": audience,
            },
            timeout=10,
        )

        if response.status_code != 200:
            print(f"   ❌ Failed to get token: {response.text}")
            sys.exit(1)

        token = response.json()["access_token"]
        expires_in = response.json()["expires_in"]
        print(f"   ✓ Token received (valid for {expires_in // 3600} hours)")
        return token

    except Exception as e:
        print(f"   ❌ Error: {e}")
        sys.exit(1)


def load_public_key() -> str:
    """Load public key from file."""
    key_path = Path("public-key.pem")

    if not key_path.exists():
        print("\n❌ Error: public-key.pem not found")
        print("   Generate it with:")
        print("   openssl ecparam -name prime256v1 -genkey -noout -out private-key.pem")
        print("   openssl ec -in private-key.pem -pubout -out public-key.pem")
        sys.exit(1)

    print("\n2. Loading public key from public-key.pem")
    public_key = key_path.read_text()
    print("   ✓ Public key loaded")
    return public_key


def register_with_tesla(
    partner_token: str, domain: str, public_key: str, region: str
) -> None:
    """Register domain with Tesla Fleet API."""
    print(f"\n3. Registering domain with Tesla Fleet API")
    print(f"   Domain: {domain}")
    print(f"   Region: {region}")

    fleet_api_url = f"https://fleet-api.prd.{region}.vn.cloud.tesla.com"

    try:
        response = requests.post(
            f"{fleet_api_url}/api/1/partner_accounts",
            headers={
                "Authorization": f"Bearer {partner_token}",
                "Content-Type": "application/json",
            },
            json={"domain": domain, "public_key": public_key},
            timeout=10,
        )

        if response.status_code == 200:
            print("   ✓ Registration request submitted successfully!")
            print("\n" + "=" * 60)
            print("✅ Fleet API Registration Complete!")
            print("=" * 60)
            print(f"\nDomain registered: {domain}")
            print(f"Region: {region}")
            print("\n📋 Next steps:")
            print("   1. Wait for Tesla approval (typically 1-24 hours)")
            print("   2. Check your email for confirmation")
            print("   3. Once approved, sync will work in the app")
            print("\n💡 Tip: You can test the app locally with sample data:")
            print("   uv run python scripts/seed_local.py")
            return

        # Handle errors
        try:
            error_data = response.json()
            error_msg = error_data.get("error", response.text)
        except:
            error_msg = response.text

        print(f"   ❌ Registration failed ({response.status_code})")
        print(f"   Error: {error_msg}")

        if response.status_code == 400:
            print("\n   Common causes:")
            print("   - Domain not in allowed_origins on developer.tesla.com")
            print("   - Public key not hosted at the well-known location")
            print("   - Invalid domain format")

        sys.exit(1)

    except Exception as e:
        print(f"   ❌ Error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Register Tesla Fleet API account")
    parser.add_argument(
        "--domain",
        required=True,
        help="Your deployed domain (e.g., dbc-xxx.cloud.databricks.com/apps/tesla-lease-tracker)",
    )
    parser.add_argument(
        "--region",
        default="na",
        choices=["na", "eu", "cn"],
        help="Tesla Fleet API region (default: na)",
    )
    parser.add_argument(
        "--client-id",
        help="Tesla OAuth client ID (reads from Databricks secrets if not provided)",
    )
    parser.add_argument(
        "--client-secret",
        help="Tesla OAuth client secret (reads from Databricks secrets if not provided)",
    )

    args = parser.parse_args()

    print("\n🔧 Tesla Fleet API Registration")
    print("=" * 60)

    # Get credentials
    if args.client_id and args.client_secret:
        client_id = args.client_id
        client_secret = args.client_secret
        print(f"\nUsing provided credentials")
    else:
        print(f"\nReading Tesla credentials from Databricks secrets...")
        try:
            ws = WorkspaceClient()
            client_id = ws.secrets.get_secret("tesla-lease-tracker", "tesla-client-id").value
            client_secret = ws.secrets.get_secret(
                "tesla-lease-tracker", "tesla-client-secret"
            ).value

            import base64

            client_id = base64.b64decode(client_id).decode("utf-8")
            client_secret = base64.b64decode(client_secret).decode("utf-8")
            print("   ✓ Credentials loaded from Databricks secrets")
        except Exception as e:
            print(f"\n❌ Could not read from Databricks secrets: {e}")
            print("\nProvide credentials manually:")
            print("   uv run python scripts/register_fleet_api.py \\")
            print("     --domain your-domain \\")
            print("     --client-id YOUR_CLIENT_ID \\")
            print("     --client-secret YOUR_CLIENT_SECRET")
            sys.exit(1)

    # Get partner token
    partner_token = get_partner_token(client_id, client_secret, args.region)

    # Load public key
    public_key = load_public_key()

    # Register with Tesla
    register_with_tesla(partner_token, args.domain, public_key, args.region)


if __name__ == "__main__":
    main()
