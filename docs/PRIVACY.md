# Privacy and security

[Back to the overview](../README.md)

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

## Storage and permissions

The default personal database is `~/.local/share/thrum/people.sqlite`.
The quickstart demo uses a separate database at
`~/.local/share/thrum-demo/people.sqlite`.

New database directories use private permissions (0700) and files use 0600 on
POSIX systems. Existing paths with broader permissions are refused; choose a
new dedicated private directory. Symlink paths and paths inside any Git checkout
are refused. On macOS, use canonical `/private/tmp` rather than the `/tmp`
symlink when experimenting with temporary data.

Windows access depends on your account's folder ACLs; POSIX permission checks
apply on macOS and Linux. Windows has not been tested for this release.

For backup instructions, see [Using Thrum](USAGE.md#backup-export-and-restore).
For the implementation review and validation limits, see the [audit report](AUDIT.md).
