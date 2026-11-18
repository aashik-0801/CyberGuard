# CyberGuard 1.0.0

Initial V1 release foundation.

## Highlights

- Public product landing page and responsive personal security dashboard.
- User registration, sign-in, sign-out, and username profile management.
- CSRF-protected requests, secure password hashing, session settings, response security headers, and login rate limiting.
- Password strength checker that evaluates input locally in the browser.
- Password generator using Python's `secrets` module, ensuring each chosen character category is represented.
- Persistent SQLite user records and privacy-safe activity history.
- Pytest coverage for authentication, protected pages, password tools, profile updates, and activity events.

## Scope notes

Password strength is a heuristic and not a guarantee of security. The V1 release does not provide password reset, email verification, multi-factor authentication, breach lookup, or device scanning.
