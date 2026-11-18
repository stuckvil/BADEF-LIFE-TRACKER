
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "badef-development-key-change-before-production"
)
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

    # Create users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'employee'
        )
    """)


    conn.commit()
    conn.close()
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required.")
            return redirect(url_for("register"))

        if len(password) < 8:
            flash("Password must be at least 8 characters.")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)

        conn = get_db_connection()

        try:
            conn.execute(
                """
                INSERT INTO users (name, email, password_hash)
                VALUES (?, ?, ?)
                """,
                (name, email, password_hash)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            flash("An account with that email already exists.")
            return redirect(url_for("register"))
        finally:
            conn.close()

        flash("Registration successful. Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]

            flash("Welcome back, " + user["name"] + "!")
            return redirect(url_for("home"))

        flash("Incorrect email or password.")
        return redirect(url_for("login"))

    return render_template("login.html")
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

