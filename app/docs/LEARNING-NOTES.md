# BADEF LIFE TRACKER - LEARNING NOTES

## Project Overview

BADEF Life Tracker is a Flask web application designed to help individuals and companies manage tasks and communicate with team members.

## Technologies Used

- Python: Main programming language.
- Flask: Python web framework.
- SQLite: Database.
- HTML: Web page structure.
- CSS: Application styling.
- JavaScript: Interactive features.
- Git: Version control.
- GitHub: Remote code repository.
- Docker: Application containerization.
- AWS: Cloud hosting (planned).
- Terraform: Infrastructure as Code (planned).

## Feature 1: User Authentication

Purpose:
Allow users to register, log in, and log out securely.

Technologies:
- Flask routes
- Python
- SQLite
- Password hashing
- Sessions

What I learned:
Authentication identifies who is using the application.
Password hashing protects stored passwords.

## Feature 2: Company Workspaces

Purpose:
Allow multiple employees to work inside the same company environment.

Technologies:
- SQLite relationships
- Flask sessions
- Workspace membership
- User roles

What I learned:
A user must belong to a company workspace before accessing company resources.

## Feature 3: Team Communication

Purpose:
Allow employees in the same company workspace to exchange messages.

Technologies:
- Flask POST and GET routes
- SQLite messages table
- HTML forms
- Workspace permissions

What I learned:
Messages must be associated with the correct workspace so authorized team members can see them.
