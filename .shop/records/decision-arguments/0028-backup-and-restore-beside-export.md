---
id: decision-argument/missingmass.io/shopsystem/kb/0028-backup-and-restore-beside-export
kind: decision-argument
about: bounded-context/missingmass.io/shopsystem/kb
---
# 0028 A store is backed up and restored whole, apart from export

2026-10-10. The operator backs up a running store whole, its history and journal included, and restores that backup as a store in an empty place, so that losing a server loses nothing; export stays the readable, portable copy, selected by the path below each type and imported into any store, and does not carry history. Promotes the backups deferred in operate-a-store. The user's decision.
