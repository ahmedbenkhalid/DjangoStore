#!/usr/bin/env python
"""
Load seeding data into MariaDB database.
Run: python load_data.py
"""

import os
import pymysql
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def load_env():
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip()


def load_data():
    load_env()
    # Connect to MariaDB
    conn = pymysql.connect(
        host=os.environ.get("MYSQL_HOST", "127.0.0.1"),
        port=int(os.environ.get("MYSQL_PORT", 3306)),
        user=os.environ.get("MYSQL_USER", "root"),
        password=os.environ.get("MYSQL_PASSWORD", ""),
        charset="utf8mb4",
        autocommit=True,
    )

    sql_files = [
        ("Seeding Data", BASE_DIR / "data_seeding.sql"),
    ]

    with conn.cursor() as cursor:
        for name, sql_file in sql_files:
            if not sql_file.exists():
                print(f"⚠️  File not found: {sql_file}")
                continue

            print(f"📄 Loading {name}...")
            with open(sql_file, "r", encoding="utf-8") as f:
                sql_content = f.read()

            # Split by semicolon and execute each statement
            for statement in sql_content.split(";"):
                statement = statement.strip()
                if statement and not statement.startswith("--"):
                    try:
                        cursor.execute(statement)
                    except pymysql.err.OperationalError as e:
                        if "already exists" in str(e).lower():
                            continue  # Skip if table already exists
                        print(f"   ⚠️  {e}")
                    except Exception as e:
                        print(f"   ⚠️  {e}")

            print(f"   ✅ {name} loaded")

    conn.close()
    print("\n🎉 Data loaded successfully!")


if __name__ == "__main__":
    load_data()
