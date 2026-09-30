# THROWAWAY SPIKE: storage behind one port

Nothing here is kept or merged. The output is an answer, written up in the
"kb usage patterns" doc: can one port be met by TerminusDB and by SQLite, and
which should back kb?

- `port.py`: the port both adapters implement, and the neutral type model.
- `model.py`: the neutral kinds the conformance suite uses.
- `test_conformance.py`: one test per usage pattern (1 to 29) and the five
  holes from the 2026-09-30 diagnosis, parametrised over every adapter.
- `sqlite_adapter.py`, `terminus_adapter.py`: the adapters.

Run: `../../.venv/bin/python -m pytest spikes/storage -q` from the worktree
root. The TerminusDB adapter starts `terminusdb/terminusdb-server:v12.0.7`
in Docker once per session, or uses `TERMINUSDB_URL` when set.

Decision criteria, fixed before any results (TerminusDB backs kb if all hold):
1. It refuses a dangling link, including one left by removing a part or a kind.
2. It refuses a lost update and the two-writer race.
3. References inside a set work, including two new documents pointing at each other.
4. At 30,000 documents, a glance read with inbound counts and a three-step
   traversal each answer under 100 ms.
5. A fresh database per test costs under 1 s.
6. Its Python client works against the 12.x server.
