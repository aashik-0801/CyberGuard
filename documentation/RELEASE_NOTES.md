# CyberGuard Release Notes

## 2.0.0 — Advanced Security Toolkit

V2.0 extends the existing V1 application in place. Existing account and activity database records are retained; no database schema changes or migrations are required for this release.

### Highlights

- Retained the V1 landing page, accounts, profile management, local password checker, secure password generator, and activity records.
- Added chunk-based SHA-256 file hashing and two-file content comparison with a 16 MiB per-file limit.
- Added local heuristic URL analysis for HTTPS, IP hostnames, punycode, recognizable shorteners, and suspicious patterns.
- Added searchable, filterable, paginated, user-scoped activity center.
- Added database-derived tool usage analytics and recent analysis events.
- Added CSV and readable text reports for hash results, file comparisons, URL analysis, and activity exports.
- Extended the responsive dashboard and authenticated navigation without replacing the V1 design system.

### Security and compatibility

- Uploaded files are processed using streams and are never permanently stored or executed.
- File uploads are limited to 16 MiB per file.
- Submitted URLs are parsed as text only. CyberGuard does not visit URLs, make network requests, or perform DNS resolution.
- Activity, analytics, and exports are scoped to the signed-in user.
- Existing V1 account and activity tables are preserved.
- CSRF protection, authentication checks, per-tool rate limits, security response headers, and hardened session cookies remain enabled.

### Limitations

- URL analysis produces heuristic indicators, not definitive phishing or malware verdicts.
- Password strength results are heuristics, not guarantees of security.
- Matching SHA-256 digests indicate content equality for the compared files; they do not establish authenticity, provenance, or safety.
- Activity history currently has no retention or pruning policy.
- Activity exports are assembled in memory; very large histories may require streaming before operating at scale.
- Password reset, email verification, multi-factor authentication, breach lookup, and device scanning are outside the current release scope.

## 1.0.0 — Initial V1 release foundation

Initial CyberGuard release providing account functionality, profile management, password checking, secure password generation, and activity records.