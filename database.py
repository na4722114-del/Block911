"""SQLite persistence layer for Block911."""

import json
import os
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional

DB_PATH = os.environ.get("BLOCK911_DB", os.path.join(os.path.dirname(__file__), "block911.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    id TEXT UNIQUE NOT NULL,
    customer_id TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    email TEXT NOT NULL,
    amount REAL NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    method TEXT NOT NULL,
    card_bin TEXT NOT NULL,
    location TEXT NOT NULL,
    ip_address TEXT NOT NULL,
    device_id TEXT NOT NULL,
    risk_score INTEGER NOT NULL,
    status TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    heuristics TEXT NOT NULL DEFAULT '[]',
    investigation_status TEXT NOT NULL,
    analyst_notes TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS blacklist (email TEXT PRIMARY KEY, added_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS graph_nodes (
    id TEXT PRIMARY KEY, type TEXT NOT NULL, code TEXT, risk INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS graph_edges (
    source TEXT NOT NULL, target TEXT NOT NULL, relation TEXT NOT NULL,
    PRIMARY KEY (source, target, relation)
);
"""

SEED_TRANSACTIONS = [
    (
        "TXN-8938",
        "CUST-9102",
        "Vikram Malhotra",
        "vikram.malhotra84@proton.me",
        890.00,
        "Credit Card",
        "453291",
        "Delhi NCR, India",
        "203.0.113.5",
        "DEV-F921-IN",
        92,
        "Declined",
        "2026-11-12 10:35:10",
        ["Shared device across multiple BINs", "Syndicate pattern"],
        "Open Triage",
    ),
    (
        "TXN-8940",
        "CUST-4412",
        "Rahul Mehta",
        "rahul.mehta92@gmail.com",
        3250.00,
        "UPI / NetBanking",
        "510510",
        "Bengaluru, Karnataka",
        "192.0.2.42",
        "DEV-B811-IN",
        48,
        "Challenged",
        "2026-11-12 10:38:45",
        ["High ticket amount (4x baseline)", "New IP subnet"],
        "Challenged (3DS OTP Pending)",
    ),
    (
        "TXN-8941",
        "CUST-3819",
        "Priya Nair",
        "priya.nair@gmail.com",
        79.50,
        "UPI / Google Pay",
        "411111",
        "Mumbai, Maharashtra",
        "198.51.100.11",
        "DEV-A310-IN",
        12,
        "Approved",
        "2026-11-12 10:41:02",
        ["Verified biometric token", "Domestic card & IP match"],
        "Safe",
    ),
    (
        "TXN-8942",
        "CUST-9102",
        "Vikram Malhotra",
        "vikram.malhotra84@proton.me",
        1480.00,
        "Credit Card",
        "453291",
        "Delhi NCR, India",
        "203.0.113.5",
        "DEV-F921-IN",
        89,
        "Declined",
        "2026-11-12 10:42:19",
        ["Proxy / Tor node detected", "Velocity: 7 txns / 3 mins", "Billing / IP geo mismatch"],
        "Open Triage",
    ),
]

SEED_NODES = [
    ("Vikram Malhotra", "Customer", "CUST-9102", 92),
    ("Rohan Kulkarni", "Customer", "CUST-9108", 88),
    ("Kabir Deshmukh", "Customer", "CUST-9114", 78),
    ("DEV-F921-IN", "Device", "Canvas FP #F921", 95),
    ("203.0.113.5", "IP Address", "Tor Exit Node", 99),
    ("BIN:453291", "Card BIN", "HDFC Compromised Batch", 85),
    ("BIN:510510", "Card BIN", "Prepaid RuPay/MC", 65),
]

SEED_EDGES = [
    ("Vikram Malhotra", "DEV-F921-IN", "Shared Device"),
    ("Rohan Kulkarni", "DEV-F921-IN", "Shared Device"),
    ("Kabir Deshmukh", "DEV-F921-IN", "Canvas Fingerprint Link"),
    ("DEV-F921-IN", "203.0.113.5", "Connected via VPN/Tor"),
    ("Vikram Malhotra", "BIN:453291", "Used Card"),
    ("Rohan Kulkarni", "BIN:453291", "Reused Card"),
    ("Kabir Deshmukh", "BIN:510510", "Card Velocity"),
]


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create tables and load seed data the first time only."""
    with connect() as conn:
        conn.executescript(SCHEMA)
        if conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0] == 0:
            for t in SEED_TRANSACTIONS:
                conn.execute(
                    """INSERT INTO transactions (id, customer_id, customer_name, email, amount,
                       method, card_bin, location, ip_address, device_id, risk_score, status,
                       timestamp, heuristics, investigation_status)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (*t[:13], json.dumps(t[13]), t[14]),
                )
            conn.executemany("INSERT INTO graph_nodes VALUES (?,?,?,?)", SEED_NODES)
            conn.executemany("INSERT INTO graph_edges VALUES (?,?,?)", SEED_EDGES)


def row_to_txn(row: sqlite3.Row) -> Dict[str, Any]:
    d = dict(row)
    d.pop("seq", None)
    d["heuristics"] = json.loads(d["heuristics"])
    return d


def next_txn_number(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT MAX(CAST(SUBSTR(id, 5) AS INTEGER)) FROM transactions").fetchone()
    return max(row[0] or 8942, 8942) + 1


def get_blacklist(conn: sqlite3.Connection) -> List[str]:
    return [r["email"] for r in conn.execute("SELECT email FROM blacklist ORDER BY added_at")]


def get_txn(conn: sqlite3.Connection, txn_id: str) -> Optional[Dict[str, Any]]:
    row = conn.execute("SELECT * FROM transactions WHERE id = ?", (txn_id,)).fetchone()
    return row_to_txn(row) if row else None