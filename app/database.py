
import sqlite3
import os

DB_PATH = "scanner.db"

class Database:
    def __init__(self, path: str = DB_PATH):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.init_db()

    def init_db(self):
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            target_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            status_code INTEGER,
            depth INTEGER DEFAULT 0,
            content_type TEXT,
            UNIQUE(project_id, url),
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS forms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_id INTEGER NOT NULL,
            action TEXT,
            method TEXT,
            FOREIGN KEY(page_id) REFERENCES pages(id)
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS inputs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            form_id INTEGER NOT NULL,
            name TEXT,
            type TEXT,
            value TEXT,
            FOREIGN KEY(form_id) REFERENCES forms(id)
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            method TEXT,
            url TEXT,
            payload TEXT,
            response_code INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
        """)

        self.conn.commit()

    def create_project(self, name: str, target_url: str) -> int:
        cur = self.conn.cursor()
        cur.execute("INSERT INTO projects(name, target_url) VALUES(?, ?)", (name, target_url))
        self.conn.commit()
        return cur.lastrowid

    def save_request(self, method: str, url: str, payload: str, response_code: int, project_id: int = None):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO requests(project_id, method, url, payload, response_code) VALUES(?,?,?,?,?)",
            (project_id, method, url, payload, response_code),
        )
        self.conn.commit()

    def upsert_page(self, project_id: int, url: str, status_code: int | None, depth: int, content_type: str | None) -> int:
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO pages(project_id, url, status_code, depth, content_type)
            VALUES(?,?,?,?,?)
            ON CONFLICT(project_id, url) DO UPDATE SET
              status_code=excluded.status_code,
              depth=MIN(pages.depth, excluded.depth),
              content_type=excluded.content_type
        """, (project_id, url, status_code, depth, content_type))
        self.conn.commit()
        cur.execute("SELECT id FROM pages WHERE project_id=? AND url=?", (project_id, url))
        row = cur.fetchone()
        return int(row["id"])

    def insert_form(self, page_id: int, action: str | None, method: str | None) -> int:
        cur = self.conn.cursor()
        cur.execute("INSERT INTO forms(page_id, action, method) VALUES(?,?,?)", (page_id, action, method))
        self.conn.commit()
        return cur.lastrowid

    def insert_input(self, form_id: int, name: str | None, type_: str | None, value: str | None):
        cur = self.conn.cursor()
        cur.execute("INSERT INTO inputs(form_id, name, type, value) VALUES(?,?,?,?)", (form_id, name, type_, value))
        self.conn.commit()

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass

def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        conn.close()
    Database(DB_PATH).close()
