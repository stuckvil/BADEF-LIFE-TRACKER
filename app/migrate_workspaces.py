
import os
import sqlite3

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.db")


def migrate():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    try:
        # Start a transaction so incomplete changes can be rolled back.
        conn.execute("BEGIN")

        # 1. Create the companies table.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Create the workspaces table.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workspaces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                workspace_type TEXT NOT NULL
                    CHECK (workspace_type IN ('personal', 'company')),
                company_id INTEGER UNIQUE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )
        """)

        # 3. Connect users to workspaces.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workspace_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                workspace_id INTEGER NOT NULL,
                role TEXT NOT NULL DEFAULT 'employee',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (user_id, workspace_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
            )
        """)

        # 4. Check whether tasks already have workspace_id.
        columns = conn.execute("PRAGMA table_info(tasks)").fetchall()
        column_names = [column["name"] for column in columns]

        if "workspace_id" not in column_names:
            conn.execute(
                "ALTER TABLE tasks ADD COLUMN workspace_id INTEGER"
            )

        # 5. Give every existing user a personal workspace.
        users = conn.execute(
            "SELECT id, name FROM users"
        ).fetchall()

        for user in users:
            existing_workspace = conn.execute("""
                SELECT w.id
                FROM workspaces w
                JOIN workspace_members wm
                    ON wm.workspace_id = w.id
                WHERE wm.user_id = ?
                  AND w.workspace_type = 'personal'
            """, (user["id"],)).fetchone()

            if existing_workspace:
                workspace_id = existing_workspace["id"]
            else:
                cursor = conn.execute("""
                    INSERT INTO workspaces (name, workspace_type)
                    VALUES (?, 'personal')
                """, (user["name"] + "'s Personal Workspace",))

                workspace_id = cursor.lastrowid

                conn.execute("""
                    INSERT INTO workspace_members
                        (user_id, workspace_id, role)
                    VALUES (?, ?, 'owner')
                """, (user["id"], workspace_id))

            # Assign this user's existing tasks to their workspace.
            conn.execute("""
                UPDATE tasks
                SET workspace_id = ?
                WHERE user_id = ?
                  AND workspace_id IS NULL
            """, (workspace_id, user["id"]))

        # 6. Add indexes for faster workspace lookups.
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_workspace_members_user
            ON workspace_members(user_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_workspace_members_workspace
            ON workspace_members(workspace_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_workspace
            ON tasks(workspace_id)
        """)

        conn.commit()
        print("Workspace migration completed successfully.")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    migrate()

