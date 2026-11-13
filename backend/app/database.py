import sqlite3
from contextlib import contextmanager
from typing import Generator
from app.config import DB_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            company TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'Stakeholder',
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deals (
            id TEXT PRIMARY KEY,
            contact_id TEXT NOT NULL,
            title TEXT NOT NULL,
            value REAL NOT NULL,
            stage TEXT NOT NULL CHECK(stage IN ('qualified', 'meeting', 'proposal', 'negotiation', 'closed_won', 'closed_lost')),
            probability INTEGER NOT NULL,
            expected_close TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id TEXT PRIMARY KEY,
            deal_id TEXT,
            contact_id TEXT NOT NULL,
            activity_type TEXT NOT NULL CHECK(activity_type IN ('call', 'meeting', 'email', 'note')),
            notes TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (deal_id) REFERENCES deals (id) ON DELETE CASCADE,
            FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE CASCADE
        )
    """)

    conn.commit()

    # Seed initial demo pipeline if empty
    cursor.execute("SELECT count(*) FROM contacts")
    if cursor.fetchone()[0] == 0:
        seed_data(cursor)
        conn.commit()

    conn.close()

def seed_data(cursor: sqlite3.Cursor):
    # Contacts
    contacts = [
        ("ct-1", "Elena Rostova", "elena@vanguard-logistics.com", "Vanguard Logistics", "Chief Information Officer", "+1 415-555-0192"),
        ("ct-2", "Marcus Chen", "marcus.c@apexfintech.io", "Apex FinTech", "VP of Engineering", "+1 212-555-0144"),
        ("ct-3", "Sarah Jenkins", "s.jenkins@cloudgrid.org", "CloudGrid Solutions", "Head of Infrastructure", "+1 312-555-0188")
    ]
    for c in contacts:
        cursor.execute("INSERT INTO contacts (id, name, email, company, role, phone) VALUES (?, ?, ?, ?, ?, ?)", c)

    # Deals
    deals = [
        ("deal-1", "ct-1", "Enterprise Cloud Migration & Fleet Telematics", 120000.0, "negotiation", 80, "2026-12-15"),
        ("deal-2", "ct-2", "Zero-Trust API Gateway Deployment", 75000.0, "proposal", 60, "2026-11-30"),
        ("deal-3", "ct-3", "Multi-Tenant Observability Pipeline", 45000.0, "meeting", 35, "2027-01-20"),
        ("deal-4", "ct-1", "Automated Security Audit & Compliance License", 35000.0, "closed_won", 100, "2026-10-15")
    ]
    for d in deals:
        cursor.execute("INSERT INTO deals (id, contact_id, title, value, stage, probability, expected_close) VALUES (?, ?, ?, ?, ?, ?, ?)", d)

    # Activities
    activities = [
        ("act-1", "deal-1", "ct-1", "call", "Reviewed security compliance addendum with legal team. Awaiting contract sign-off."),
        ("act-2", "deal-2", "ct-2", "meeting", "Architecture walkthrough covering latency benchmarks and rate-limiting quotas."),
        ("act-3", "deal-4", "ct-1", "email", "Received signed enterprise contract for annual compliance license.")
    ]
    for a in activities:
        cursor.execute("INSERT INTO activities (id, deal_id, contact_id, activity_type, notes) VALUES (?, ?, ?, ?, ?)", a)

@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
