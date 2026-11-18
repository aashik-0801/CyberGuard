# CyberGuard 1.0.0

CyberGuard is a personal cybersecurity platform with a private dashboard, account management, activity history, a local password strength checker, and a secure password generator.

## What is included

- Public landing page and responsive authenticated workspace.
- Registration, email/password sign-in, sign-out, protected routes, and account profile editing.
- Werkzeug password hashing; plaintext account passwords are never stored.
- CSRF protection on form and JSON state-changing requests.
- Login attempt limiting and hardened session cookie defaults.
- SQLite persistence through SQLAlchemy. Startup uses `create_all()` and does not delete existing user records.
- Client-side password checks. The password entered in the checker is not sent to the server.
- Server-side random password generation with Python `secrets`; generated passwords are not stored or included in activity descriptions.
- Activity events for successful and failed logins, sign-outs, checker use, generation, and profile updates. Event descriptions exclude submitted/generated password values.
- Responsive layouts, keyboard-focus styling, reduced-motion support, and security response headers.

The checker is a practical heuristic, not a breach check or a guarantee of account safety. A long, unique password is generally preferable to a predictable complex one.

## Requirements

- Python 3.10 or later.
- Windows PowerShell examples below; use the equivalent virtual-environment commands on other platforms.

## Installation

From the project directory, create a virtual environment only if one does not already exist:

```powershell
py -m venv .venv
```

Install dependencies into the project environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Create local configuration:

```powershell
Copy-Item .env.example .env
```

Generate a secret key:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Set the generated value as `SECRET_KEY` in `.env`. Do not commit `.env` or use the example placeholder in a deployed environment.

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `SECRET_KEY` | Flask session and CSRF signing key; required at startup | None |
| `DATABASE_URL` | SQLAlchemy database connection | `sqlite:///cyberguard.db` (stored under `instance/`) |
| `COOKIE_SECURE` | Set secure session and remember cookies for HTTPS deployments | `false` for local development |
| `FLASK_DEBUG` | Enable the Flask development debugger | `false` |
| `RATELIMIT_STORAGE_URI` | Flask-Limiter storage URI | `memory://` |

Set `COOKIE_SECURE=true` when serving the application over HTTPS. The in-memory rate-limit backend is suitable for local/single-process use; production deployments with multiple workers should configure a shared Flask-Limiter storage backend and its matching package.

## Start the application

```powershell
.\.venv\Scripts\python.exe app.py
```

Open `http://127.0.0.1:5000`. The SQLite database is created at `instance/cyberguard.db` by default. `db.create_all()` creates missing tables on startup and does not reset or erase user data.

## Run tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Security and operations notes

- The password checker is implemented in browser JavaScript and sends only a password-checker-used event to the server. It does not submit the checked value, save it, or transmit it to a third party.
- The generator accepts only length/category settings, uses `secrets`, and returns the generated value to the requesting browser. Activity history stores a generic event only.
- Anonymous failed login events may have no user association; failures for a recognized account are associated with that account. Attempted emails and passwords are not recorded in activity descriptions.
- CSRF tokens, HTTP-only/SameSite cookies, configurable secure-cookie flags, login rate limiting, and basic security headers are enabled.
- Activity history currently has no retention/pruning policy. Add one before operating at scale.
- `create_all()` does not migrate changed schemas. Use a migration system before evolving deployed database models.
- V1 does not include email verification, password reset, multi-factor authentication, breach lookup, or device scanning.

## Release

Version: **1.0.0**
Release notes: [documentation/RELEASE_NOTES.md](documentation/RELEASE_NOTES.md)

After reviewing and committing the release on a Git branch, create the local tag:

```powershell
git tag -a v1.0.0 -m "CyberGuard 1.0.0"
git show v1.0.0
```

Push or publish only after explicit approval:

```powershell
git push origin v1.0.0
```
