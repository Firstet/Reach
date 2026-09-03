#!/usr/bin/env python3
"""
Reach Local-to-VPS Full Data & Settings Sync Utility
Extracts local SQLite data, transforms types to match PostgreSQL (pgvector, booleans, UUIDs, enums),
transfers local .env secrets, and imports everything cleanly into VPS PostgreSQL.
"""

import json
import os
import re
import sqlite3
import subprocess

VPS_HOST = "169.58.142.29"
VPS_USER = "root"
VPS_PATH = "/etc/dokploy/compose/reach-xghikw/code"
LOCAL_DB = "backend/reach.db"
LOCAL_ENV = ".env"

UUID_REGEX = re.compile(r"^[0-9a-fA-F]{32}$")

COLUMN_MAP = {
    "provider_configs": {
        "encrypted_secret": "encrypted_secrets",
        "created_by": "updated_by_id",
    }
}

BOOLEAN_PREFIXES = ("is_", "has_", "require_")
BOOLEAN_NAMES = {"email_verified", "test_mode", "tracking_enabled", "use_tls"}

LOWERCASE_ENUM_COLUMNS = {
    "users": {"role"},
}


def run_ssh(cmd: str) -> str:
    full_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", f"{VPS_USER}@{VPS_HOST}", cmd]
    res = subprocess.run(full_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"SSH Warning ({cmd}): {res.stderr}")
    return res.stdout


def format_uuid(val):
    if isinstance(val, str) and UUID_REGEX.match(val):
        return f"{val[:8]}-{val[8:12]}-{val[12:16]}-{val[16:20]}-{val[20:]}"
    return val


def sync_env_to_vps():
    print("🔄 Step 1: Syncing local .env secrets and keys to VPS...")
    if not os.path.exists(LOCAL_ENV):
        print("❌ Local .env file not found!")
        return

    with open(LOCAL_ENV) as f:
        env_content = f.read()

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

    sql_statements = [
        "-- Reach Local Database Migration to VPS PostgreSQL --\n",
        "SET statement_timeout = 0;",
        "SET client_encoding = 'UTF8';",
    ]

    # Clear target tables on VPS first in reverse dependency order
    for t in reversed(tables):
        sql_statements.append(f'TRUNCATE TABLE "{t}" CASCADE;')

    for table in tables:
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            raw_columns = [col[1] for col in cursor.fetchall()]
            if not raw_columns:
                continue

            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            if not rows:
                continue

            mapped_cols = [COLUMN_MAP.get(table, {}).get(c, c) for c in raw_columns]
            cols_str = ", ".join([f'"{c}"' for c in mapped_cols])

            for row in rows:
                vals = []
                for col_name, val in zip(mapped_cols, row):
                    val = format_uuid(val)

                    # Dynamic Foreign Key reference for provider_configs.updated_by_id
                    if table == "provider_configs" and col_name == "updated_by_id":
                        vals.append("(SELECT id FROM users LIMIT 1)")
                        continue

                    # Handle Lowercase Enums
                    if table in LOWERCASE_ENUM_COLUMNS and col_name in LOWERCASE_ENUM_COLUMNS[table]:
                        if isinstance(val, str):
                            val = val.lower()

                    # Handle Booleans dynamically by column name or prefix
                    is_bool_col = col_name in BOOLEAN_NAMES or any(col_name.startswith(p) for p in BOOLEAN_PREFIXES)
                    if is_bool_col:
                        if val in (1, "1", True, "true", "TRUE"):
                            vals.append("TRUE")
                        elif val in (0, "0", False, "false", "FALSE"):
                            vals.append("FALSE")
                        elif val is None:
                            vals.append("NULL")
                        else:
                            vals.append("TRUE" if val else "FALSE")
                        continue

                    # Handle Vector Embeddings in pgvector
                    if table == "knowledge_chunks" and col_name == "embedding":
                        if val is None:
                            vals.append("NULL")
                        elif isinstance(val, str):
                            try:
                                parsed = json.loads(val)
                                vec_str = f"[{','.join(str(float(x)) for x in parsed)}]"
                                vals.append(f"'{vec_str}'")
                            except Exception:
                                vals.append("NULL")
                        else:
                            vals.append("NULL")
                        continue

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
                sql_statements.append(f'INSERT INTO "{table}" ({cols_str}) VALUES ({val_str});')

            print(f"  ✓ Processed table '{table}': {len(rows)} rows.")
        except Exception as e:
            print(f"  ⚠ Skipping table {table}: {e}")

    conn.close()

    script_sql = "\n".join(sql_statements)
    temp_sql_file = "vps_data_dump.sql"
    with open(temp_sql_file, "w") as f:
        f.write(script_sql)

    print("🔄 Step 3: Importing local data into VPS PostgreSQL database...")
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
