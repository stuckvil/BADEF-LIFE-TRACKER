
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# Always use the database inside the app folder
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.db")


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            completed BOOLEAN NOT NULL DEFAULT 0,
            priority TEXT NOT NULL DEFAULT 'Medium',
            due_date TEXT
        )
    """)

    # Safely add due_date if an older database does not have it
    columns = conn.execute("PRAGMA table_info(tasks)").fetchall()
    column_names = [column["name"] for column in columns]

    if "due_date" not in column_names:
        conn.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT")

    conn.commit()
    conn.close()


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        task = request.form.get("task", "").strip()
        priority = request.form.get("priority", "Medium")
        due_date = request.form.get("due_date", "").strip() or None

        if task:
            if priority not in ["Low", "Medium", "High"]:
                priority = "Medium"

            if due_date:
                try:
                    datetime.strptime(due_date, "%Y-%m-%d")
                except ValueError:
                    return "Invalid due date", 400

            conn = get_db_connection()
            conn.execute(
                """
                INSERT INTO tasks (name, priority, due_date)
                VALUES (?, ?, ?)
                """,
                (task, priority, due_date)
            )
            conn.commit()
            conn.close()

        return redirect(url_for("home"))

    conn = get_db_connection()
    tasks = conn.execute(
        "SELECT * FROM tasks ORDER BY id"
    ).fetchall()
    conn.close()

    return render_template("index.html", tasks=tasks)


@app.route("/complete/<int:task_id>")
def complete(task_id):
    conn = get_db_connection()

    conn.execute("""
        UPDATE tasks
        SET completed = NOT completed
        WHERE id = ?
    """, (task_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("home"))


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete(task_id):
    conn = get_db_connection()

    conn.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("home"))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)

