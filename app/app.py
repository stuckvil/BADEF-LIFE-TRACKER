from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "badef-development-key-change-before-production"
)
# Always use the database inside the app folder
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.db")
def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.")
            return redirect(url_for("login"))

        return view(**kwargs)

    return wrapped_view

def get_db_connection():
    conn = sqlite3.connect(DATABASE)

    # Enable foreign-key enforcement for this connection
    conn.execute("PRAGMA foreign_keys = ON")

    # Allow database rows to be accessed by column name
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

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("login"))

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

        if user and check_password_hash(user["password_hash"], password):

            # Find this user's personal workspace.
            personal_workspace = conn.execute("""
                SELECT w.id
                FROM workspaces w
                JOIN workspace_members wm
                    ON wm.workspace_id = w.id
                WHERE wm.user_id = ?
                  AND w.workspace_type = 'personal'
            """, (user["id"],)).fetchone()

            conn.close()

            if not personal_workspace:
                flash("Your personal workspace could not be found.")
                return redirect(url_for("login"))

            # Start a fresh session.
            session.clear()

            # Store the authenticated user and active workspace.
            session["user_id"] = user["id"]
            session["workspace_id"] = personal_workspace["id"]

            flash("Welcome back, " + user["name"] + "!")
            return redirect(url_for("home"))

        conn.close()

        flash("Incorrect email or password.")
        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    user_id = session["user_id"]
    workspace_id = session.get("workspace_id")

    conn = get_db_connection()

    # Confirm that this user belongs to the active workspace.
    membership = conn.execute("""
        SELECT id
        FROM workspace_members
        WHERE user_id = ? AND workspace_id = ?
    """, (user_id, workspace_id)).fetchone()

    if not membership:
        conn.close()
        session.clear()
        flash("Please log in and select an authorized workspace.")
        return redirect(url_for("login"))

    # Add a task when the form is submitted.
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
                    conn.close()
                    return "Invalid due date", 400

            conn.execute("""
                INSERT INTO tasks
                    (name, priority, due_date, user_id, workspace_id)
                VALUES (?, ?, ?, ?, ?)
            """, (task, priority, due_date, user_id, workspace_id))

            conn.commit()

        conn.close()
        return redirect(url_for("home"))

    # Show only tasks belonging to this user and workspace.
    tasks = conn.execute("""
        SELECT *
        FROM tasks
        WHERE user_id = ? AND workspace_id = ?
        ORDER BY id
    """, (user_id, workspace_id)).fetchall()

    conn.close()

    return render_template("index.html", tasks=tasks)

@app.route("/complete/<int:task_id>", methods=["POST"])
@login_required
def complete(task_id):
    user_id = session["user_id"]
    workspace_id = session.get("workspace_id")

    conn = get_db_connection()

    # Verify that the user belongs to the active workspace.
    membership = conn.execute("""
        SELECT id
        FROM workspace_members
        WHERE user_id = ? AND workspace_id = ?
    """, (user_id, workspace_id)).fetchone()

    if not membership:
        conn.close()
        return "Unauthorized workspace", 403

    # Update only a task owned by this user in this workspace.
    conn.execute("""
        UPDATE tasks
        SET completed = NOT completed
        WHERE id = ?
          AND user_id = ?
          AND workspace_id = ?
    """, (task_id, user_id, workspace_id))

    conn.commit()
    conn.close()

    return redirect(url_for("home"))
@app.route("/delete/<int:task_id>", methods=["POST"])
@login_required
def delete(task_id):
    user_id = session["user_id"]
    workspace_id = session.get("workspace_id")

    conn = get_db_connection()

    # Verify workspace membership.
    membership = conn.execute("""
        SELECT id
        FROM workspace_members
        WHERE user_id = ? AND workspace_id = ?
    """, (user_id, workspace_id)).fetchone()

    if not membership:
        conn.close()
        return "Unauthorized workspace", 403

    # Delete only this user's task in the active workspace.
    conn.execute("""
        DELETE FROM tasks
        WHERE id = ?
          AND user_id = ?
          AND workspace_id = ?
    """, (task_id, user_id, workspace_id))

    conn.commit()
    conn.close()

    return redirect(url_for("home"))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)


