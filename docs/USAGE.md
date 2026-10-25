# Using Thrum

[Back to the overview](../README.md)

## Try Thrum

With **Python 3.10 or newer** installed, follow the
[download instructions](../README.md#quickstart) to get and extract Thrum.
Change into the project folder containing `README.md` and the `thrum/`
directory, then run these commands to try some fictional contacts.
This example assumes you extracted it to `~/Downloads/thrum-main`; adjust
the path to match:

```sh
cd ~/Downloads/thrum-main
python3 -m thrum --db ~/.local/share/thrum-demo/people.sqlite init
python3 -m thrum --db ~/.local/share/thrum-demo/people.sqlite demo
python3 -m thrum --db ~/.local/share/thrum-demo/people.sqlite serve
```

Open **http://127.0.0.1:8765/**. Stop Thrum with **Ctrl-C**.
Next time, return to the same project folder and run only the last command.
Run all commands in this guide from that folder. If Python reports
`No module named thrum`, make sure you are not in `~/Downloads` or the inner
`thrum/` directory. No package installation is required.

## Add your own contacts

Stop the demo, then run:

```sh
python3 -m thrum init
python3 -m thrum serve
```

Open **http://127.0.0.1:8765/** and select **Add contact**.
Your contacts are kept separate from the demo. Next time, run only
`python3 -m thrum serve`.

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

## Startup options

The commands above are for macOS and Linux. On Windows, use `py -3` instead of
`python3` and replace `~` paths with absolute paths in your user profile, outside
the project folder. Windows has not been tested for this release.

- **Different port:** append `--port 8766` to `serve`, then open the printed address.
- **Different database:** put `--db PATH` before the command, as in the demo.
- **Demo already loaded:** run only its `serve` command. `demo` requires an empty database.
- **Storage or permission errors:** see [Storage and permissions](PRIVACY.md#storage-and-permissions).
