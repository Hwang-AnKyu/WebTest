#!/usr/bin/env python3
"""
Database setup script for AICOM.
Run this script to execute the schema SQL in Supabase.

Usage:
    1. Set SUPABASE_ACCESS_TOKEN environment variable (get from Supabase dashboard)
    2. Run: python setup_database.py

Or manually run supabase_schema.sql in Supabase SQL Editor.
"""

import os
import sys
import requests

PROJECT_REF = "yxemmeurskvpocxuickw"

def main():
    access_token = os.environ.get("SUPABASE_ACCESS_TOKEN")

    if not access_token:
        print("=" * 60)
        print("SUPABASE_ACCESS_TOKEN not set.")
        print()
        print("To set up the database, please do ONE of the following:")
        print()
        print("Option 1: Run SQL manually in Supabase Dashboard")
        print("-" * 60)
        print("1. Go to https://supabase.com/dashboard/project/yxemmeurskvpocxuickw")
        print("2. Navigate to SQL Editor")
        print("3. Copy and paste the contents of supabase_schema.sql")
        print("4. Click 'Run'")
        print()
        print("Option 2: Use Supabase CLI with access token")
        print("-" * 60)
        print("1. Get your access token from Supabase Dashboard > Account > Access Tokens")
        print("2. Set the environment variable:")
        print("   export SUPABASE_ACCESS_TOKEN=your_token_here")
        print("3. Run this script again")
        print("=" * 60)
        sys.exit(1)

    # Read the schema file
    schema_path = os.path.join(os.path.dirname(__file__), "supabase_schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    print("Executing schema SQL...")

    # Use Supabase Management API to execute SQL
    url = f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "query": schema_sql
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200 or response.status_code == 201:
            print("Schema executed successfully!")
            print("Database tables created.")
        else:
            print(f"Error executing schema: {response.status_code}")
            print(response.text)
            print()
            print("Please run the SQL manually in Supabase SQL Editor.")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        print("Please run the SQL manually in Supabase SQL Editor.")
        sys.exit(1)


if __name__ == "__main__":
    main()
