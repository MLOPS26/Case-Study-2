import duckdb
import uuid
from datetime import datetime
from typing import Optional
import os

from backend.utils.consts import DB_PATH
from backend.datamodels.datamodels import User


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.con = None

    def connect(self):
        if os.path.dirname(self.db_path):
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.con = duckdb.connect(self.db_path)

    def close(self):
        if self.con:
            self.con.close()
            self.con = None

    def initialize_db(self):
        if not self.con:
            self.connect()

        self.con.execute("""
            CREATE TABLE IF NOT EXISTS users (
                uuid VARCHAR PRIMARY KEY,
                email VARCHAR UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.con.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id UUID PRIMARY KEY,
                user_uuid VARCHAR,
                question VARCHAR,
                image_url VARCHAR,
                response VARCHAR,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_uuid) REFERENCES users(uuid)
            )
        """)

    def add_user(self, user: User):
        if not self.con:
            self.connect()

        try:
            self.con.execute(
                """
                INSERT INTO users (uuid, email) VALUES (?, ?)
            """,
                (user.uuid, user.email),
            )
            return True
        except duckdb.ConstraintException:
            return False

    def get_user(self, user_uuid: str) -> Optional[User]:
        if not self.con:
            self.connect()

        result = self.con.execute(
            """
            SELECT uuid, email FROM users WHERE uuid = ?
        """,
            (user_uuid,),
        ).fetchone()

        if result:
            return User(uuid=result[0], email=result[1])
        return None

    def add_history_entry(
        self,
        user_uuid: str,
        question: str,
        response: str,
        image_url: Optional[str] = None,
    ):
        if not self.con:
            self.connect()

        entry_id = uuid.uuid4()
        self.con.execute(
            """
            INSERT INTO history (id, user_uuid, question, image_url, response, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (entry_id, user_uuid, question, image_url, response, datetime.now()),
        )
        return entry_id

    def get_user_history(self, user_uuid: str, limit: int = 50):
        if not self.con:
            self.connect()

        results = self.con.execute(
            """
            SELECT id, question, image_url, response, timestamp 
            FROM history 
            WHERE user_uuid = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (user_uuid, limit),
        ).fetchall()

        history = []
        for row in results:
            history.append(
                {
                    "id": str(row[0]),
                    "question": row[1],
                    "image_url": row[2],
                    "response": row[3],
                    "timestamp": row[4].isoformat() if row[4] else None,
                }
            )
        return history


if __name__ == "__main__":
    db = Database()
    db.initialize_db()
    print("Database initialized successfully.")
