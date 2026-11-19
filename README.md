# CyberGuard 3.0.0 — Personal Security Intelligence

CyberGuard is a personal cybersecurity platform with a private dashboard, account management, password tools, file integrity utilities, heuristic URL analysis, searchable activity, and downloadable reports.

Version 3.0 extends the existing V1 and V2 Flask application in place while preserving accounts, activity records, password tools, reports, and the established design system.

## V3.0.0 Features

- Backend device information dashboard with explicit collection scope and timestamps.
- Read-only local network configuration display for hostname, local IP, interfaces, gateway, DNS, and connectivity limitations.
- Unified user-scoped security event timeline with existing search, category, date filters, pagination, and CSV/text exports.
- Transparent recommendation engine based on actual account events and clearly labeled general guidance.
- Database-derived security analytics for login activity, tool usage, event distribution, daily totals, and event trends.
- Downloadable HTML and CSV personal security reports containing collected facts, activity summaries, tool usage, and recommendations.
- Expanded dashboard summaries for device facts, network facts, recent activity, tool usage, and recommendations.

## V2.0.0 Features

- Public landing page and responsive authenticated workspace.
- Registration, email/password sign-in, sign-out, protected routes, and account profile editing.
- Werkzeug password hashing; plaintext account passwords are never stored.
- CSRF protection on form and JSON state-changing requests.
- Login attempt limiting and hardened session cookie defaults.
- SQLite persistence through SQLAlchemy.
- Client-side password checks. Passwords entered in the checker are not sent to the server.
- Server-side random password generation using Python `secrets`.
- Activity events for successful and failed logins, sign-outs, password checker use, password generation, and profile updates.
- SHA-256 file hashing and two-file integrity comparison, processed in bounded chunks with a 16 MiB per-file limit.
- URL analysis for HTTPS usage, IP hostnames, punycode, recognizable shorteners, and suspicious patterns.
- User-scoped Security Activity Center with search, category/date filters, and pagination.
- Database-derived per-user tool usage statistics.
- CSV and readable text reports for hashes, comparisons, URL analysis, and activity history.
- Responsive dashboard with V2 security tools, navigation, recent activity, and version indicator.
- Security response headers and keyboard accessibility improvements.

## Security Tool Limitations

URL indicators are transparent heuristics, not definitive phishing, malware, authenticity, or safety verdicts.

Matching SHA-256 file hashes establish content equality for the compared files, not their authenticity or safety.

Password strength is a heuristic, not a breach check or a guarantee of account safety.

Device information describes the Flask backend host, not necessarily the browser user's device.

Network information is read-only local configuration. CyberGuard does not scan networks, scan ports, intercept packets, or inspect traffic content.

Security recommendations are informational and do not constitute a complete security audit or vulnerability assessment.

V3 does not add email verification, password reset, multi-factor authentication, breach lookup, or device vulnerability scanning.

## Data and Database Continuity

V3 reuses the existing `users` and `activities` tables.

No schema changes were needed for this release, so no migration is required.

- Existing account records are preserved.
- Existing activity records are preserved.
- No database reset or deletion is performed.
- Startup uses SQLAlchemy `create_all()` to create missing tables on a fresh installation.
- `create_all()` does not migrate changed database schemas.

Use a migration system before introducing future schema changes.

Uploaded file contents, entered passwords, and submitted URLs are not stored in the database.

Activity entries contain generic tool-use events only. Reports are generated on demand and downloaded, not retained server-side.

## Requirements

- Python 3.10 or later.
- Windows PowerShell examples are provided below.

## Installation

From the project directory, create a virtual environment only if one does not already exist:

```powershell
py -m venv .venv
```

Install dependencies:

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

Set the generated value as `SECRET_KEY` in `.env`.

Do not commit `.env` or use the example placeholder in a deployed environment.

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `SECRET_KEY` | Flask session and CSRF signing key | None |
| `DATABASE_URL` | SQLAlchemy database connection | `sqlite:///cyberguard.db` |
| `COOKIE_SECURE` | Secure session and remember cookies for HTTPS | `false` |
| `FLASK_DEBUG` | Enable Flask development debugger | `false` |
| `RATELIMIT_STORAGE_URI` | Flask-Limiter storage URI | `memory://` |

The SQLite database is stored under `instance/` by default.

Set `COOKIE_SECURE=true` when serving the application over HTTPS.

Each uploaded file is limited to 16 MiB. File comparisons accept up to two such files per request.

The in-memory rate-limit backend is suitable for local or single-process use. Production deployments with multiple workers should configure shared Flask-Limiter storage and its matching package.

## Start the Application

```powershell
.\.venv\Scripts\python.exe app.py
```

Open:

http://127.0.0.1:5000

The SQLite database is created at `instance/cyberguard.db` by default.

Existing V1 user accounts and activity records are preserved.

File hashing and comparison tools accept files up to 16 MiB each.

Configure HTTPS and set `COOKIE_SECURE=true` when deploying outside local development.

## Run Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Run the complete test suite before releasing V3.0.0.

## Security and Operations Notes

- The password checker runs in browser JavaScript and sends only a generic usage event to the server.
- The password generator uses Python `secrets`.
- Generated passwords are not stored in activity descriptions.
- Hashing and comparison read uploaded files in 1 MiB chunks.
- Uploaded file contents are not permanently saved or executed.
- URL analysis performs no network requests, DNS lookups, or URL visits.
- Device and network information is collected locally and displayed read-only.
- Security reports are generated on demand and downloaded, not retained server-side.