# Thrum implementation and privacy audit

Audit date: October 25, 2026.

## Scope and outcome

This is an independently written starter application in a new standalone Git
repository. No source files, contact records, configuration, databases, or Git
objects were copied from reference repositories. No GitHub repository was created
or changed. No remote is configured and nothing has been pushed.

All project files were inspected. Pattern checks covered credential formats,
private keys, personal absolute paths, and email addresses. Email-shaped values
in source and examples use only `example.invalid`. No personal records, secrets,
SQLite files, exports, backups, screenshots, environment files, or logs were
found in the project. The four demo contacts and three relationships were
invented for this implementation; duplicate names are intentional.

Gitleaks and TruffleHog were unavailable. These checks combine manual review and
custom heuristics, not a comprehensive secret-scanner certification. A clean
scan cannot prove absence of every sensitive value.

## Validation

- 33 automated tests passed on Python 3.12/macOS using unittest.
- Storage: duplicate-name CRUD, cascading deletion, directed relationship CRUD,
  search/filtering, atomic validation, stale edits, revision overflow protection.
- Migrations: repeatable initialization, upgrade from schema 1 to 2 without data
  loss, rejection of unrelated and future databases.
- Portability: ID-preserving JSON round trips, malformed import rollback,
  duplicate IDs/JSON keys, missing endpoints, unsupported versions, private output
  permissions, overwrite refusal, SQLite integrity, and backups excluding an
  uncommitted concurrent write.
- HTTP: contact and relationship lifecycles; loopback binding; Host/Origin and
  CSRF rejection; duplicate headers/fields; deletion confirmation; path traversal
  refusal; output escaping; cache/CSP headers; no request logging; reversible
  delimiter handling and distinguishable duplicate-name selectors.
- CLI: init, demo, check, export, backup, restore/import and error handling ran in
  temporary fictional directories. The documented command sequences were
  exercised with isolated database/output paths.
- Server startup succeeded on loopback. HTTP checks returned 200 for the contact
  directory, contact form, relationship form, data guidance, and stylesheet.
- The Browser plugin reported no available browser. Visual layout, keyboard
  accessibility, and real-browser form behavior were not manually verified.
- Ignore probes passed for databases, journal/WAL/SHM files, exports, backups,
  environment files, private notes, screenshots, logs, and keys.

## Independent review

A separate reviewer inspected the implementation and ran the original 27 tests.
Three important findings were fixed with regression tests: delimiter round-trip
loss in browser editing, revision overflow, and indistinguishable duplicate-name
selectors. No critical issues were found.

One minor limitation remains: the CLI limits imports to 16 MiB, while exports
have no size limit. Large datasets may require a code-level import or a later
streaming import feature; SQLite backups remain restorable. Other limits are
listed below and in the README.

## Fresh history and preservation

The project is recorded as a single new root commit, with no inherited parent,
branch, tag, remote, or Git objects from either reference repository. Its author
and committer use a project-level attribution and a reserved example-domain
email rather than the developer machine's personal identity. Tracked files,
commit metadata, and all locally stored objects are checked after committing.

The original repositories' HEADs, working-tree status, and tracked file hashes
are compared with the baseline captured before implementation. Their existing
changes are preserved. Private databases were not opened.

## Remaining limitations

- Intended for one trusted operating-system account, not hostile local processes
  or multiple users. No application authentication or encryption at rest.
- Python's standard HTTP server is for local use only; no public deployment.
- Filesystem permission enforcement is POSIX-specific; Windows ACL behavior has
  not been tested. Python 3.10/3.11 were not separately tested.
- Search scans the contact list in memory. No pagination or advanced analytics.
- Import supports Thrum JSON into an empty database only, not CSV/vCard or merges.
- Free-text affiliations and organization relationships are not synchronized.
- Form validation uses a simple error page with browser Back recovery.
- Migration rollback is transactional; no automatic downgrade mechanism.
- Secure deletion cannot erase operating-system snapshots or existing backups.

## Publication checklist

1. Review this code, MIT attribution, and chosen Git author identity.
2. Rerun tests and a dedicated secret scanner before publication; inspect every
   tracked file and the complete commit history, including any later commits.
3. Keep all personal databases, exports, backups, and screenshots outside Git.
4. Choose a new GitHub repository name and visibility; obtain explicit approval
   before creating it, adding its remote, pushing, or making it public.
5. Perform a real-browser usability/accessibility check and test supported target
   platforms before describing this as a production-ready release.

No public hosting, repository creation, visibility change, or push is authorized
by completion of this local implementation.
