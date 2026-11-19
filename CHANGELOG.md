# Changelog

## 3.0.0 — Personal Security Intelligence

### Added

- Backend device information and timestamped collection status.
- Read-only local network configuration views.
- Recommendation engine with verified, evidence-based, and general classifications.
- Database-derived security analytics and date-range filtering.
- Downloadable HTML and CSV personal security intelligence reports.
- Dashboard device, network, recommendation, and analytics links.

### Changed

- Updated application version indicators to 3.0.0.
- Expanded navigation and dashboard while preserving V1/V2 tools and design.

### Preserved

- Existing V1 authentication/profile/password features and V2 toolkit/activity/report features.
- Existing `users` and `activities` database records.

### Deprecated

- None.

### Database

- No schema changes or migration required. V3 reuses the existing `users` and `activities` tables.

## 2.0.0 — Advanced Security Toolkit

### Added

- SHA-256 hashing and comparison for files up to 16 MiB each, using chunk-based reads.
- URL analysis heuristics that never visit or fetch submitted URLs.
- Searchable, filterable, paginated, user-scoped activity history and database-derived tool usage analytics.
- On-demand CSV and readable text reports for file hashes, comparisons, URL analyses, and activity.
- V2 dashboard tool cards, analysis history, and usage statistics.

### Changed

- Updated product version indicators and navigation for V2.
- Added per-tool rate limits and upload request limits.

### Preserved

- V1 authentication, profile, password checker/generator, activity records, user accounts, and application architecture.

### Deprecated

- None.

### Database

- No schema changes; no migration was required. Existing records remain in the existing SQLAlchemy tables.