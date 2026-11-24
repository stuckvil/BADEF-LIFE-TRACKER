
import os
import sqlite3

DATABASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "tasks.db"
)


def migrate():
    conn = sqlite3.connect(DATABASE)

    try:
        conn.execute("PRAGMA foreign_keys = ON")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (workspace_id)
                    REFERENCES workspaces(id),

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_workspace
            ON messages(workspace_id, created_at)
        """)

        conn.commit()

        print("Messaging database created successfully!")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    migrate()

