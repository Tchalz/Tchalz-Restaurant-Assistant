import json
import os
import random
import sqlite3

DB_PATH = os.path.join("data", "tchalz_business.sqlite")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_column(conn, table, column, coltype):
    """Adds a column to an existing table if it isn't already there (simple migration)."""
    cols = [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")
        conn.commit()


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            name TEXT,
            date TEXT,
            time TEXT,
            party_size INTEGER,
            contact TEXT,
            status TEXT DEFAULT 'confirmed'
        )
    """)
    _ensure_column(conn, "reservations", "session_id", "TEXT")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            items TEXT,
            order_type TEXT,
            contact TEXT,
            status TEXT,
            eta TEXT,
            subtotal REAL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS waitlist (
            id TEXT PRIMARY KEY,
            name TEXT,
            date TEXT,
            time TEXT,
            party_size INTEGER,
            contact TEXT,
            status TEXT DEFAULT 'waiting'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cart_items (
            session_id TEXT,
            item_name TEXT,
            quantity INTEGER,
            modifiers TEXT,
            unit_price REAL
        )
    """)
    conn.commit()
    conn.close()


# ---- Reservations ----

def create_reservation(name, date, time, party_size, contact, session_id=None):
    conn = get_connection()
    res_id = f"RES{random.randint(1000, 9999)}"
    conn.execute(
        "INSERT INTO reservations (id, session_id, name, date, time, party_size, contact, status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, 'confirmed')",
        (res_id, session_id, name, date, time, party_size, contact),
    )
    conn.commit()
    conn.close()
    return res_id


def get_reservation_by_session(session_id):
    """Returns the most recently touched reservation for a chat session, or None."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM reservations WHERE session_id = ? ORDER BY rowid DESC LIMIT 1",
        (session_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_reservation(res_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM reservations WHERE id = ?", (res_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_reservation(res_id, **fields):
    if not fields:
        return
    conn = get_connection()
    sets = ", ".join(f"{k} = ?" for k in fields)
    conn.execute(f"UPDATE reservations SET {sets} WHERE id = ?", (*fields.values(), res_id))
    conn.commit()
    conn.close()


def delete_reservation(res_id):
    conn = get_connection()
    conn.execute("DELETE FROM reservations WHERE id = ?", (res_id,))
    conn.commit()
    conn.close()


# ---- Orders ----

def create_order(items, order_type, contact, eta):
    conn = get_connection()
    order_id = f"ORD{random.randint(1000, 9999)}"
    subtotal = sum(i["unit_price"] * i["quantity"] for i in items)
    conn.execute(
        "INSERT INTO orders (id, items, order_type, contact, status, eta, subtotal) "
        "VALUES (?, ?, ?, ?, 'preparing', ?, ?)",
        (order_id, json.dumps(items), order_type, contact, eta, subtotal),
    )
    conn.commit()
    conn.close()
    return order_id, subtotal


def get_order(order_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    conn.close()
    if not row:
        return None
    data = dict(row)
    data["items"] = json.loads(data["items"])
    return data


# ---- Waitlist ----

def add_to_waitlist(name, date, time, party_size, contact):
    conn = get_connection()
    waitlist_id = f"WL{random.randint(1000, 9999)}"
    conn.execute(
        "INSERT INTO waitlist (id, name, date, time, party_size, contact, status) "
        "VALUES (?, ?, ?, ?, ?, ?, 'waiting')",
        (waitlist_id, name, date, time, party_size, contact),
    )
    conn.commit()
    conn.close()
    return waitlist_id


# ---- Cart ----

def get_cart(session_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT rowid, * FROM cart_items WHERE session_id = ?", (session_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_cart_item(session_id, item_name, quantity, modifiers, unit_price):
    conn = get_connection()
    conn.execute(
        "INSERT INTO cart_items (session_id, item_name, quantity, modifiers, unit_price) "
        "VALUES (?, ?, ?, ?, ?)",
        (session_id, item_name, quantity, json.dumps(modifiers), unit_price),
    )
    conn.commit()
    conn.close()


def clear_cart(session_id):
    conn = get_connection()
    conn.execute("DELETE FROM cart_items WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()


init_db()
