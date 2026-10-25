# Developing Thrum

[Back to the overview](../README.md)

## Architecture and customization

| File | Responsibility |
| --- | --- |
| `thrum/storage.py` | Private paths, SQLite schema, numbered migrations, CRUD, search |
| `thrum/portability.py` | Versioned JSON import/export and SQLite backups |
| `thrum/web.py` | Local HTTP routing and browser request protections |
| `thrum/views.py` | Escaped, server-rendered HTML forms and pages |
| `thrum/style.css` | Responsive styling using system fonts |
| `thrum/demo.py` | Independently invented example dataset |
| `thrum/__main__.py` | Initialization, server, integrity, portability CLI |
| `tests/` | Standard-library unit and HTTP integration tests |

There are two numbered migrations: contacts (1), relationships and indexes (2).
`PRAGMA application_id` identifies Thrum databases; `PRAGMA user_version` tracks
schema versions. Initialization applies pending migrations transactionally and
refuses unrelated or newer databases. Back up before updating the application.

Add migrations at the next number in `MIGRATIONS`; do not rewrite released
migrations. Update export versioning and round-trip tests when changing the data
model. Add new fields through storage validation, views, and import/export
validation together. Relationship types and contact-method types already accept
custom labels. Change `style.css` to customize appearance; no frontend build is
needed. Search currently scans contacts in memory and suits small personal lists.

Run all tests from the project root:

```sh
python3 -B -m unittest discover -s tests -v
```

Tests use temporary fictional databases, never the default personal database.
HTTP tests require permission to bind localhost sockets.

## License and dependencies

Thrum is MIT licensed; see [LICENSE](../LICENSE). There are no third-party Python packages
or bundled assets. The runtime is Python (PSF License) and its bundled SQLite
library (public domain). Neither runtime is vendored here. System fonts are used
without redistribution. This implementation was written independently using
contact-management concepts as references; no reference code or data was copied.

## Before publishing

Review the [audit report](AUDIT.md), inspect all files and Git history, and rerun tests and
secret scanning. Choose a Git author identity appropriate for public attribution.
Never add personal databases, exports, screenshots, or machine configuration.
This local project has no remote; creating a GitHub repository, pushing, and
changing visibility are separate actions requiring approval.
