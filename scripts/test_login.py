#!/usr/bin/env python3
"""Test login API directly."""
import requests
import json

API_URL = "http://localhost:8000"

def test_login():
    print("=" * 60)
    print("TEST LOGIN API")
    print("=" * 60)

    # Test data
    data = {
        "email": "admin@azals.local",
        "password": "admin123"
    }

    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": "masith"
    }

    print(f"\nURL: {API_URL}/auth/login")
    print(f"Headers: {headers}")
    print(f"Body: {json.dumps(data, indent=2)}")

    try:
        response = requests.post(
            f"{API_URL}/auth/login",
            json=data,
            headers=headers
        )

        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")

        try:
            resp_json = response.json()
            print(f"\nResponse Body:")
            print(json.dumps(resp_json, indent=2, ensure_ascii=False))
        except (json.JSONDecodeError, ValueError):
            print(f"\nResponse Text: {response.text}")

        if response.status_code == 200:
            print("\n[SUCCESS] Login successful!")
        elif response.status_code == 422:
            print("\n[ERROR] 422 Validation Error - Check the 'details' field above")
        elif response.status_code == 401:
            print("\n[ERROR] 401 Unauthorized - Wrong credentials")
        else:
            print(f"\n[ERROR] Unexpected status code: {response.status_code}")

    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Cannot connect to API. Is the server running?")
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_login()
