import sqlite3

DB_FILE = "app_data.db"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, session_id INTEGER, role TEXT, content TEXT)')

def login_user(u, p):
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("SELECT id, username FROM users WHERE username=? AND password=?", (u, p)).fetchone()

def create_user(u, p):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (u, p))
            return True
    except: return False

def create_session(user_id, title="New Chat"):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO sessions (user_id, title) VALUES (?, ?)", (user_id, title))
        return c.lastrowid

def get_sessions(user_id):
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("SELECT id, title FROM sessions WHERE user_id=? ORDER BY id DESC", (user_id,)).fetchall()

def save_message(session_id, role, content):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)", (session_id, role, content))
        # Rename "New Chat" to the first user question
        if role == "user":
            conn.execute("UPDATE sessions SET title = ? WHERE id = ? AND title = 'New Chat'", (content[:25], session_id))

def get_history(session_id):
    with sqlite3.connect(DB_FILE) as conn:
        return conn.execute("SELECT role, content FROM messages WHERE session_id=? ORDER BY id ASC", (session_id,)).fetchall()