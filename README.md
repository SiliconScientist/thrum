# Thrum

A small, local-first relationship manager. Keep contact details, remember context,
and see how people and organizations connect—without a cloud account.

Thrum runs a browser dashboard on your own computer. It supports people and
organizations, duplicate names, tags, notes, directed relationships, search,
portable JSON exports, and consistent SQLite backups.

## Quickstart with fictional data

Requires **Python 3.10 or newer**, including its standard `sqlite3` module.
No packages, build step, account, or internet connection are required.
Download or clone this project's source, open a terminal, and change into its
root directory (the directory containing this README).

Run these commands from that directory on macOS or Linux:

```sh
python3 -m thrum --db ~/.local/share/thrum-demo/people.sqlite init
python3 -m thrum --db ~/.local/share/thrum-demo/people.sqlite demo
python3 -m thrum --db ~/.local/share/thrum-demo/people.sqlite serve
```

Open **http://127.0.0.1:8765/** in your browser. Stop the server with **Ctrl-C**.
To use another port, append `--port 8766` to `serve` and open the printed address.
The server never binds to a public network interface.

The demo contains four invented contacts and three invented relationships.
Two people deliberately share a name to demonstrate separate identities.
All demo emails use `example.invalid`. No examples come from a personal database.
`demo` refuses a nonempty database and never silently resets your data.

On Windows, use `py -3` instead of `python3`, and replace `~` paths with absolute
paths in your own user profile, outside the checkout. POSIX permission checks
are enforced on macOS/Linux; Windows access depends on your account's folder ACLs.
Windows has not been tested for this release.

## Start your own directory

The default private database is `~/.local/share/thrum/people.sqlite`, separate
from the demo:

```sh
python3 -m thrum init
python3 -m thrum serve
```

New database directories use private permissions (0700) and files use 0600 on
POSIX systems. Existing paths with broader permissions are refused; choose a
new dedicated private directory. Symlink paths and paths inside any Git checkout
are refused. On macOS, use canonical `/private/tmp` rather than the `/tmp`
symlink when experimenting with temporary data.

`--db` is a global option: put it **before** the subcommand.

## Contacts and relationships

- Select **Add contact**, choose person or organization, and enter a name.
- Add affiliation, comma-separated tags, notes, and contact details. Each detail
  takes one line: `email | hello@example.invalid | work` or `phone | value`.
  The third part is an optional label. Fields containing `|`, commas in tags,
  quotes, or newlines are quoted using CSV conventions; the editor preserves
  those quotes when displaying existing values.
- Select a contact to view or edit it. Names do not need to be unique; UUIDs
  identify records. Editing a record never changes its ID.
- Select **Add relationship**. Choose **From**, **To**, and a type such as
  `introduced`, `colleague of`, or `member of`. Relationship options show affiliation and full
  IDs so same-name contacts remain distinguishable.
- Contact pages show **outgoing** and **incoming** relationships. Relationships
  can be edited or removed. Deleting a contact also deletes its relationships;
  the confirmation screen explains this before deletion.
- Search matches names, affiliation text, contact-method values, and tags,
  case-insensitively. Type and exact-tag filters combine with search.

Affiliation is free text for quick context. To connect a person to an organization
record, add a `member of` or `works at` relationship as well. These two fields are
not automatically synchronized. Relationship types are free text; reciprocal
relationships are not inferred. Notes are not included in search.

Concurrent edits are guarded by revision checks. If a save is rejected because
another tab changed the record, reopen the contact before retrying. Use the
browser's Back button to recover entries after a validation error.

## Backup, export, and restore

These commands use the default personal database. Add `--db PATH` before the
subcommand to use the demo or another database. New output directories are created
privately. Existing output files are **never overwritten**; choose a fresh name.

```sh
python3 -m thrum backup ~/.local/share/thrum-backups/first.sqlite
python3 -m thrum export ~/.local/share/thrum-exports/first.json
python3 -m thrum check
```

Backups use SQLite's backup API, so they are consistent even while the browser is
running. A backup can be opened directly:

```sh
python3 -m thrum --db ~/.local/share/thrum-backups/first.sqlite check
python3 -m thrum --db ~/.local/share/thrum-backups/first.sqlite serve
```

Serving a backup makes it a live, editable database. Preserve another copy if you
need an untouched backup. Do not copy an active database file with ordinary file
copy tools; use `backup`.

Import a JSON export into a **new, empty** database:

```sh
python3 -m thrum --db ~/.local/share/thrum-restored/people.sqlite import ~/.local/share/thrum-exports/first.json
python3 -m thrum --db ~/.local/share/thrum-restored/people.sqlite check
python3 -m thrum --db ~/.local/share/thrum-restored/people.sqlite serve
```

Import preserves stable IDs, contact details, notes, tags, relationships, and
revision counters. Validation and writes are atomic. Nonempty databases, unknown
versions, duplicate IDs/JSON keys, and missing relationship endpoints are rejected.
The CLI accepts imports up to 16 MiB. JSON exports contain `format: "thrum"`,
`version: 1`, `contacts`, and `relationships`. This is a Thrum-specific format;
CSV and address-book imports are not included.

## Privacy and security

- All contact data stays in the chosen local database. No telemetry, AI services,
  external fonts, CDNs, remote assets, or outbound application requests.
- Loopback-only HTTP, strict Host/Origin validation, per-server random CSRF
  tokens, bounded form bodies, escaped HTML, a restrictive Content Security
  Policy, and `no-store` response headers.
- No request logs or contact values printed by the CLI. Error responses omit
  database paths and raw exception details.
- Runtime data is refused inside Git checkouts. `.gitignore` additionally excludes
  databases and sidecars, exports, backups, environment files, logs, and images.
  Ignore rules are a precaution, not a guarantee: `git add -f` can bypass them.
- No passwords, authentication, encryption at rest, or secure-erasure guarantee.
  This is for one trusted device account. Other programs or browser extensions
  running as you may access data. Protect your operating-system account, disk,
  and backups. SQLite secure deletion cannot erase backups, filesystem snapshots,
  or storage-device history.
- Do not expose this development HTTP server through a proxy, tunnel, container
  port mapping, or public network. It is not a multi-user hosting service.

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

Thrum is MIT licensed; see `LICENSE`. There are no third-party Python packages
or bundled assets. The runtime is Python (PSF License) and its bundled SQLite
library (public domain). Neither runtime is vendored here. System fonts are used
without redistribution. This implementation was written independently using
contact-management concepts as references; no reference code or data was copied.

## Before publishing

Review `docs/AUDIT.md`, inspect all files and Git history, and rerun tests and
secret scanning. Choose a Git author identity appropriate for public attribution.
Never add personal databases, exports, screenshots, or machine configuration.
This local project has no remote; creating a GitHub repository, pushing, and
changing visibility are separate actions requiring approval.
