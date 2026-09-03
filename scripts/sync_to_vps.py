#!/usr/bin/env python3
"""
Sync Local Configuration, Settings, Branding, and Database Data to VPS
Transfers all local SQLite records (provider configs, SMTP, API keys, Rayven branding,
companies, prospects, campaigns, leads, knowledge base RAG vectors) directly to VPS PostgreSQL.
"""

import json
import os
import sqlite3
import subprocess

VPS_HOST = "169.58.142.29"
VPS_USER = "root"
VPS_PATH = "/etc/dokploy/compose/reach-xghikw/code"
LOCAL_DB = "backend/reach.db"
LOCAL_ENV = ".env"


def run_ssh(cmd: str) -> str:
    full_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", f"{VPS_USER}@{VPS_HOST}", cmd]
    res = subprocess.run(full_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"SSH Error ({cmd}): {res.stderr}")
    return res.stdout


def sync_env_to_vps():
    print("🔄 Step 1: Syncing local .env secrets and keys to VPS...")
    if not os.path.exists(LOCAL_ENV):
        print("❌ Local .env file not found!")
        return

    with open(LOCAL_ENV) as f:
        env_content = f.read()

    # Write .env to VPS
    escaped_content = env_content.replace("'", "'\\''")
    run_ssh(f"cat << 'EOF' > {VPS_PATH}/.env\n{env_content}\nEOF")
    print("✅ .env file synced to VPS.")


def export_sqlite_to_postgres():
    print("🔄 Step 2: Extracting local settings, branding, knowledge base, and pipeline data...")
    if not os.path.exists(LOCAL_DB):
        print(f"❌ Local SQLite database ({LOCAL_DB}) not found!")
        return

    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    tables = [
        "users",
        "provider_configs",
        "companies",
        "prospects",
        "campaigns",
        "leads",
        "knowledge_documents",
        "knowledge_chunks",
        "discovery_jobs",
        "audit_logs",
        "email_templates",
        "suppressions",
    ]

    sql_statements = ["-- Reach Local Database Migration to VPS PostgreSQL --\n"]

    for table in tables:
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            if not columns:
                continue

            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            if not rows:
                continue

            # TRUNCATE / DELETE existing rows on VPS table to ensure clean state
            sql_statements.append(f"TRUNCATE TABLE {table} CASCADE;")

            cols_str = ", ".join([f'"{c}"' for c in columns])
            for row in rows:
                vals = []
                for val in row:
                    if val is None:
                        vals.append("NULL")
                    elif isinstance(val, bool):
                        vals.append("TRUE" if val else "FALSE")
                    elif isinstance(val, (int, float)):
                        vals.append(str(val))
                    else:
                        escaped = str(val).replace("'", "''")
                        vals.append(f"'{escaped}'")
                val_str = ", ".join(vals)
                sql_statements.append(f"INSERT INTO {table} ({cols_str}) VALUES ({val_str});")

            print(f"  ✓ Processed table '{table}': {len(rows)} rows.")
        except Exception as e:
            print(f"  ⚠ Skipping table {table}: {e}")

    conn.close()

    script_sql = "\n".join(sql_statements)
    temp_sql_file = "vps_data_dump.sql"
    with open(temp_sql_file, "w") as f:
        f.write(script_sql)

    print("🔄 Step 3: Importing local data into VPS PostgreSQL database...")
    # Copy SQL file to VPS and execute psql
    scp_cmd = ["scp", "-o", "StrictHostKeyChecking=no", temp_sql_file, f"{VPS_USER}@{VPS_HOST}:/tmp/vps_data_dump.sql"]
    subprocess.run(scp_cmd, check=True)

    import_cmd = (
        f"docker exec -i reach_postgres psql -U reach -d reach < /tmp/vps_data_dump.sql && rm /tmp/vps_data_dump.sql"
    )
    res_out = run_ssh(import_cmd)
    print(res_out)

    if os.path.exists(temp_sql_file):
        os.remove(temp_sql_file)

    print("✅ Database data successfully imported into VPS PostgreSQL.")


def restart_vps_services():
    print("🔄 Step 4: Restarting containers on VPS to apply synced settings & credentials...")
    restart_cmd = f"cd {VPS_PATH} && docker compose -p reach-xghikw -f ./docker-compose.yml restart backend worker frontend"
    run_ssh(restart_cmd)
    print("🚀 VPS Services restarted & synced!")


def main():
    print("=========================================================")
    print("⚡ Reach Local-to-VPS Configuration & Data Sync Utility")
    print("=========================================================")
    sync_env_to_vps()
    export_sqlite_to_postgres()
    restart_vps_services()
    print("\n🎉 ALL LOCAL SETTINGS, API KEYS, SMTP, BRANDING & DATA ARE NOW LIVE ON VPS!")


if __name__ == "__main__":
    main()
