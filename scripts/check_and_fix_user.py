#!/usr/bin/env python3
"""Quick script to check user status and fix password hash."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import bcrypt
from sqlalchemy import create_engine, text

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

engine = create_engine(database_url)

print("=" * 60)
print("AZALS - User Check and Password Fix")
print("=" * 60)

# Generate valid hash
password = "admin123"
salt = bcrypt.gensalt()
new_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

print(f"\nNew hash for 'admin123': {new_hash}")

# Verify hash works
verify = bcrypt.checkpw(password.encode('utf-8'), new_hash.encode('utf-8'))
print(f"Hash verification: {verify}")

with engine.connect() as conn:
    # Check all users
    result = conn.execute(text("SELECT id, email, tenant_id, role, is_active, LEFT(password_hash, 40) as hash FROM users"))
    rows = result.fetchall()

    print(f"\n{'='*60}")
    print(f"USERS IN DATABASE: {len(rows)}")
    print(f"{'='*60}")

    for row in rows:
        print(f"\n  ID: {row[0]}")
        print(f"  Email: {row[1]}")
        print(f"  Tenant: {row[2]}")
        print(f"  Role: {row[3]}")
        print(f"  Active: {row[4]}")
        print(f"  Hash: {row[5]}...")

    if len(rows) == 0:
        print("\n[WARNING] No users found! Creating admin user...")

        # Insert new user
        conn.execute(text("""
            INSERT INTO users (id, email, password_hash, tenant_id, role, is_active, totp_enabled, must_change_password, created_at, updated_at)
            VALUES (gen_random_uuid(), 'admin@azals.local', :hash, 'masith', 'DIRIGEANT', 1, 0, 0, NOW(), NOW())
        """), {"hash": new_hash})
        conn.commit()
        print("[OK] Admin user created with tenant_id='masith'")
    else:
        # Update existing user(s)
        print(f"\n{'='*60}")
        print("UPDATING PASSWORD HASH...")
        print(f"{'='*60}")

        conn.execute(text("""
            UPDATE users SET
                password_hash = :hash,
                tenant_id = 'masith',
                is_active = 1,
                totp_enabled = 0,
                must_change_password = 0,
                updated_at = NOW()
            WHERE email = 'admin@azals.local'
        """), {"hash": new_hash})
        conn.commit()
        print("[OK] Password hash and tenant_id updated to 'masith'")

    # Verify final state
    result = conn.execute(text("SELECT id, email, tenant_id, password_hash FROM users WHERE email = 'admin@azals.local'"))
    user = result.fetchone()

    if user:
        print(f"\n{'='*60}")
        print("FINAL VERIFICATION")
        print(f"{'='*60}")
        print(f"User ID: {user[0]}")
        print(f"Email: {user[1]}")
        print(f"Tenant: {user[2]}")

        # Test password verification
        test_verify = bcrypt.checkpw(b"admin123", user[3].encode('utf-8'))
        print(f"Password 'admin123' verification: {test_verify}")

        if test_verify:
            print(f"\n{'='*60}")
            print("SUCCESS! Login with:")
            print(f"  Organisation: {user[2]}")
            print(f"  Email: {user[1]}")
            print(f"  Password: admin123")
            print(f"{'='*60}")
