# CyberGuard 2.0.0 — Advanced Security Toolkit

V2 extends the V1 application in place. Existing account and activity database records are retained; no database schema changes or migrations were needed for this release.

## Highlights

- Retained the V1 landing page, accounts, profile management, local password checker, secure password generator, and activity records.
- Added chunked SHA-256 file hashing and two-file content comparison with a 16 MiB per-file limit. Uploaded files are not stored or executed.
- Added URL heuristic analysis for HTTPS, IP hostnames, punycode, shorteners, and suspicious patterns. Submitted URLs are never visited or fetched.
- Added user-scoped activity search, category/date filters, pagination, usage counts from database events, and CSV/text reports.
- Extended the existing responsive dashboard and navigation without replacing the V1 design system.
- Kept CSRF protection, authentication checks, per-tool rate limits, security response headers, and hardened session cookies.

## Scope notes

Password and URL indicators are heuristics, not security guarantees or definitive threat verdicts. Matching SHA-256 values indicate content equality only and do not establish file authenticity or safety.

No V1 functionality was deprecated. V2 does not include password reset, email verification, multi-factor authentication, breach lookup, or device scanning.

Activity exports are assembled in memory; very large histories may need streaming before operating at scale.
