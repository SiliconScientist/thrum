Plan: docs/superpowers/plans/2026-10-25-mvp.md
Preflight: storage interfaces supply browser and CLI. No shared-state workers.
Task 1 complete: 15 storage/portability tests pass. Test fixture uses canonical temporary paths to respect symlink refusal.
Task 2 complete: 8 HTTP tests pass with required local socket permission.
Task 3 CLI: 4 subprocess tests pass; final review and audit in progress.
Ruling: JSON import is empty-database-only to prevent destructive merging. No dependencies or installation step.
Final review: independent reviewer; three important findings fixed with regression tests. Suite 33/33.
Ruling: Preserve delimiter-bearing data with quoted CSV in the simple text editor; quote syntax is documented.
Ruling: Show affiliation and full IDs in relationship selectors for unambiguous duplicate names.
Final: minor (deferred): imports limited to 16 MiB while exports unbounded; SQLite backups remain usable.
Browser connection unavailable: HTTP validation completed; visual verification explicitly unclaimed.
Task 3 complete: CLI, documentation, review fixes and privacy scan complete; fresh commit and final location verification follow.
