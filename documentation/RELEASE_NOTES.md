# CyberGuard Release Notes

## 3.0.0 — Personal Security Intelligence

V3.0 extends the existing V1 and V2 application in place. It adds defensive, local, read-only information dashboards and reporting without replacing the existing accounts, activity table, tools, or visual design.

### Highlights

- Device information is collected from the machine running the Flask backend, not inferred to be the browser user's device.
- Network information is local and read-only. CyberGuard does not scan networks, scan ports, access other devices, intercept packets, or inspect traffic content.
- Security activity remains user-scoped and supports search, category/date filters, pagination, and existing exports.
- Recommendations distinguish account findings, evidence-based recommendations, general advice, and configuration guidance.
- Analytics are generated from actual database activity records, with date-range filtering and explicit empty states.
- HTML and CSV security reports include generation date, application version, available device/network facts, activity summary, tool usage, and recommendations.

### Security and compatibility

- Existing accounts and activity records remain unchanged.
- No database schema change or migration is required for V3.
- Device and network values are displayed as unavailable when collection APIs do not provide them.
- Reports contain no passwords or uploaded file contents.
- Authentication, CSRF protection, rate limits, secure session defaults, and per-user data access remain enabled.

### Limitations

- CyberGuard does not perform a complete security audit or vulnerability assessment.
- Device details describe the Flask backend host.
- Network connectivity is not claimed to be externally tested.
- Missing operating-system or network values are not invented.
- Recommendations are informational unless a rule explicitly identifies a recorded application event.

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