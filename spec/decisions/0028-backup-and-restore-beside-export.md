---
id: design-decision/missingmass.io/shopsystem/kb/backup-and-restore-beside-export
summary: "The operator backs up a running store whole, its history and journal included, without stopping writers, and restores that backup as a store in an empty place, so that losing a server loses nothing: backup is how a lost server is recovered; export stays the readable, portable copy and does not carry history. Files enter a store through the operator's import, or whole as a store through the operator's restore of a backup. Promotes the backups deferred in operate-a-store; the user's decision."
date: 2026-10-10
status: accepted
by: ".shop/records/decision-arguments/0028-backup-and-restore-beside-export.md; supersedes design-decision/missingmass.io/shopsystem/kb/files-are-an-export (its clause that files on disk enter a store only through `kb import`)"
source: decision-argument/missingmass.io/shopsystem/kb/0028-backup-and-restore-beside-export
supersedes: design-decision/missingmass.io/shopsystem/kb/files-are-an-export
---

# backup-and-restore-beside-export

## Decision
The operator backs up a running store whole, its history and journal included, without stopping writers, and restores that backup as a store in an empty place, so that losing a server loses nothing: backup is how a lost server is recovered; export stays the readable, portable copy and does not carry history. Files enter a store through the operator's import, or whole as a store through the operator's restore of a backup. Promotes the backups deferred in operate-a-store; the user's decision.
