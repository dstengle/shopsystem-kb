# kb Batch 23 Implementation Plan: slices 102.7 to 114, storage behind a port with SQLite first

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. There is one task per slice of `docs/superpowers/plans/2026-09-24-kb-slices.md`, in slice order. Capability slices are built red-green under shopsystem-bdd:bdd-red-green. Enabling and stack slices are verified by their checks. Task 7 (slice 102.9.5) is the tenth architecture review: the controller dispatches it to the shopsystem-bdd:architecture-reviewer agent, and no implementer works on it.

**This plan carries no code** (shopsystem-knowledge adrs/0011). For each task it says:
- what is red and why;
- where the change lands;
- what is already decided, and the spec line each decision rests on;
- which existing steps can be reused;
- how to verify the task, with expected counts.

The implementer writes every step definition and every line of code.

**Goal:** move kb's store out of files in a git repository into one SQLite database behind an internal port, with no change any client can see. Then build on that:
- integrity checked in both directions (a dropped item, a type still in use);
- a set checked once against the state it leaves;
- concurrent clients on one machine;
- the operator's export, import check and import;
- one fault for a database that cannot be read, from every call and command;
- the performance bounds, checked by a benchmark.

Before the rewrite, six small slices put the code and the tests into a known shape: 102.7, 102.8, and the ninth review's R1 to R4. Then the tenth review (102.9.5) checks that shape. Serving a store (`kb serve`) is not built in this batch. The spec defers it from the damaged-database and command-line lines (Not yet entries, spec `4603df6`).

**Architecture:**
- `servicer.py` stays the one fail-closed adapter. From slice 104, its wrapper turns any escaping exception into a fault, and a failing clock into rule `clock`.
- kb's rules stay above the port: names, content checks, sections and items, signatures, faults, and the contract.
- `port.py` holds the kb-internal interface:
  - one write call, `land(changes, signature)`, carrying each change's content, links, parts by place and the revision it was read at, with the history entries riding along;
  - reads by name, kind, field, link, text and history.
- `sqlite_store.py` is the adapter. It keeps the artifacts, the link index, the search rows, the history and every past revision in `kb/store.sqlite3` (WAL mode).
- `store.py` keeps discovery and the marker `kb/store.yaml`.
- `journal.py` keeps entry naming and fingerprints, and writes no files.
- No git runs anywhere.
- The operator's `kb export` and `kb import` run through the same wrapper as every rpc.

**Tech Stack:**
- Python 3.11 and the standard library's `sqlite3` (this machine has SQLite 3.46.1 with FTS5);
- protobuf and grpcio (contract unchanged);
- ruamel.yaml 0.19 (YAML 1.2, the one canonical form);
- jsonschema with referencing;
- pytest 9 with pytest-bdd 8.1.

**Spec** (at `4603df6`; features and slices at `c9d450b`):
- `spec/index.md` (Constraints carried, Order of building change (1), Testing);
- `spec/decisions.md`: in particular `decision/sqlite-canonical`, `kb-runs-no-git`, `storage-behind-a-port`, `integrity-checked-both-ways`, `write-lock-on-one-machine`, `a-set-lands-in-one-transaction`, `a-set-is-checked-whole-links-and-types`, `damaged-database-one-fault`, `files-are-an-export`, `past-states-kept-not-yet-read`, `performance-bounds` and `clock-failure-rule`;
- `spec/capabilities/*.md`: change-the-store, check-a-change, define-a-type, make-several-changes-in-one-go, keep-the-history, query-the-store, start-a-store, answer-a-damaged-file, export-and-import-a-store and operate-a-store;
- the absorbed note, `docs/superpowers/specs/2026-10-01-kb-storage-sqlite-design.md`;
- the ninth architecture review, `/home/vscode/kb-reviews/ninth-review.md` (R1 to R5, deferred minors, coupling);
- the slices plan's log entry of 2026-10-01, "Batch 23 planned", which records the controller's answers to this plan's questions. This plan states each answer as a decision where it applies.

The spike on branch `spike/storage-2026-09-30` is cited for its findings only, never its code. `CLAUDE.md` is binding: its rules and its module map.

## Global Constraints

Copied verbatim from `spec/index.md` where they apply:

- The database is canonical; canonical YAML is its export and wire form. The contract is the only access path for clients; files on disk enter a store only through the operator's import, checked first, into a freshly started store. kb runs no git.
- Every change goes through the contract or the operator's import: drafted, checked, then landed with its history in one transaction. Nothing else edits the store.
- All YAML kb reads or writes is YAML 1.2: content over the contract, types, exported and imported files, and the type that describes types.
- What a client may depend on is published and versioned together by kb's release tag, which clients pin: `kb.proto` and its messages, the in-process client's `connect` with its clock, `kb.content` (content as canonical text, and `NotCanonical`), the connection file's form (`kb/server.yaml` and its `address`), and each fault's `rule` name. A fault's message wording, the store's files and layout, the storage port and every other module may change behind the contract.
- A fault's `rule` is one of kb's own rule names, or, for content that breaks a type's JSON Schema, the JSON Schema keyword it breaks. kb's own rule names: `not-found`, `kind`, `locator`, `collection`, `identity`, `on_delete`, `unreadable`, `item-name`, `shape`, `built-on`, `targets`, `version`, `content`, `sections`, `ref`, `actor`, `message`, `operations`, `since`, `title`, `root`, `store`, `clock`.
- Errors are a typed list of `{ artifact, path, rule, message }`.
- Bounds: one database per store; at most one store above any directory (stores never nest); one delete rule, refuse; a server's network is its only boundary (no authentication or encryption); on one machine several callers share a store directly, the database's write lock serialising their changes, and across containers only through a server, which takes changes one at a time.
- Performance bounds, at 30,000 artifacts: a summary read and a three-step traversal under 100 ms each; a single change under 50 ms; a set of 100 changes under 1 s. Provisional until the scale targets are set.
- (Testing) No test reaches a store outside its own temporary directory. A set of changes is a scenario. Every storage adapter passes the same conformance tests of the port. The performance bounds are checked by a benchmark kept in the repository, not by scenarios; a release that misses one does not ship.

This plan's own constraints:

- **No feature line changes.** `kb.proto` does not change.
- **One rule name is added.** `clock` comes in with Task 9 (slice 104, `decision/clock-failure-rule`), and the published-contract test that pins the rule list moves with it. No other rule name is added: `src/kb/rules.py` is published and its list is closed.
- **Size.** No module in `src/kb/` may pass 250 lines, and `servicer.py` stays under 150 (it is 103 today). `store.py` is at 249, so nothing may be added to it before Task 8 shrinks it. A task that would cross a limit splits the module first, by concern, giving each new module a CLAUDE.md row. Each task says where this may happen.
- **The suite's baseline.** `make test` (or `.venv/bin/python -m pytest -q -p no:warnings`) gives `230 passed, 7 failed` at `c9d450b`. The 7 are slice 106's one scenario, slice 107's five and slice 113's one, each `StepDefinitionNotFoundError`.
  - Record the failing list before the batch with `.venv/bin/python -m pytest -q -rf -p no:warnings | grep ^FAILED | sort > .superpowers/batch23/failing-before.txt`.
  - Enabling tasks leave that list unchanged.
  - Each task states the answer the suite should give after it.
  - At the end of the batch, 341 tests are collected and every one passes.
- **The conformance suite.** Task 8 writes `C` conformance tests of the port. This plan counts 22, one per case it lists. If the implementer writes a different number, every later total moves by the difference, and the checkpoint says so.
- **CLAUDE.md edits this batch makes.** Each rests on a decision that supersedes the old text.
  - Rows for the new modules: `port.py`, `sqlite_store.py` (and `sqlite_reads.py` if Task 8 splits it), `draft.py`, `export.py` and `importing.py`.
  - Rewritten rows: `store.py`, `journal.py`, `write.py`, `edits.py`, `query.py`, `check.py`, `rules.py` (if its row names the list) and `cli.py`.
  - Rule 3 is reworded to the one fault of a database that cannot be read (`decision/damaged-database-one-fault`), and rule 4's "write, journal and commit" becomes one landing transaction (`decision/a-set-lands-in-one-transaction`).
  - No other rule text changes.
  - Any refactor slice the tenth review cuts may add to this list.
- **Commits.** Use `git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit`, ending the message with the model's Co-Authored-By line.
  - Each task's commit holds its change, its checkpoint in the slice plan's Log and its status set to green. Task 8 may be several commits (it says how).
  - The implementer never pushes or tags.
  - No release falls inside this batch: no store made between Task 8 and Task 11 carries the implicit link to its type.
- **Scratch.** Probes, scratch virtualenvs and stores go under this checkout's `.superpowers/batch23/` or under the system's temporary directory. Never create anything elsewhere under `/home/vscode`, which shop-knowledge shares.
- **Refactors the tenth review cuts** (Task 7) are new slices. They are not tasks of this plan. If any must run before slice 103, the batch stops after Task 7 so the controller can amend this plan. Otherwise they wait for a later batch.

## Review Focus

### Five input classes most likely to bite

1. **Names whose path order is not their string order** (owner: Task 8).
   - Every reader today gives artifacts "in path order", by kind folder and then `<slug>.yaml`. Probe in a temporary store: create notes titled `Price`, `Price` (named `price-2`), `Price b` and `Pricea`, then call `List` with `ids_only`. It gives `price-2, price-b, price, pricea`, because `-` sorts before `.`. A plain `ORDER BY id` gives `price, price-2, price-b, pricea`.
   - Search breaks ties in the same order.
   - Also, `Draft.ids` sorts by the string `<kind>/<slug>.yaml`, while `Store.ids` sorts by path. These disagree for kinds like `work` and `work-item`.
   - The port's names come back in one defined order: kind, then `<slug>.yaml`, compared as the old paths compared. The draft uses the same order.
   - Add a conformance case for it, and a probe repeating this one after the switch.
2. **Content values a JSON column or SQLite's JSON functions do not carry exactly** (owner: Task 8).
   - A note created with content `n: 123456789012345678901234567890`, `x: .inf`, `d: 2026-10-01`, `f: 1.50` is accepted today and reads back as the same values.
   - Python's `json` round-trips them exactly. SQLite's `json_extract` turns the large integer into `1.2345678901234568e+29`.
   - `List` narrowed by a field compares the text YAML 1.2 writes for the value (`kb.content.text`). A `boolean` field filtered by `true` and an `integer` field filtered by `3` both match today.
   - The adapter's field filter gives the same answer as that text comparison. Content reads back equal to what was written.
   - Probe both after the switch.
3. **A database that is missing, damaged, or left with side files** (owners: Task 8 for opening, Task 18 for the fault).
   - Reproduce with the standard library. `sqlite3.connect(path)` on a missing path creates an empty database. `connect("file:...?mode=rw", uri=True)` raises `OperationalError: unable to open database file` and creates nothing.
   - On a file overwritten with other bytes, `connect` succeeds and the first statement raises `DatabaseError: file is not a database`.
   - A WAL database shows `-wal` and `-shm` beside it while a connection reads, and they go when it closes.
   - So the store opens its database read-write without creating it. Damage shows at the first statement, not at opening. Every connection closes when its call ends, so a store at rest is the marker and the database alone.
   - Probe all three after Task 8, and again in Task 18.
4. **A clock that raises, or that blocks** (owners: Task 9 for raising, Task 14 for blocking).
   - Today, a client readied with a clock that raises `RuntimeError` makes a valid `Write` raise `RuntimeError` out of the client. The store is unchanged (revision 1, three entries), because stamps are read before any write.
   - After Task 8 the clock is read after the draft and before the landing transaction. No read transaction may stay open across it. In WAL mode, a connection that took its read snapshot before another writer committed fails `BEGIN IMMEDIATE` with a busy-snapshot error instead of waiting. Task 14's scenarios hold a change inside a blocking clock while another lands, so they show this at once.
5. **A directory for import holding files that are not artifacts** (owners: Tasks 16 and 17).
   - A store made today has `kb/` holding `.git`, `decision`, `journal`, `schema` and `store.yaml`.
   - The check and the import pass over exactly `.git/`, `journal/` and `store.yaml` at the directory's top, an old store's history and marker (decided, see Task 16).
   - Anything else that is not `<kind>/<slug>.yaml` is reported. That covers a stray `README.md`, a file one level too deep, or a `.yaml` under a folder whose name is not a plain kind. It is either "cannot be read as YAML 1.2" or "not in canonical form", never passed over silently.
   - Probe against a store's `kb/` made by the code at `c9d450b` (kept under `.superpowers/batch23/old-store/` before Task 8 removes git), and against an export with a `README.md` added.

No questions for the spec remain open from planning. The seven found were answered on 2026-10-01 (slices plan log, "Batch 23 planned"), and each answer appears below as a decision in the task it governs.

---

### Task 1: Slice 102.7, a snapshot's request is converted in one call

**Check** (seventh review's R2, made concrete):
- `grep -n "values\." src/kb/servicer.py` gives only the `values.Refused` line (21).
- `grep -n "signatures\." src/kb/servicer.py` gives none.
- `servicer.py` stays under 150 lines.
- Review 6's snapshot refusals give the same faults in the same order:
  - `.venv/bin/python -m pytest -q -p no:warnings -m "slice-37 or slice-93 or slice-96"` gives `27 passed`, before and after;
  - `tests/test_snapshot_what_a_piece_of_work_read.py` gives `7 passed`.
- The suite gives `230 passed, 7 failed`, with the same 7.

**Where it lands:**
- `requests.py` gains one conversion of a whole Snapshot request. It returns the names, each converted or standing as its `Refusal`, and the reader's signature.
- The servicer's Snapshot makes that one call and one domain call, as every other rpc does.

**Decided:** the signature's faults come first and alone (adrs/0014, `decision/0014-signature-refused-before-operations`): the role's, then the message's, then the piece of work's. Names are judged only for a signed request.

- [ ] Run the three commands above and record their answers.
- [ ] Make the change.
- [ ] Run the check: expect the same answers and the greps clean.
- [ ] Log the checkpoint, set 102.7 green, and commit.

### Task 2: Slice 102.8, the journal has no clock but the one a client gives, or the machine's

**Check:**
- `grep -n "def now\|journal.now" src/kb/*.py` gives none.
- With no clock given, `journal.py` reads the machine's clock in its one place, and that is not a module function a client can replace.
- `grep -n "kb_journal\|setattr(.*now" tests/*.py` gives none.
- kb's dated steps (`today is {day}` in `tests/test_read_the_journal.py:85-97`, and the conftest Given "the client was readied with a clock that reads {reading}") use the published `connect(clock=...)`. The clock helper is written once, in `tests/calls.py`.
- `tests/test_read_the_journal.py` gives `27 passed`, and the suite gives `230 passed, 7 failed`.

**Why it can go now:** the slice plan's log of 2026-09-28 records that shop-knowledge landed its slice 50.23 and no longer replaces `kb.journal.now` (the slice's Needs).

**Where it lands:**
- `journal.py`: the default clock.
- The tests: every Given that builds a client in a dated scenario takes the clock fixture `today is` gives, and passes it to `connect`. The clock moves on a second at each reading, as today.

- [ ] Run `tests/test_read_the_journal.py`: expect `27 passed`.
- [ ] Make the change.
- [ ] Run the check.
- [ ] Log the checkpoint, set 102.8 green, and commit.

### Task 3: Slice 102.9.1, the retired scenarios' steps and fixtures are gone

**Check** (ninth review's R1, as the slice plan states it):
- The suite gives `230 passed, 7 failed`, the same 7.
- `test ! -e tests/test_a_file_the_store_cannot_read.py && test ! -e tests/repositories.py` succeeds.
- `grep -n "MANGLED\|REPOSITORIES\|WORKING\|named_repository" tests/*.py` gives none.
- No step function is left that no scenario runs. A step-usage probe shows this: a pytest plugin under `.superpowers/batch23/` that records each step function a scenario runs through `pytest_bdd_before_step`, compared with every step function defined in `tests/`.

**Where it lands:** every row of the review's "Dead after the retired scenarios" table. Two things need care:
- **`conftest.py`'s history Then** (`:175`) is the one live use of `repositories.git`. It keeps its check through a private helper in `conftest.py` until Task 5 takes it into the one test module that knows how the store is kept. The `git` there keeps its cleared environment.
- **Slice 112.1 needs the Given that goes with this file.** `tests/test_a_file_the_store_cannot_read.py` holds "a store holding a decision, a process and a tag, each of a kind the store holds a type for" and the `CALLS` table, both of which slice 112.1 (the damaged database) needs. They go now, as dead code. Task 18 writes its own, recovering the texts from `git show HEAD:tests/test_a_file_the_store_cannot_read.py` at this task's parent commit.

**Folded in:** the review's C10. `conftest.py:28` stops reading pytest's private `config._tmp_path_factory`. The isolation guard takes pytest's public base temp through a session-scoped autouse fixture, refusing as it does now.

- [ ] Write the step-usage probe and run it: expect the review's 38 unused step functions.
- [ ] Remove them, and the fixtures, constants and modules only they used.
- [ ] Run the check: the probe reports none unused, the greps are clean, and the suite gives `230 passed, 7 failed`.
- [ ] Show the guard still refuses: point it at a store made above a scratch base temp under `.superpowers/batch23/`, and log it.
- [ ] Log the checkpoint, set 102.9.1 green, and commit.

### Task 4: Slice 102.9.2, kb's declared dependency floors match what its generated code and suite need

**Check** (ninth review's R4):
- `grep -n "protobuf\|grpcio\|ruamel\|pytest" pyproject.toml` shows these bounds:
  - `protobuf>=7.35.1,<8`, because the generated code checks for it at import (`kb_pb2.py:12-19`);
  - `grpcio>=1.84.0`, because `kb_pb2_grpc.py:8-23` raises below it;
  - `ruamel.yaml>=0.19.1,<0.20`;
  - `pytest>=9,<10` in `dev`, until pytest-bdd stops passing `baseid` (C7);
  - `grpcio-tools>=1.84.0` in `dev`, so that `make contract` regenerates code the runtime floor accepts.
- A golden-bytes test of `canonical.dump` passes.
- A fresh virtualenv under `.superpowers/batch23/floors/`, with each floor installed exactly, runs `python -c "import kb.client"` and the suite with the same answer.
- The suite gives `231 passed, 7 failed`: the golden test is the one new test.

**Where it lands:**
- `pyproject.toml`.
- One new test module, `tests/test_the_canonical_form.py`. Through `canonical.dump`, it pins the bytes of one artifact that exercises a short and a long prose body, a list under its key, an empty section body, an integer, a boolean and a date-like string.
- **Folded in, C3:** the emitter's `width` becomes a large integer instead of `float("inf")`. The golden test shows the bytes do not move.

- [ ] Write the golden test against today's bytes and see it pass.
- [ ] Change `width`, and see it still pass.
- [ ] Set the floors.
- [ ] Build the floors virtualenv and run the check there. Log the exact versions installed.
- [ ] Run the suite: expect `231 passed, 7 failed`.
- [ ] Log the checkpoint, set 102.9.2 green, and commit.

### Task 5: Slice 102.9.3, steps see the store only through the contract or one test module that knows how it is kept

**Check** (ninth review's R2):
- `grep -nE '/ "kb"|"kb" /|"journal"|"git"|git\(' tests/*.py | grep -v '^tests/held.py'` gives none.
- `grep -n subprocess tests/*.py` gives only `tests/conftest.py`'s `_kb` runner of the command line (in `tests/test_look_after_a_store.py` until Task 15 moved it) and, since Task 14, `tests/at_once.py`'s runner of the other program a scenario's held client runs in (`InAnotherProgram`).
- The suite gives `231 passed, 7 failed`, the same 7.

**Where it lands:** a new test module, `tests/held.py`, the only test code that knows how the store is kept. Task 8 rewrites this module alone. Its public functions, each named for what a step asks:
- the artifact the store holds under a name;
- its canonical text and that text's fingerprint;
- the history, read through the `Journal` rpc;
- what the store holds, as one opaque value that steps compare before and after;
- what a directory holds apart from any store inside it, together with what that store holds, for "nothing written anywhere";
- whether a directory has a store, or anything, in the place a store goes, and occupying that place for the start-a-store corners;
- planting an artifact behind the store's back, for check-the-store's violation Givens and the operator's "store needing attention".

Every step the review lists under "Not met 1" calls it. The three `_everything_under` copies and every `_git` helper collapse into it (deferred minor 9).

**Decided:**
- "What the store holds" is compared as an opaque value, never as file bytes in a step. So when the files become a database in Task 8, no step changes.
- The steps' assertions about git commits go. The history a step checks is the entries `Journal` gives (keep-the-history), and `decision/kb-runs-no-git` supersedes the commits. So `tests/held.py` runs no subprocess.
- The start-a-store Then "none of them is the store's concern" asks the store through the contract (`Validate`, and what the store holds) instead of `git ls-files`.

- [ ] Write `tests/held.py` over today's files.
- [ ] Move each listed step onto it, one test module at a time, running that module after each move.
- [ ] Run the check.
- [ ] Log the checkpoint, set 102.9.3 green, and commit.

### Task 6: Slice 102.9.4, reads reach the store only through its own methods

**Check** (ninth review's R3):
- `grep -nE "store\.(dir|path)|journal\.(entries|digest)\(" src/kb/query.py src/kb/read.py src/kb/check.py` gives none.
- The suite gives `231 passed, 7 failed`.

**Where it lands:**
- `store.py`'s `Store` gains a method for the history and a method for an artifact's fingerprint.
- `query.entries` and `query.snapshotted` call those methods.
- `store.py` is at 249 lines. Make room first, inside `store.py`'s own concern: fold the `Damaged`/`readable` docstrings, or move `vacant`'s refusals so the module stays at 250 or fewer. If that is not enough, split discovery (`find_above`, `working_directory`, `locate`, `_nothing_found`) into a module of its own with a CLAUDE.md row. Task 8 needs that split anyway.

- [ ] Make the change.
- [ ] Run the check and `wc -l src/kb/store.py`: expect 250 or fewer.
- [ ] Log the checkpoint, set 102.9.4 green, and commit. The tenth review (Task 7) falls due now.

### Task 7: Slice 102.9.5, the tenth architecture review

**Check:**
- The review of the code's shape against CLAUDE.md, after the six slices 102.7 to 102.9.4, is in the slices plan's Log.
- Every refactor it calls for is a slice of its own with a check, or is marked superseded by slice 103.

**Who does it:** the controller dispatches the shopsystem-bdd:architecture-reviewer agent with the report path, `/home/vscode/kb-reviews/tenth-review.md` (beside the ninth). The agent changes nothing else.

**What the implementer does:** nothing. Wait for the controller to log the review, cut its slices and mark 102.9.5 green.

**What the review has to work from:**
- the suite's answer, `231 passed, 7 failed`, with the same 7 as `.superpowers/batch23/failing-before.txt`;
- `wc -l src/kb/*.py`;
- the seam `tests/held.py` (R2) and the store's new history and fingerprint methods (R3), which slice 103 builds on;
- the ninth review's items superseded by 103 and not cut. The review confirms they are still superseded, not re-cut.

**After it:**
- A refactor it cuts that must come before slice 103 stops the batch here, so the controller can amend this plan (Global Constraints).
- Otherwise Task 8 begins.

- [ ] (Controller) Dispatch the reviewer, log its report, cut its slices, and set 102.9.5 green.
- [ ] (Controller) Decide whether any cut slice must come before 103, and amend this plan if so.


### Task 8: Slice 103, the store keeps its artifacts and history in one database behind the port

**Check:**
- `make test` gives every scenario green before as green after: `253 passed, 7 failed`, the same 7 as `.superpowers/batch23/failing-before.txt`. That is 231 plus C = 22 conformance tests.
- A store started by the client, and one started by `kb init`, each hold `kb/store.yaml` and `kb/store.sqlite3` and nothing else once the call has returned: `ls -A <root>/kb`, and `test ! -e <root>/kb/.git`.
- Nothing under `src/kb` runs git: `grep -n "subprocess\|\"git\"" src/kb/*.py` gives none.
- `wc -l src/kb/*.py`: every module at 250 or fewer, and `servicer.py` under 150.

**Unknown, and how this plan answers it.** Does the port as the spec states it carry every existing read and write without a change any scenario can see? Yes, if three things hold:
- The domain already reads its corpus through three methods (`holds`, `artifact`, `ids`). The port's reads carry those same three, so `composition`, `validation`, `links`, `definitions` and `edits` do not change.
- The store-wide scans become port reads with the same answers: `read._inbound`, `query._inward`, `query.listing`, `query.found`, the history and the snapshot's fingerprint.
- The write path changes only where it writes: one `land` in place of files, journal files and a commit.

The 102.9.3 seam is what keeps the scenarios green: the steps never saw files.

**Decided** (spec line in brackets):
- **The port** is a Python interface in `port.py`, not published [check-a-change, Implementation; `decision/storage-behind-a-port`].
  - Each change carries: the operation, the artifact's id, its whole content after the change (none for a removal), its links (field, place, target artifact and part, and the allowed kinds), its parts by place, and the revision it was read at.
  - The history entries, named by `journal.py`, ride with the set.
  - The port's own refusals are named exceptions defined in `port.py`. `conflict` covers a moved revision, and an entry id already held. `linked` names each link into what the set removes, an artifact or a part. A further refusal covers a link landing nowhere or on a kind not allowed. `Unreadable` covers the database. None of these is published.
- **In this slice kb translates none of the port's refusals.** kb's draft already refuses everything a single-writer store can meet, except a dropped item that something links into. An untranslated port refusal is a named exception that escapes. Task 9's wrapper makes it a fault, Task 10 translates `linked`, and Task 14 translates `conflict` and the landing refusal. This keeps 103 an enabling slice: no scenario it keeps green meets a port refusal.
  - kb does not yet hand the implicit link to an artifact's type. That is Task 11, so a type's removal answers as it does today.
- **What is stored** [keep-the-history, Implementation; `decision/past-states-kept-not-yet-read`]:
  - each artifact's current content, and its content at every revision;
  - the link index, both ways, into parts too;
  - the search rows, per section and per field;
  - the history rows.
- **Content and fingerprints.** Content goes in as JSON text, which round-trips every value kb accepts (risk class 2). A fingerprint is sha256 of `canonical.dump` of the content, which is the same text and bytes kb wrote before ("fingerprinted from the canonical text").
- **Search.** The adapter's FTS rows narrow to candidate artifacts holding any word searched for. `search.rank` still ranks them, by term frequency in a section, as today (`decision/search-ranking`).
  - The candidates must be a superset of what `search.rank`'s whole-word match finds. FTS5's default tokenizer splits on underscores and folds diacritics, both of which only widen the set.
  - Ties keep the order of risk class 1.
- **History.**
  - Rows are read oldest first by moment and then by seq, as `journal.entries` sorts today, never by insertion order: a client's clock may go back.
  - `since` compares moments, not their ISO text.
  - `journal.py` asks the port which ids are held at a moment, and decides the next one itself (rule 6).
  - A snapshot lands through `land` with no changes and its one entry.
- **Connections.**
  - A database opens read-write and is never created by opening (risk class 3). WAL mode is set once, when the database is made, never on opening.
  - Each call opens its connection inside the rpc's wrapper, never in `KbServicer.__init__`, and closes it when the call ends. Every write is one `BEGIN IMMEDIATE` transaction.
  - A call's reads end their transaction before the clock is read (risk class 4).
  - A busy timeout is set on every connection. The spike found that `BEGIN IMMEDIATE` serialises writers before any read, so the second validates against the first's result.
- **Removed names.** A removed name may be held again [name-artifacts-and-items, "A name is free again once what held it has been removed"]. The spike's adapter kept removed ids taken; kb's must not.
- **Starting a store** [start-a-store; ninth review, deferred minor 7]:
  - the clock is read;
  - `vacant` is checked;
  - the directory is made;
  - the database is made and the type of types landed with its entry;
  - the marker is written last.
  If making the database raises (`sqlite3.Error` or `OSError`, both named), the directory it made is removed and the error re-raised, so a failed start leaves nothing.
- **Modules** [check-a-change, Implementation]:
  - `store.py` keeps discovery, the marker, `vacant`, the marker's value, and where the database lies beside the marker, which it hands to the adapter.
  - `Draft` moves to a new `draft.py` ("the store as a set's changes would leave it, read like the store"). It answers the corpus methods and links in, over the port.
  - `journal.py` names entries and fingerprints them, and writes no files.
  - `write.py` drafts, settles stamps and lands.
  - Git code goes.

**Reuse:** the spike's conformance suite gives the cases below, rewritten for kb's port, where kinds, shapes and composition stay above the port. Cite it as findings; take nothing of its code.

**Conformance cases** (one test each, C = 22, in a new `tests/test_the_storage_port.py`, parametrised over the adapters, which is SQLite only today, each in its own `tmp_path`):
1. a new database holds nothing, and a landed create reads back equal;
2. `holds`;
3. names in the order of risk class 1;
4. a set lands whole or not at all;
5. a replacement read at a moved revision is refused `conflict` and writes nothing;
6. two writers to one artifact on two connections: the second is refused `conflict`;
7. a removal and a new link to it on two connections never both land;
8. a link must land on an artifact or part of an allowed kind;
9. two new artifacts in one set that link each other land;
10. removing an artifact something outside the set links into is refused `linked`, naming each link;
11. a replacement dropping a part something links into is refused `linked`;
12. a link handed as the implicit type link blocks the type's removal, while the adapter knows nothing of kinds;
13. a removed name may be held again;
14. names by kind with field equality on the text form (risk class 2);
15. links out of an artifact and out of one place in it;
16. links in, narrowed by field and source kind, into parts too;
17. inbound counts by source kind and field, each source counted once;
18. traversal to a depth, each artifact once, by the shortest route, with the route;
19. search candidates per section and per field, keeping the section title;
20. history filtered by artifact, role, piece of work, moment and set, oldest first by moment then seq;
21. an entry id already held is refused `conflict`;
22. content as of an earlier set.

**Steps, in order, each verifiable.** Task 8 is one task (one slice) in three commits, so a reviewer can gate each.

- [ ] **Before any change:** keep a store made by today's code, with a decision type, a decision and some history, under `.superpowers/batch23/old-store/`. Review Focus 5 and Task 17 probe it after git is gone.
- [ ] **Commit 1, the port and its adapter, not yet wired.**
  - [ ] Write `port.py`: the interface, the change, link and entry values, and the refusals.
  - [ ] Write the 22 conformance tests. Run `.venv/bin/python -m pytest -q -p no:warnings tests/test_the_storage_port.py` and see each red, because no adapter exists yet.
  - [ ] Write `sqlite_store.py` (schema, opening, the landing transaction) until they pass: expect `22 passed`.
  - [ ] Watch the size. The spike's adapter was 749 lines, with kinds and shapes below its port. If `sqlite_store.py` would pass 250, split first: the reads go to `sqlite_reads.py`, the landing transaction stays. Each gets a CLAUDE.md row.
  - [ ] Run the whole suite: expect `253 passed, 7 failed`.
  - [ ] Commit.
- [ ] **Commit 2, the switch.** Files and the database cannot both be the store, so these land together:
  - [ ] Make the history rows: `journal.py` builds entries and fingerprints and writes nothing.
  - [ ] Move `Draft` to `draft.py`.
  - [ ] Land `write.start`, `write.land` and `write.record` through the port, with the start order above (marker last).
  - [ ] Route the reads through the port: `read._inbound` to inbound counts; `query._inward` to links in; `query.listing` to names by kind; `query.found` to search candidates then `search.rank`; `query.entries` to the history; the snapshot's fingerprint through the Task 6 method.
  - [ ] Make `check.everything` read every artifact through the port.
  - [ ] Reduce `store.py` to discovery and the marker.
  - [ ] Make the servicer open the port inside each rpc.
  - [ ] Rewrite `tests/held.py` over the port's public functions. Planting a dangling link for check-the-store's violation Given ("another points at something the store does not hold") cannot go through `land`, which refuses it, so `tests/held.py` writes those rows itself: it is the one module that knows how the store is kept.
  - [ ] Run the whole suite: expect `253 passed, 7 failed`, the same 7. Any other failure is a seam or port gap, fixed here.
  - [ ] Commit.
- [ ] **Commit 3, what the switch left dead.**
  - [ ] Remove:
    - git: `store._git`, `_locating`, `QUIET`, `Store.commit`;
    - the damaged-file machinery: `store.Damaged`, `readable`, `Store.load`'s damaged branch, `journal.entries` over files, `query`'s `readable`, `validation._refusal_behind`, the file wording of `refusals.unreadable`, `check._with_type`'s damaged half;
    - `settled.lacking`, unless still used.
  - [ ] Update the CLAUDE.md rows and rules 3 and 4 (Global Constraints).
  - [ ] Run the check.
  - [ ] Run Review Focus 1, 2 and 3 as probes under `.superpowers/batch23/`.
  - [ ] Probe a failed start: replace the adapter's make with one that raises, in a probe only. Expect nothing left under the root.
  - [ ] Log the checkpoint, set 103 green, and commit.

### Task 9: Slice 104, a clock that fails during a change leaves the store as it was

**Scenario** (`@slice-104`, 1): `change-the-store` / The clock fails during a change.
- `.venv/bin/python -m pytest --collect-only -q -m slice-104` collects 0 today, and 1 once bound.

**Why red:**
- Not collected today: the feature is bound by title, and this title is not.
- Once bound, its Given "the client was readied with a clock that fails when it is asked the time" is undefined.
- With steps, the When raises `RuntimeError` out of the client. The probe reproduced this: `servicer.py:21` catches only `values.Refused`.
- "The store holds what it held before" already holds, since stamps are read before any write.
- The published-contract test `tests/test_the_published_contract.py::test_the_rule_names_kb_gives_are_exactly_the_spec_lists` still reads the rule list from the old design note (`docs/superpowers/specs/2026-09-23-kb-design.md`, "kb's own rule names are: ..."). That list has no `clock`, so adding `rules.CLOCK` alone turns that test red.

**Binding:** bind by title with `@scenario` in `tests/test_change_an_artifact.py`, which holds "a store holding a decision with a purpose and a rationale, at its first version" and "the client replaces the decision, saying which role and why".
- That When builds its own client. Let the failing-clock Given give the client the When uses, as the conftest clock Given does with `target_fixture="client"`.
- New steps: the failing-clock Given; "the client is given a fault" (a response of the rpc's type carrying a fault, never an exception); "the store holds what it held before" in this module, through `tests/held.py`.

**Where it lands:**
- `servicer.py`'s one wrapper turns any exception that escapes the domain into a fault, with nothing written, as CLAUDE.md rule 1 already requires.
- The servicer hands the domain its own wrapping of the client's clock. A clock that raises, or that gives something other than a `datetime`, surfaces as a named clock failure, which the wrapper turns into the `clock` fault. So the clock's failure is told apart from any other without a broad `except` outside `servicer.py`.
- `rules.py` gains `CLOCK = "clock"`, and `refusals.py` makes the fault.
- The published-contract test's rule-list check moves from the old design note to `spec/index.md`'s sentence "kb's own rule names: ...", which now ends with `clock`. So the pinned set and `rules.ALL` agree, and they keep agreeing with the spec that publishes them.
- The unknown ("without catching broad exceptions anywhere else") is answered by `grep -n "except" src/kb/*.py`: only `servicer.py` catches broadly.
- The port's `Unreadable` stays for Task 18.
- `servicer.py` stays under 150 lines; check `wc -l`.

**Decided:**
- [change-the-store, Implementation: "Every rpc runs inside one fail-closed wrapper, so an exception a clock or the database raises becomes a fault." and "A clock that fails during a change gives a fault with rule `clock`, no artifact and no path."; `decision/clock-failure-rule`]
- The fault carries rule `clock`, no artifact and no path. Its message says the clock failed and gives the exception's own text.
- Any other escaping exception gives a fault too, with no new rule invented: a database error carries `unreadable` (decision/damaged-database-one-fault), and anything else carries the existing rule `store`, no artifact and no path. Decided by the controller on the person's authority, 2026-10-01; no scenario pins it.
- This also closes the ninth review's deferred minors 1 and 2.

- [ ] Bind the scenario and run slice-104: see it red on the undefined Given.
- [ ] Write the steps and see it red on the escaping `RuntimeError`.
- [ ] Make it green. In the same change, add `clock` to `rules.py` and move the published-contract test to `spec/index.md`. Run `tests/test_the_published_contract.py`: expect `6 passed`.
- [ ] Probe a clock that returns `None`: expect the `clock` fault, and nothing written.
- [ ] Run the whole suite: expect `254 passed, 7 failed`.
- [ ] Log the checkpoint, set 104 green, and commit.

### Task 10: Slice 105, dropping an item something links into is refused

**Scenario** (`@slice-105`, 2 rows): `change-the-store` / A replacement that leaves out an item something links into is refused (a whole replacement; a placed replacement of the collection).
- Collects 0 today, and 2 once bound.

**Why red:**
- Not bound today.
- Probed before Task 8: a whole `Write` dropping a linked option, and a placed `Write` of `options` dropping it, both answer revision 2 with no fault.
- After Tasks 8 and 9, the adapter refuses `linked` (conformance case 11), but kb does not translate it. The client gets Task 9's generic fault, so the rows are red on "rejected because something still points at that item" (rule `on_delete`) and on "given each link into that option".

**Binding:** bind by title in `tests/test_change_an_artifact.py`, reusing:
- "a store holding a decision with a purpose and a rationale, at its first version";
- "the decision carries two options" (`:348`).

New:
- "another artifact links into one of those options", which needs a test type whose link field allows parts (`parts: true`, targets `decision`), beside the types in `tests/calls.py`;
- the two Whens of the outline's `<change>`;
- the two Thens.

**Where it lands:** `write.py` translates the port's `linked` into one `on_delete` fault per link, made in `refusals.py`. The fault names the linking artifact as `artifact` and the link's place as `path`. Its message names the item (`<artifact>#<collection>/<item>`) or, for a whole artifact, the artifact.

**Decided:**
- [check-a-change, Implementation: "linked reaches the client as a fault with rule on_delete, naming each link"; `decision/integrity-checked-both-ways`]
- The refusal comes from the port's check inside the landing transaction (check-a-change, Implementation). kb's draft keeps its own whole-artifact removal check, now reading links in through the port. Faults the draft finds come back alone, without calling the port, as every refused draft does today.

- [ ] Bind, run slice-105, and see both rows red: first on undefined steps, then on the generic fault.
- [ ] Make each row green in turn.
- [ ] Run the whole suite: expect `256 passed, 7 failed`.
- [ ] Log the checkpoint, set 105 green, and commit.

### Task 11: Slice 106, removing a type still in use is refused

**Scenario** (`@slice-106`, 1): `define-a-type` / Removing a type while the store holds artifacts of its kind is refused.
- Collected today (1, failing). `tests/test_define_a_type.py` binds the whole feature with `scenarios(...)`.

**Why red:**
- Today, `StepDefinitionNotFoundError` on "a type the store holds, and two artifacts of its kind".
- Probed: removing `schema/vote` while `vote/mine` exists answers revision 2 with no fault. Afterwards `List` of that kind is refused `kind`, and `Validate` reports `kind` twice.
- After Task 8 nothing changes this, because kb hands no implicit link yet.

**Binding:** new steps in `tests/test_define_a_type.py`: the Given (a type and two artifacts of its kind), the When "the client removes that type", and the Then "naming each of those two artifacts".

**Where it lands:** each change kb hands the port carries one more link, to `schema/<kind>`, so the adapter refuses `linked` and Task 10's translation names each artifact.
- kb's draft check of a type's removal reads the same links in through the port.
- Every read keeps the implicit link out: links out and in, inbound counts and traversal answer as they did. Probe `Refs` into `schema/decision` and its summary read before and after: expect nothing reached and no counts, both times.

**Decided:**
- [define-a-type, Implementation: "Every artifact carries one implicit link to its type artifact (`schema/<kind>`); removing a type in use is refused with rule `on_delete`, naming each artifact of its kind"; check-a-change: "the adapter knows nothing of kinds"]
- Each fault's `path` is empty: the link is the artifact's own, not a place in its content. Faults come in name order (risk class 1).
- `schema/schema` carries its implicit link to itself, which never blocks anything, since a link from inside the removed artifact does not count.
- The implicit link is internal: it is never shown by reads, link listings or inbound counts. It shows only in the refusal it causes (controller's answer of 2026-10-01, slices plan log). The port marks it so that its reads can leave it out, while the adapter still knows nothing of kinds.

- [ ] Run slice-106 and see it red on the undefined Given.
- [ ] Write the steps and see it red on the accepted removal.
- [ ] Make it green.
- [ ] Run the read probe.
- [ ] Run the whole suite: expect `257 passed, 6 failed`.
- [ ] Log the checkpoint, set 106 green, and commit.

### Task 12: Slice 106.1, the whole-store check holds no kind-with-no-type finding

**Check** (ninth review's R5):
- `grep -n "named_type" src/kb/*.py` gives none.
- CLAUDE.md's `check.py` row no longer names "an artifact of a kind with no type", nor a file that cannot be read.
- The suite gives `257 passed, 6 failed`, the same 6.

**Where it lands:**
- `composition.named_type` and its `artifact` parameter fold into `kind_type`.
- `check.everything` takes each artifact's type through `composition.kind_schema`.
- `refusals.no_type` loses its `artifact` parameter if nothing else passes one.

- [ ] Make the change.
- [ ] Run the check.
- [ ] Log the checkpoint, set 106.1 green, and commit.

### Task 13: Slice 107, a set's links are checked against the state the whole set leaves

**Scenarios** (`@slice-107`, 5, all collected and failing today):
- `make-several-changes-in-one-go` / A change in a set points at what another change in it makes, earlier or later (4 rows);
- `make-several-changes-in-one-go` / Two new artifacts in one set that point at each other land.

**Why red:**
- Today: `StepDefinitionNotFoundError`.
- Probed with the Background's store:
  - "a decision to be created and the work item to point at it" lands;
  - "a decision to be created and that decision to be replaced" lands;
  - "a decision to be replaced and that decision to be created" is refused `not-found`.
  These three rows are pins of slice 5's set and of acting in order (slice 85). Credit them once their steps exist, seen red only as undefined steps.
- "the work item to point at a decision and that decision to be created" is refused `ref` at `work-item/... decisions/0`.
- The mutual pair is refused `ref` at both `supersedes`. These two are the real reds.

**Binding:** `tests/test_make_several_changes_in_one_go.py` binds the whole feature.
- Row 1's When text is the existing When (`:42`).
- Row 4's Then is the existing `:201`, which reads `attempt`, so the new When for that row returns the same `attempt` shape.
- New: the When for rows 2 to 4 and the mutual pair, and the Thens "the set lands, and ...".
- "Given the decision type lets a decision point at another decision": `DECISION_TYPE`'s `supersedes` already does.

**Where it lands:**
- `edits.py` acts in order: names, not-found, revisions, items named, each against the draft as the operations before it left it. It no longer checks content.
- `write.py` checks every artifact the set touched once, against the draft's end state: content against its type as the set leaves it, links landing, and a type checked as a type. Faults come in the order of the operations, every one of them (`decision/every-fault-at-once`).
- A removal's inbound check moves to the end state too. Only links that the set's end state still holds block a removal. The draft reads them through the port, minus the links the set removed or replaced, plus those it added.
- CLAUDE.md's `edits.py` row changes to say so. `write.py`'s row already says "validate the whole draft".
- `edits.py` is at 182 lines and `write.py` at about 130 after Task 8. If either would pass 250, split first.

**Decided:**
- [`decision/a-set-is-checked-whole-links-and-types`: "A set's links and types are checked once against the state the whole set leaves ... while each change acts on the store as the changes before it in the set left it"]
- The version an artifact records is the version of the type it was checked against, which is the set's end state [change-the-store L1].
- A removal whose blocking link is removed later in the same set lands: links are judged against the set's end state [`decision/a-set-is-checked-whole-links-and-types`; controller's answer of 2026-10-01, slices plan log].
  - Reproduction of today's refusal: create `decision/old` and `decision/new` (`supersedes: decision/old`), then Apply `[remove decision/old, remove decision/new]`. Today it is refused, `on_delete` at `decision/new` `supersedes`. After this task it lands.
  - No scenario pins this, and none is added. Probe it under `.superpowers/batch23/` and log the result.
  - The existing scenario "a set in which the second change removes an artifact something still points at" stays refused, because the work item that points there is outside the set.

- [ ] Write the steps. Run slice-107: rows 1, 3 and 4 green (credited), row 2 and the pair red on `ref`.
- [ ] Make them green.
- [ ] Run the removal probe above.
- [ ] Run the whole suite: expect `262 passed, 1 failed` (slice 113's).
- [ ] Log the checkpoint, set 107 green, and commit.

### Task 14: Slice 108, clients on one machine changing one store at once

**Scenarios** (`@slice-108`, 5 rows). Collects 0 today, and 5 once bound.
- `change-the-store` / Several clients on one machine change one store at the same time (two rows: one program, two programs);
- `change-the-store` / A removal and a new link to the same artifact made at once never both land (2 rows);
- `change-the-store` / Two clients replace one artifact at the same time.

**Why red** (after Tasks 8 to 13):
- The client that lands second drafted against the state before the first landed. The adapter refuses it `conflict`, kb does not re-draft, and the client gets Task 9's generic fault.
- So the rows are red on:
  - "the process holds both new steps";
  - "each replacement left a version of its own" (the replacement race);
  - "the new decision is rejected because a link must land on a node of a kind the type allows". In the removal-first row, the port's landing refusal is untranslated, so the client gets the generic fault, not `ref`.
- The creation-first row may already be green through Task 10's `linked` translation. If so, credit it, seen red only as undefined steps.

**How a scenario makes two changes land in a chosen order** (the slice's unknown, answered with the published clock):
- The client that must land second is readied with a clock that blocks. When it is first asked the time, it signals that it is waiting and waits for a go.
- kb reads the clock after drafting and before the landing transaction (Task 8), so that client is held with a draft of the old state.
- The other client's change then runs to the end, the go is given, and the held client lands second.
- In one program the held client runs on a thread. In two programs it is a small helper program under `tests/`, run with the suite's interpreter, whose clock waits on files in the test's `tmp_path`.
- The helper's runner sits beside the command-line runner, so one test module runs subprocesses. Update the Task 5 check to name it.

**Binding:** each scenario binds by title with `@scenario` in the module that holds its Given:
- the first in `tests/test_add_an_item_to_a_collection.py` ("a store holding a process with two steps and a shared step other processes use", `:126`);
- the second in `tests/test_remove_an_artifact.py` ("a store holding a tag nothing points at", `:42`);
- the third in `tests/test_change_an_artifact.py` (`:84`).

The gate (the blocking clock, the thread and the program runner) is written once, in a shared test module.

**Where it lands:** `write.py`. On `conflict`, kb re-drafts the operations against the new state and lands again:
- The stamps already read are kept, and the clock is not read again.
- Entry ids are minted again.
- The rounds are bounded by a module constant. Past it, the escaping refusal becomes Task 9's fault.
- The port's landing refusal becomes `rules.REF` with validation's message ("a link must land on a node of a kind the type allows; ...").

**Decided:**
- [`decision/write-lock-on-one-machine`: "on a mismatch, the change re-drafted against the new state and landed, so no client sees a conflict"]
- [change-the-store L17: without an expected revision, "the later replacement's content still wins"]
- Each connection's busy timeout lets the second writer wait rather than fail.
- No read transaction stays open across the clock (risk class 4).

- [ ] Bind each scenario, see it red, and make it green one at a time: the one-program row first.
- [ ] Run each new scenario 20 times (`--count` is not installed, so loop the command) and log that none flakes.
- [ ] Run the whole suite: expect `267 passed, 1 failed`.
- [ ] Log the checkpoint, set 108 green, and commit.

### Task 15: Slice 110, the operator exports the store

**Scenarios** (`@slice-110`, 5). Collects 0 today, and 5 once bound.
- `export-and-import-a-store` / The operator exports the store to a directory that is empty or does not exist (2 rows);
- The operator opens an exported artifact's file;
- Two stores given the same content by the same client are exported;
- Exporting to a directory that holds anything is refused.

**Why red:** not bound. Once bound, `kb export` is `invalid choice`.

**Binding:** a new `tests/test_export_and_import_a_store.py`, binding this feature's scenarios by title, slice by slice. The feature draws on the operator's steps as well as its own, so they move first from `tests/test_look_after_a_store.py` to `tests/conftest.py`, where every module that needs them sees them: the command-line runner `_kb` and the operator's store-finding Givens. Tasks 16 to 18 use them too. Update Task 5's subprocess check to name the runner's new home. The file checks (identity first; prose as blocks; lists indented under their key; no folding; no tags) read the exported files, which are the operator's output, not the store.

**Where it lands:**
- A new `export.py`: "the store written out as canonical files at one moment, never over anything".
- `cli.py` gains `kb export <dir>`. `values.py` gains a directory value (Root's kin).
- The servicer runs the export inside its one wrapper, through a method that is not an rpc. That keeps rule 1 whole, and Task 18 can put `kb export` behind the same `unreadable` fault without touching the command.
- The export opens the database before it touches the directory it is aimed at. So a store that cannot be read leaves that directory as it was (Task 18).

**Decided:**
- [export-and-import-a-store, Implementation: layout `<dir>/<kind>/<slug>.yaml`, types at `<dir>/schema/<kind>.yaml`; identity keys first, in the order `id`, `type`, `schema_version`, `revision`, `title`]
- One moment: every name and artifact is read within one read transaction on one connection. WAL gives that view, unchanged by writers that land meanwhile (the slice's unknown).
- A directory that holds anything is refused. The rule is `root`, as a store's place is refused (start-a-store), and nothing is written. A directory that does not exist is made.

- [ ] Bind each scenario, see it red, and make it green in turn.
- [ ] Run the whole suite: expect `272 passed, 1 failed`.
- [ ] Log the checkpoint, set 110 green, and commit.

### Task 16: Slice 111, the operator checks a directory for import

**Scenarios** (`@slice-111`, 13). Collects 0 today, and 13 once bound.
- each error is reported by file and reason (5 rows);
- a file with an error, and files linking to it (4 rows);
- a directory that holds no error;
- one that holds an error;
- the store left as it was;
- a type that describes types differing from the store's.

**Why red:** not bound. Once bound, `kb import` is `invalid choice`.

**Binding:** by title in `tests/test_export_and_import_a_store.py`. The Givens build directories of files: from a real export (Task 15), then broken in the one way each row names.

**Where it lands:**
- A new `importing.py`: "a directory read as a set: each file's errors, the files that would be skipped because of them, with their chains". If it would pass 250 lines, the skip analysis gets its own module.
- `cli.py` gains `kb import <dir> --check`. It runs in the servicer's wrapper and opens the store's database before it reads the directory.
- The check drafts every readable file as one set, through Task 13's end-state check against the directory's types and the store's. So "how files are checked against types the directory itself brings" is answered by the same code that checks a set.

**Decided:**
- Report lines: `error <file> <rule> <message>` and `skipped <file> <chain>`, where the chain is the file names from the skipped file to the broken one. Exit 0 when clean, with a line saying so; exit 1 with errors [Implementation: "exits 0 when clean and 1 with errors"].
- Rules, from the closed list:
  - a file not readable as YAML 1.2: `unreadable`;
  - not in canonical form: its bytes are not those `canonical.dump` gives, or its place in the directory is not the export layout's place for its name and kind: `content`;
  - a kind neither the directory nor the store holds a type for: `kind`;
  - content not fitting: the JSON Schema keyword or kb's rule, as `Validate` gives;
  - a link landing nowhere: `ref`;
  - a type that describes types differing from the store's: `content`;
- A file whose path disagrees with its name or its kind, such as `decision/a.yaml` holding `id: decision/b` or `type: work-item`, is reported as not in canonical form. The export layout is part of the canonical form (controller's answer of 2026-10-01). Such a file never lands under either name.
- The directory's top-level `.git/`, `journal/` and `store.yaml` are passed over, unread and unreported. They are an old store's history and marker [export-and-import-a-store: "its history and its store marker passed over"; controller's answer of 2026-10-01]. Anything else that is not `<kind>/<slug>.yaml` is read and reported (Review Focus 5).
- The skip analysis follows each link and each artifact's implicit link to its type file [Implementation: "artifact → type file"].
- The store is never written: the check lands nothing.

- [ ] Bind each scenario, see it red, and make it green in turn.
- [ ] Run Review Focus 5 against the old store kept in Task 8 and against an export with a `README.md` added. Log what each reports.
- [ ] Run the whole suite: expect `285 passed, 1 failed`.
- [ ] Log the checkpoint, set 111 green, and commit.

### Task 17: Slice 112, the operator imports a directory into a freshly started store

**Scenarios** (`@slice-112`, 21). Collects 0 today, and 21 once bound.
- clean, signed;
- each type before its artifacts;
- refused with errors;
- errors skipped (3 rows);
- a store that is not fresh;
- an existing store's `kb` directory;
- no `KB_ACTOR`;
- the store found as `kb validate` finds it (10 rows);
- nothing would land;
- a matching type that describes types.

**Why red:** not bound. Once bound, `kb import` without `--check` is unknown.

**Binding:** by title in `tests/test_export_and_import_a_store.py`. The store-finding rows reuse the operator's store-finding Givens and outcomes, moved to `tests/conftest.py` in Task 15, as `kb validate`'s scenarios state them. "The kb directory of an existing store, ... together with its history and its store marker" is laid out by hand in `tmp_path`: an export plus a `journal/` and a `store.yaml`. No store of the old kind can be made any more.

**Where it lands:**
- `importing.py` builds one operation per file that lands, keeping its identity, revision and type version.
- `edits.py` gains what an import does to the draft.
- `write.land` lands the set through the port under `KB_ACTOR`, with entries whose op is `import`.
- The servicer's wrapper runs it.

**Decided:**
- [export-and-import-a-store, Behaviour and Implementation]
- Order: types first, each base before the types built on it, then artifacts in name order.
- The message is `import <dir as the operator named it>`.
- `schema/schema` is compared and passed over when it matches: no entry.
- A store that holds any artifact besides `schema/schema` is refused, rule `store`, and nothing is written.
- No `KB_ACTOR`: refused, rule `actor`, as `kb init` is.
- With errors, the report is printed, then the refusal: exit 2, nothing written.
- `--skip-errors` lands the rest and prints what was skipped and why. If nothing would land, it is refused and nothing is written.
- An import's history begins after the store's starting entry. Old history stays behind (`decision/files-are-an-export`; Not yet: "Carrying history across an export").

- [ ] Bind each scenario, see it red, and make it green in turn.
- [ ] Probe `kb import` of the old store kept in Task 8 (`.superpowers/batch23/old-store/<root>/kb`). Expect its types and artifacts to land, and its `.git/`, `journal/` and `store.yaml` to be passed over.
- [ ] Run the whole suite: expect `306 passed, 1 failed` (slice 113's).
- [ ] Log the checkpoint, set 112 green, and commit.

### Task 18: Slice 112.1, a store whose database cannot be read refuses every call and command

**Scenario** (`@slice-112.1`, 34 rows): `answer-a-damaged-file` / A store whose database cannot be read, because it is damaged or missing beside its marker, refuses every call and command that needs it.
- Each of the two damages has 17 rows:
  - 13 client calls (create, read, replace, add an item, remove, a set of two, list, links out, links in, search, the journal, a snapshot, the check of the store);
  - `kb validate`;
  - `kb export`;
  - the import check;
  - `kb import`.
- `.venv/bin/python -m pytest --collect-only -q -m slice-112.1` collects 0 today, and 34 once bound.

**Why red** (after Task 17):
- A database overwritten behind the store's back raises `sqlite3.DatabaseError` at the first statement. A missing one raises `OperationalError` on opening (risk class 3).
- Task 9's wrapper makes either a generic fault. Every row is red on "rejected because the store's database cannot be read, and the database is named" (rule `unreadable`). The client rows, `kb validate`, `kb export`, `kb import --check` and `kb import` all answer that way: the last four print the generic fault and exit 2.

**Binding:** a new `tests/test_answer_a_damaged_file.py`, bound by title, since the outline draws on the client's steps and on the operator's steps in `tests/conftest.py` (moved there in Task 15). It holds:
- "a store holding a decision, a process and a tag, each of a kind the store holds a type for", and the calls table, recovered from the module Task 3 deleted;
- "the store's database <damage>", through `tests/held.py`: damaged means its bytes overwritten; missing means the file taken away with the marker kept;
- "an empty directory outside the store";
- the snapshot and check Whens;
- the operator rows, through the command-line runner. "A directory exported from another store" is made with `kb export` from a second, healthy store in `tmp_path`.
- The Thens:
  - the rule `unreadable`, with the database named in the message;
  - "given as any other fault": the rpc's response type, or exit 2 with `kb <command>: refused: unreadable: ...` on stderr;
  - "nothing is written": the bytes under `<root>/kb/` and in the empty directory, compared through `tests/held.py`, which knows the store is damaged and so compares bytes, not what a read gives.

**Where it lands:**
- The adapter raises `port.Unreadable`, naming the database, for any `sqlite3.DatabaseError` on opening or on any statement.
- `servicer.py`'s wrapper turns it into the one fault, made by `refusals.py`: rule `unreadable`, no artifact, no path, a message naming `kb/store.sqlite3`.
- The command line already prints faults, and the export and import commands already open the database first (Tasks 15 to 17).

**Decided:**
- [answer-a-damaged-file, Implementation: "A database cannot be read when `kb/store.sqlite3` cannot be opened or read, or is absent while `kb/store.yaml` is present. Both cases are the same fault."]
- Damage shows at the first statement. This is the slice's unknown. No integrity check runs on opening, since a full check grows with the store and would break the bounds.
- `kb serve` is not built. Refusing to serve a damaged store is the spec's Not yet [answer-a-damaged-file, Not yet].

- [ ] Bind the outline and run slice-112.1: see every row red.
- [ ] Make the client rows green, then the operator's, one damage at a time.
- [ ] Run Review Focus 3 again.
- [ ] Run the whole suite: expect `340 passed, 1 failed` (slice 113's).
- [ ] Log the checkpoint, set 112.1 green, and commit.

### Task 19: Slice 113, the command line changes content only by importing

**Scenario** (`@slice-113`, 1, collected and failing today): `operate-a-store` / The command line changes content only by importing into a freshly started store.

**Why red:**
- Today, `StepDefinitionNotFoundError` on "it offers setting a store up, checking and exporting one, and importing into a freshly started store".
- Once defined, it is red today on what `kb --help` offers: `{init,validate}`.
- By this task, Tasks 15 to 17 have added `export` and `import`. If their help lines already say what the Then asks, the scenario is green on its steps alone. Credit it to slices 110 to 112, seen red only as an undefined step, and say so in the checkpoint.

**Binding:** `tests/test_look_after_a_store.py` binds the whole feature. Its old Thens went in Task 3. New Thens:
- the help lists exactly `init`, `validate`, `export` and `import`, each with its help line, and `import`'s says it imports into a freshly started store;
- "nothing else that changes what the store holds": any other command, `serve` and `create` among them, is `invalid choice`, as the old Then checked.

**Where it lands:** `cli.py`'s parser, and its module docstring and CLAUDE.md row ("set up, check, export, and import into a freshly started store").

**Decided:** [operate-a-store, Behaviour: "The command line offers setting a store up, checking and exporting one, and importing into a freshly started store, and nothing else that changes what the store holds."; Not yet: serving].

- [ ] Write the Thens and run slice-113.
- [ ] Make it green, or record the credit above.
- [ ] Run the whole suite: expect `341 passed`, nothing failing.
- [ ] Log the checkpoint, set 113 green, and commit.

### Task 20: Slice 114, the store meets its performance bounds at 30,000 artifacts

**Check:** `make bench`. At 30,000 artifacts, each figure is the median of 20 calls, and the command exits 0 only when every bound holds:
- a summary read: under 100 ms;
- a three-step traversal: under 100 ms;
- a single change (Create, Write, Delete each): under 50 ms;
- a set of 100 changes: under 1 s.

The suite's answer is unchanged.

**Where it lives:**
- A new top-level `bench/` directory, outside `tests/`, so pytest never collects it. The script is named for what it checks (for example `bench/bounds.py`).
- A `bench` target in the `Makefile` beside `test`, running it with the checkout's interpreter at 30,000. The script also takes a smaller count for a quick look.
- It builds its store in a fresh temporary directory under the system's temp, and removes it after.
- It reaches the store only through `kb.client.connect`, as a client does. It prints one line per figure, each with its bound.

**How the store is built:**
- The graph has about three links per artifact, after the spike's benchmark: a few hundred tags; decisions, each linking to two tags and most to the decision before; work items, each linking to two decisions.
- It is landed through `Apply` in sets of 100. Record the set's cost at 3,000 and at 30,000: the slice's unknown is whether a change's cost stays flat as the store grows. In the spike's adapter it grew tenfold from 3,000 to 30,000.

**What is measured:**
- a summary read of a decision, with stubs of what it points at and its inbound counts, and of a tag;
- three steps out from a work item, and three steps in from a decision.
  - No in-traversal starts at a tag: thousands of stubs at three steps are a read the bound does not describe. Log the figure anyway, beside the others.
- Create, Write and Delete of something nothing points at;
- `Apply` of 100 creates.

**Bounds:** copied from `spec/index.md` into the script as one table, with the spec named.

**If a bound is missed:** fix it in `src/kb/` within this task, keeping the suite's answer. The likely costs are:
- any remaining whole-store scan on the write path (`Draft.ids`, a removal's inbound check);
- the composed schema and registry rebuilt per change;
- `canonical.dump` per change;
- one connection per call.

**Decided:** [`decision/performance-bounds`; index, Testing: "checked by a benchmark kept in the repository, not by scenarios; a release that misses one does not ship"].

- [ ] Write the bench, and run it at 3,000 then at 30,000. Log both tables.
- [ ] Fix any bound missed and run again.
- [ ] Run the whole suite: expect `341 passed`, unchanged.
- [ ] Log the checkpoint with the 30,000 table, set 114 green, and commit.

## After the batch

- [ ] A whole-branch review on the most capable model, against this plan, CLAUDE.md, the spec and adrs/0018. The reviewer:
  - runs kb's suite, the conformance suite and `make bench`;
  - runs shop-knowledge's suite against this checkout's `src` through a scratch interpreter that loads it (the batch 22 review's way). shop-knowledge's steps name `<root>/kb` only through `driver.store_in`. If any reads what kb keeps inside it, that is shop-knowledge's to change (adrs/0018).
- [ ] Triage the batch's deferred minors, the review's C6 among them: a test pins jsonschema's wording in `tests/test_look_after_a_store.py`'s `REPORT`.
- [ ] Push `main`. A release, and shop-knowledge's pin bump, is the user's decision once every scenario is green.
