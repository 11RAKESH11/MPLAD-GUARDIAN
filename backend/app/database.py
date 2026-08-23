import sqlite3
import os

DB_PATH = os.getenv("DATABASE_PATH", r"c:\SIH_PROJECT\mplad.db")

def _get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=20.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Fast in-memory performance settings
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA cache_size = -64000;") # 64MB RAM cache
    conn.execute("PRAGMA temp_store = MEMORY;")
    conn.execute("PRAGMA mmap_size = 30000000000;")
    return conn

def get_db():
    conn = _get_connection()
    try:
        yield conn
    finally:
        conn.close()

def query_db(query, args=(), one=False):
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute(query, args)
    r = cur.fetchall()
    conn.close()
    return (r[0] if r else None) if one else r

def execute_db(query, args=()):
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute(query, args)
    conn.commit()
    conn.close()
