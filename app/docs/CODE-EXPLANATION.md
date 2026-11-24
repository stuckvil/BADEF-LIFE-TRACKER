# BADEF LIFE TRACKER - CODE EXPLANATION

## 1. Application Entry Point

File: app/app.py

This is the main Python file that runs our Flask application.

## 2. Flask Imports

from flask import Flask, render_template, request, redirect, url_for, session, flash

Explanation:

Flask: Creates our web application.
render_template: Displays HTML pages.
request: Receives information submitted by users.
redirect: Sends users to another page.
url_for: Generates application URLs.
session: Remembers the logged-in user.
flash: Displays temporary messages.

## 3. Database Connection

SQLite stores application information.

The database contains information such as:
- Users
- Companies
- Workspaces
- Workspace members
- Tasks
- Messages

## 4. User Authentication

Registration creates a user account.
Login verifies the user's password.
Logout clears the login session.

Passwords should be stored as secure hashes, not plain text.

## 5. Workspace Membership

The workspace_members table connects users to workspaces.

Example:

User 1 -> BADEF Technologies Workspace

This allows the application to check whether a user has permission to access a company workspace.

## 6. Team Messaging

The messages table stores:
- Message ID
- User ID
- Workspace ID
- Message content
- Date and time

Each message belongs to a workspace.

This allows authorized members of the same workspace to see shared messages.

## 7. Important Developer Lesson

Authentication answers:
Who are you?

Authorization answers:
What are you allowed to access?

Both are necessary for a secure application.
