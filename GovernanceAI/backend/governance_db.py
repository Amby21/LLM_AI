import sqlite3
import json
from datetime import datetime
from backend.config import DATABASE_PATH

def get_connection():
    """ Creates and returns a connection to the SQLite database.
    check_same_thread=False is needed for FastAPI """
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def initialise_database():
    """Creates all tables if they don't already exist """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_assets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            asset_type  TEXT NOT NULL,
            domain      TEXT,
            owner       TEXT,
            sensitivity TEXT,
            description TEXT,
            tags        TEXT,
            created_at  TEXT DEFAULT (datetime('now')),
            updated_at  TEXT DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lineage_edges (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            source_asset_id  INTEGER NOT NULL,
            target_asset_id  INTEGER NOT NULL,
            relationship     TEXT,
            created_at       TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (source_asset_id) REFERENCES data_assets(id),
            FOREIGN KEY (target_asset_id) REFERENCES data_assets(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quality_rules (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id          INTEGER NOT NULL,
            column_name       TEXT,
            rule_type         TEXT,
            rule_definition   TEXT,
            sql_expression    TEXT,
            created_by_agent  INTEGER DEFAULT 1,
            created_at        TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (asset_id) REFERENCES data_assets(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_query      TEXT NOT NULL,
            agent_action    TEXT NOT NULL,
            assets_touched  TEXT,
            result_summary  TEXT,
            full_response   TEXT,
            timestamp       TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()
    print(f"✅ Database initialised at {DATABASE_PATH}")


def create_asset(name, asset_type, domain=None, owner=None, sensitivity=None, description=None, tags=None):
    conn = get_connection()
    cursor = conn.cursor()
    tags_json = json.dumps(tags) if tags else "[]"
    cursor.execute("""INSERT INTO data_assets
                   (name, asset_type, domain, owner, sensitivity, description, tags)
                   VALUES (?,?,?,?,?,?,?)""",
                   (name, asset_type, domain, owner, sensitivity, description, tags_json))
    asset_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return asset_id


def get_all_assets():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM data_assets ORDER BY domain, name")
    rows = cursor.fetchall()
    conn.close()
    assets = []
    for row in rows:
        asset = dict(row)
        asset["tags"] = json.loads(asset["tags"] or "[]")
        assets.append(asset)
    return assets


def get_asset_by_id(asset_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM data_assets WHERE id = ?", (asset_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        asset = dict(row)
        asset["tags"] = json.loads(asset["tags"] or "[]")
        return asset
    return None


def get_assets_by_domain(domain):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM data_assets WHERE LOWER(domain) = LOWER(?)", (domain,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_unowned_assets():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM data_assets WHERE owner IS NULL OR owner = ''")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_assets(query):
    conn = get_connection()
    cursor = conn.cursor()
    like = f"%{query}%"
    cursor.execute("""SELECT * FROM data_assets
                   WHERE name LIKE ? OR description LIKE ? OR domain LIKE ?
                   ORDER BY name""", (like, like, like))
    rows = cursor.fetchall()
    conn.close()
    assets = []
    for row in rows:
        asset = dict(row)
        asset["tags"] = json.loads(asset["tags"] or "[]")
        assets.append(asset)
    return assets


def update_asset(asset_id, **kwargs):
    if not kwargs:
        return False
    conn = get_connection()
    cursor = conn.cursor()
    set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values())
    values.append(datetime.now().isoformat())
    values.append(asset_id)
    cursor.execute(f"UPDATE data_assets SET {set_clause}, updated_at = ? WHERE id = ?", values)
    conn.commit()
    conn.close()
    return True


def add_lineage_edge(source_id, target_id, relationship="feeds_into"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO lineage_edges (source_asset_id, target_asset_id, relationship)
        VALUES (?, ?, ?)
    """, (source_id, target_id, relationship))
    conn.commit()
    conn.close()


def get_lineage_for_asset(asset_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT da.*, le.relationship
        FROM lineage_edges le
        JOIN data_assets da ON le.source_asset_id = da.id
        WHERE le.target_asset_id = ?
    """, (asset_id,))
    upstream = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT da.*, le.relationship
        FROM lineage_edges le
        JOIN data_assets da ON le.target_asset_id = da.id
        WHERE le.source_asset_id = ?
    """, (asset_id,))
    downstream = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"upstream": upstream, "downstream": downstream}


def add_quality_rule(asset_id, column_name, rule_type, rule_definition, sql_expression=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO quality_rules
            (asset_id, column_name, rule_type, rule_definition, sql_expression)
        VALUES (?, ?, ?, ?, ?)
    """, (asset_id, column_name, rule_type, rule_definition, sql_expression))
    rule_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return rule_id


def get_rules_for_asset(asset_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM quality_rules WHERE asset_id = ? ORDER BY column_name",
        (asset_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def log_audit(user_query, agent_action, assets_touched=None, result_summary=None, full_response=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_log
            (user_query, agent_action, assets_touched, result_summary, full_response)
        VALUES (?, ?, ?, ?, ?)
    """, (
        user_query,
        agent_action,
        json.dumps(assets_touched or []),
        result_summary,
        full_response
    ))
    conn.commit()
    conn.close()


def get_audit_log(limit=50):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM audit_log
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
