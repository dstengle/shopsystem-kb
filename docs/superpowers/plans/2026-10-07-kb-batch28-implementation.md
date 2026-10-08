# kb batch 28 Implementation Plan: kb served from a Docker container (kb 0.7.0)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Each task is one slice, implemented under shopsystem-bdd:bdd-red-green. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** the operator sets a store up already holding a directory of files, all or nothing, however the run ends (138, 139, 140); `kb serve --start` starts a store where there is none and serves it, leaving nothing behind when it cannot serve (141, 142, 143); `kb serve` on an unreadable database is pinned by its scenario (144); kb's image runs all of it beside its callers, reached by service name (145). Shipped as kb 0.7.0; contract v1 is added to, nothing in it changes.

**Architecture:** one new module, `staging.py`, owns a store started (and, for a seed, imported into) out of sight under the root, then put in place whole with one rename, and taken back whole when what it was started for fails. `cli.py` gains `--seed` on `init` and `--start` on `serve` and only dispatches: `kb.init` and the operator's import are called as they are today, against the staged root. The server is unchanged. The image is a root `Dockerfile` whose entry point is `kb` and whose default command is `serve /data --listen 0.0.0.0:50051 --start`, checked by `make image-check` outside the suite.

**Tech Stack:** Python 3.11 (3.12 in the image), argparse, `os.rename`, `shutil.rmtree`, grpcio 1.84, pytest-bdd 8.1, pytest-xdist; Docker Engine 29.6, Docker Compose v5.3 (probed 2026-10-07).

**Spec:** `spec/capabilities/operate-a-store.md` (Behaviour lines on kb init with a seed directory and kb serve with `--start`; Implementation lines on staging and the image), `spec/capabilities/answer-a-damaged-file.md` (kb serve on a database that cannot be read), `spec/index.md` (published image surface; Testing), `spec/decisions.md` decision/0021-kb-served-from-a-container, decision/published-contract-v1-in-0-7-0, decision/init-refuses-inside-or-above; `adrs/0021-kb-served-from-a-container.md`; note `docs/superpowers/specs/2026-10-07-kb-docker-design.md`. Slices: `docs/superpowers/plans/2026-09-24-kb-slices.md`, slices 138 to 145.

## Global Constraints

- Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts
- One task per slice, in slice order. The plan holds no code: the implementer writes steps and code under bdd-red-green, after the red run.
- The controller dispatches each task by its `Review:` and `Model:` lines: `Review: per-task` and `Model: opus` for a task touching concurrency, the published contract, data integrity or moving stored data (138, 139, 141, 142, 145); `Review: batch-end` and `Model: sonnet` for the rest (140, 143, 144). A batch-end task gets no task review; the batch's branch review covers it.
- CLAUDE.md holds: no module under `src/kb/` over 250 lines, `servicer.py` under 150; a change that would cross a limit splits first, inside the task. `cli.py` is 150 lines today and only dispatches: what a seeded start or a start for serving does lives in `staging.py`, not in `cli.py`. `values.py` is at 241 and must not grow: nothing in this batch adds a conversion there. A new module gets its row in CLAUDE.md's module map in the task that makes it (138); `cli.py`'s and `client.py`'s rows gain `kb init --seed` and `kb serve --start` in the tasks that add them.
- Rule 1: `staging.py` catches no broad exception. Taking a staged or placed store back on failure is done with `try`/`finally` or a context manager over the specific outcomes (a refusal, `ValueError` from a bind, `Refused`), or by `ExitStack` callbacks popped on success, as `server.Server.__init__` does; never `except Exception`.
- Rule 4 (draft, validate, land) is untouched: the seed lands through the operator's import exactly as `kb import` lands it, into a freshly started store, in one set.
- Only a store this run started is ever removed. Nothing in this batch removes, renames or writes anything under `<root>/kb/` that was there before the command ran.
- Every test reaches only stores, servers and Docker projects it made inside its own temporary directory or under a project name of its own, on ports the system picks; servers and compose projects a test starts are stopped and removed when it ends, passed or failed (spec Testing).
- No scenario or step definition names the staging directory (`.kb-starting`): spec Testing says "No scenario touches Docker or the place a seeded store is staged". A plain test of `staging.py`'s public functions may.
- Each task's Verify line names its marker and expected count.
- Baseline at 4e2aa58 (plan log): **645 passed, 20 failed** in 21 s: the 19 collected operate-a-store scenarios of slices 138 to 143, and `tests/test_every_scenario_is_bound.py`, failing on answer-a-damaged-file's new outline (slice 144), which no module binds yet.

### Binding values, verbatim from the spec

- Commands (operate-a-store, Implementation): "The commands are `kb init <root> [--seed <dir>]`, `kb validate` and `kb serve <root> --listen <host:port> [--start]`; the role for `kb init` and for a store `kb serve --start` starts comes from `KB_ACTOR`."
- Staging (operate-a-store, Implementation): "`kb init --seed` starts the store (`kb.init`) and imports the seed (the operator's import) under `<root>/.kb-starting/`, then moves `.kb-starting/kb` to `<root>/kb` with one `os.rename`, atomic because both lie on one filesystem. Whatever an earlier stopped run left in `.kb-starting/` is removed first. The staging directory is part of the store's files and layout, which may change, and is not published."
- Exit codes (operate-a-store, Implementation): "2 for a refusal (a seed's report printed first, as `kb import` prints it), 0 after a clean stop."
- The image's published surface (spec/index.md): "kb's image's store directory (`/data`), its port (50051), its entry point (`kb`) and its default command (`serve /data --listen 0.0.0.0:50051 --start`)."
- The image (operate-a-store, Implementation): "One `Dockerfile` at the repository's root ... a `.dockerignore` leaves out `.venv`, `.git`, `tests`, `features`, `bench` and `docs`"; "Two stages: the first builds kb's wheel; the second installs that wheel and its runtime dependencies alone into a virtualenv on `python:3.12-slim`, pinned to an exact tag"; "It runs as a user `kb`, not root. `/data` is made and owned by that user in the image"; "`ENTRYPOINT ["kb"]`, `CMD ["serve", "/data", "--listen", "0.0.0.0:50051", "--start"]`, `WORKDIR /data`, `VOLUME /data`, `EXPOSE 50051`"; "`HEALTHCHECK` is a short Python connect to `127.0.0.1:50051`, every few seconds after a short start period"; "`KB_ACTOR` has no default in the image".
- The image check (spec/index.md, Testing): "`make image` builds it, and `make image-check` runs a script against a throwaway compose project that checks that `kb init --seed` lands a small seed and a refused seed leaves the volume holding no store; `up` becomes healthy; a second container reaches `kb:50051` through a connection given by a compose config, reads and makes a change; `docker compose run --rm kb validate` answers; a stop and a start keep the store; and an empty volume with no `KB_ACTOR` exits 2 with the role's line. A release that fails it does not ship."

## Decisions this plan takes (the Behaviour leaves them open)

1. **The order of kb init --seed's refusals**, first refusal only, as `kb init` gives one today: the role (`KB_ACTOR`, the existing `cli._init` check), then the root as `kb.init` refuses it (already a store inside it, inside a store, not a directory; `store.vacant`'s faults, rule `root`), checked against `<root>` itself before anything is made, then the seed (not a directory: the import's own refusal, `refusals.not_an_import_directory`, the reason the line names, "files for import are read from a directory"), then the seed's check. Everything before staging begins writes nothing; everything after it removes the staging directory before exiting 2, so the root is left exactly as found. Rests on the seven kb init with a seed directory lines ("the directory still has no store inside it", "that store holds what it held before").
2. **A seed's report** is printed exactly as `kb import` prints it (`cli._reported`: `error` and `skipped` lines on stdout), then the refusal on stderr, exit 2. Rests on "the check's report is shown" and the Implementation line "as `kb import` prints it".
3. **What the seeded store holds**: exactly what `kb import` of the same directory into a store freshly started under the same role leaves: the same artifacts with the same names, titles, revisions and type versions, and a history of the start entry followed by the import's set, signed by the role, with the message `kb import` gives (`import <directory>`, the seed directory as named on the command line). Moments and entry ids may differ. Rests on "holding the files in the seed directory as kb import lands them into a freshly started store" and decision/files-are-an-export.
4. **Staging**: `<root>/.kb-starting/` is removed whole if present, `kb.init` starts a store there, the operator's import (`operating.Operator(<staged root>).import_`) lands the seed into it, then `<root>/.kb-starting/kb` is renamed to `<root>/kb` and `.kb-starting/` removed. A store is "inside the directory" only once the rename has happened. kb.init on the staged root is not refused because of the root: decision/init-refuses-inside-or-above refuses only a store directly inside the named directory or above it, and the root holds none. Nothing the store keeps names its own path (confirm in Task 1 that the marker and the database hold no absolute path, so the rename moves a working store; if one does, stop and hand back).
5. **Stopped, however**: a run killed with SIGKILL at any moment before the rename leaves at most a `.kb-starting/` directory, never `<root>/kb`; the next `kb init --seed` removes it first. SIGINT and SIGTERM during a seeded init exit non-zero with the staging removed when Python gets to run its `finally`, and leave it otherwise; either way there is no store. Rests on "If kb init with a seed directory is stopped before it finishes, however it was stopped, ...".
6. **kb serve --start's order**: no address → today's refusal (no role needed). The address read (`addresses.address`) → today's refusal when it is not a host and a port. Then the root: a store's marker there (any form, an earlier or later kb's included) → served exactly as `kb serve` serves it today, with today's refusals (`server.refused`, `served`), no role read. A connection and no store, or anything else `server.refused` refuses other than "no store" → that refusal, unchanged. No store → the role (`KB_ACTOR`, refused as decision 7 words it), then the store started in staging and renamed into place (decision 4 without a seed), then `server.started`; if serving then fails (a bind `ValueError`, `Refused` from the lock), the store this run placed is taken back (renamed out and removed) before exiting 2 with today's refusal. Rests on the six kb serve with `--start` lines and the line list "refused as kb serve without it is".
7. **The role refusal's words** for kb serve --start: `kb serve: refused: actor: a store can only be started under a role, named through KB_ACTOR`, rule `actor` (`rules.ACTOR`), the reason the line names. kb init keeps its own wording. Rests on "it is refused because a store can only be started under a role named through `KB_ACTOR`".
8. **Inside a store, with --start**: the root has no store of its own, so decision 6 reaches the start, and `store.vacant` refuses it with rule `root` ("stores do not nest; ... is inside the store at ..."), the reason the line names; nothing is served, and the store above holds what it held. Rests on "If the operator runs kb serve with `--start` on a directory that sits inside a store, it is refused because that directory is inside a store".
9. **"The same reason kb serve without --start is rejected"** (slice 143's outline) means byte-identical stderr and the same exit code from the two runs at the same address on the same directory state; the step runs plain `kb serve` first (it changes nothing when refused) and `kb serve --start` second, and compares.
10. **The image's healthcheck and user**: `HEALTHCHECK --interval=5s --timeout=3s --start-period=10s --retries=3` running the venv's Python with a two-second `socket.create_connection(("127.0.0.1", 50051))`; the user `kb` with uid and gid 1000, owning `/data`. The base image is `python:3.12-slim` pinned to an exact patch tag current on the day it is written (record it in the plan log). Rests on the image's Implementation lines.
11. **What the image check uses in place of host bind mounts.** This development environment is itself a container whose Docker daemon may not see its paths (slice 145's unknown). The check builds from the checkout (`docker build`, whose context the client sends) and gets the seed into a named volume by a means that needs no host path (for example `docker compose cp` into a helper service, or a small image built with the seed in it); it never relies on `-v ./seed:/seed`. The README keeps the bind-mount form for operators on an ordinary host.

## Questions for the spec

None open. Two edge cases no line decides go to Review Focus as tests that pin "no store is left behind" without choosing a new behaviour (1 and 2 below); if either needs a choice, it is logged as `QUESTION FOR THE SPEC:` and the task stops.

## Review Focus

1. **A seed directory that is the root, or holds it.** `kb init <root> --seed <root>` (an operator mounting one directory twice) must not import the staged store's own files or loop; whatever it answers, the root afterwards holds no `kb/` and no `.kb-starting/`. Owner: Task 1. Test intent: run it on a root holding a clean seed's files; assert exit is 0 or 2, and if 2, nothing under the root but the seed's own files; if 0, the store holds exactly the seed's artifacts. If it lands the staging files as errors, log `QUESTION FOR THE SPEC:` and keep the assertion on "no half store".
2. **A run killed after it was staged, then a plain start.** After a killed `kb init --seed`, plain `kb init <root>` and `kb serve <root> --start` both start a store as if nothing were there (decision/init-refuses-inside-or-above: a store deeper below does not refuse), and `kb init --seed` clears the leftover. Owner: Task 2. Test intent: a plain test that leaves a staged directory by killing the process (or by calling `staging.py`'s public start with the import made to raise), then runs each command and asserts a working store and, for the seed, no leftover.
3. **Ctrl-C during `docker compose run ... kb init --seed`.** SIGINT mid-import exits non-zero with no Python traceback on stderr beyond kb's refusal line, and no store. Owner: Task 2. Test intent: SIGINT the installed `kb` during a large seed's import; assert exit non-zero, stderr has no `Traceback`, no `<root>/kb`.
4. **`kb serve --start` on a root that does not exist** (an operator's typo, or `/data` missing) is refused with `kb.init`'s own fault (rule `root`, "a store is started in a directory that exists"), nothing served, nothing made. Owner: Task 4. Test intent: in process, exit 2, the rule, the path still absent.
5. **The image on a bind mount its user cannot write.** The container exits 2 with kb's `unreadable` fault naming the database, never a Python traceback, as the README says. Owner: Task 8. Test intent: a case in the image check running the default command against a volume made root-owned (chown by a root-run helper), asserting exit 2 and `unreadable` on stderr.

---

### Task 1: Slice 138 — a store set up seeded from a directory of files

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts

- [ ] **Scenarios** (`@slice-138`, 1 scenario, 1 collected): operate-a-store / The operator sets up a store seeded from a directory of files.

- [ ] **Why it is red today** (suite record at 4e2aa58): `StepDefinitionNotFoundError` for "a seed directory that checks clean, holding a type for decisions and a decision"; and behind the steps, `kb init` has no `--seed` (`cli.main`'s `init` parser takes only `root`), and nothing starts a store anywhere but in place.

- [ ] **Where the change lands.** New module `staging.py` (decision 4): a store started under a role out of sight beneath the root, a seed imported into it through `operating.Operator`, put in place by one rename, the staging removed on every refusal (Rule 1's constraint above on how). `cli.py`: `init` takes `--seed <dir>`; `_init` dispatches to `staging.py` when a seed is given and prints a refused import's report through `_reported` (decision 2). CLAUDE.md: a `staging.py` row (owns: a store started, and seeded, out of sight under its root, put in place whole by one rename, and taken back whole; never holds: finding a store, checks, rpcs); `cli.py`'s row names `kb init --seed`. Confirm decision 4's last sentence before the rename is relied on.

- [ ] **Steps to reuse.** `a directory that has no store inside it` (tests/test_look_after_a_store.py, target `root`); `_kb` (tests/conftest.py) for the command with `KB_ACTOR` in `env`; the seed's files written as an export writes them: `_for_import`, `_put`, `_artifact` and `_file` in tests/test_export_and_import_a_store.py (move what both modules need into tests/calls.py or tests/held.py rather than importing across test modules), with `DECISION_TYPE` from tests/calls.py. "As kb import lands them" (decision 3): start a second store under the same role with `_kb("init", ...)`, run `_kb("import", seed, ...)` in it, and compare the two stores' artifacts (`held.names`, `held.text`) and their histories' roles, messages and sets (`held.history`), not moments or ids.

- [ ] **Decisions applied.** 2, 3, 4.

- [ ] **Verify.** `.venv/bin/python -m pytest -q -m slice-138` → 1 passed. Review Focus 1's test lands in this task.

- [ ] **Checkpoint.** `plan status 138 green`, and `plan log "Slice 138: ..."` naming the module made and the result of decision 4's check on stored paths.

### Task 2: Slice 139 — a seeded setup stopped partway leaves no store

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts

- [ ] **Scenarios** (`@slice-139`, 1 scenario, 1 collected): operate-a-store / A seeded setup that was stopped before it finished leaves no store, and the same setup run again lands the seed.

- [ ] **Why it is red today**: `StepDefinitionNotFoundError` for "the operator's kb init with that seed directory against the directory, saying which role they are, is stopped before it finishes"; behind it, slice 138's staging must already leave no `<root>/kb` when killed, and must clear what a killed run left.

- [ ] **Where the change lands.** Test code, mostly: the step that stops a real run. `staging.py` only if the run again does not already clear the leftover (decision 4's "removed whole if present").

- [ ] **The unknown, and the approach this plan takes.** The step must stop the installed `kb` partway without a hook in kb and without naming the staging directory. Run the installed command as `tests/serving.py` runs `kb serve` (`serving.KB`, `subprocess.Popen` with `KB_ACTOR` set, `cwd` the root), with a seed large enough that its import takes well over a second (a few thousand small artifacts of one type; time it once and log the size chosen), and SIGKILL it as soon as the root holds anything new while it still holds no `kb/` (poll `root.iterdir()` at millisecond intervals; this watches the root the operator named, not the staging place). If the import proves too fast to catch reliably at any seed size the suite can afford, stop and hand back with the timings: do not add a hook to kb.

- [ ] **Steps to reuse.** Task 1's seed builder and its "holds the files in the seed directory as kb import lands them" Then; `a directory that has no store inside it`. "That directory has no store inside it" here asserts no `<root>/kb` (a staging leftover may remain until the next run), unlike the existing `that directory still has no store inside it`, which asserts the root is empty. "The operator runs the same kb init again" is `_kb` in process with the same arguments.

- [ ] **Decisions applied.** 4, 5.

- [ ] **Verify.** `.venv/bin/python -m pytest -q -m slice-139` → 1 passed, run three times in a row with no failure. Review Focus 2 and 3 tests land in this task.

- [ ] **Checkpoint.** `plan status 139 green`; `plan log` the seed size, the import's time, and how the kill was timed.

### Task 3: Slice 140 — a seeded setup refused leaves no store

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts

- [ ] **Scenarios** (`@slice-140`, 5 scenarios, 5 collected): operate-a-store / Setting up a store from a seed directory whose files do not check clean is refused; / Setting up a seeded store where the directory already has one inside it is refused; / Setting up a seeded store without naming which role is refused; / Setting up a seeded store inside a store is refused; / Setting up a store seeded from something that is not a directory is refused.

- [ ] **Why each is red today**: `StepDefinitionNotFoundError` for the seed Givens ("a seed directory holding one file whose content does not fit its type", "a seed directory that checks clean", "a file where the seed directory should be") and the When "the operator runs kb init with that seed directory against the directory" (with and without a role, and "with that file as the seed directory"); the refusals themselves may already be right once Task 1's order is in place (decision 1): run the slice first and record which are red for a reason other than missing steps.

- [ ] **Where the change lands.** Test code; `staging.py` and `cli.py` only where decision 1's order is not yet what Task 1 built.

- [ ] **Steps to reuse.** `setting the store up is rejected because the role must be named through KB_ACTOR`, `... because that directory already has a store inside it`, `... because that directory is inside a store`, `that directory still has no store inside it`, `the store that is there holds what it held before` / `the store it sits inside holds what it held before` (tests/conftest.py's `_store_holds_what_it_held`, with `before`), `a directory that already has a store inside it, with content in that store` and `a directory that sits inside a store` (tests/conftest.py). "The operator is shown the check's report": the stdout lines `kb import --check` gives for the same directory (`_kb("import", "--check", ...)` in a fresh store), compared line for line. "Files for import are read from a directory": the rule and message `kb import` gives a file named as its directory (tests/test_export_and_import_a_store.py's existing refusal step for that case, by name, if one exists; otherwise the rule `refusals.not_an_import_directory` carries).

- [ ] **Decisions applied.** 1, 2.

- [ ] **Verify.** `.venv/bin/python -m pytest -q -m slice-140` → 5 passed.

- [ ] **Checkpoint.** `plan status 140 green`; `plan log` which scenarios were red only for steps.

### Task 4: Slice 141 — a store started and served in one command

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts

- [ ] **Scenarios** (`@slice-141`, 2 scenarios, 2 collected): operate-a-store / The operator serves a directory holding no store, asking for it to be started first; / Serving with --start a directory that already holds a store serves that store as it stands.

- [ ] **Why each is red today**: `StepDefinitionNotFoundError` for "the operator runs kb serve with --start on that directory, giving an address[, saying which role they are]"; behind it, `serve` has no `--start`, and `cli._serve` calls `server.refused(root)` first, which refuses a root holding no store with rule `store`.

- [ ] **Where the change lands.** `cli.py`: `serve` takes `--start`; `_serve` keeps today's path when the flag is absent and dispatches to `staging.py` for the start (decision 6). `staging.py`: a start with no seed, staged and placed as decision 4, and the take-back of a store this run placed (used by Task 5; build it here only if Task 4's scenarios need it). `server.py` is not changed. CLAUDE.md: `cli.py`'s row names `kb serve --start`; `staging.py`'s row names the start for serving.

- [ ] **Steps to reuse.** `a directory holding no store` (add beside `a directory that has no store inside it` if not present under that wording); `a directory holding a store with content in it, and nothing names which role the operator is` (compose from tests/conftest.py's `_store_with_content` and the existing "nothing names" Given); `tests/serving.py`'s `Serving` and `started`, which run the installed `kb serve` as a program: extend them to pass extra arguments (`--start`) and an environment with `KB_ACTOR`, rather than writing a second launcher. `that store is served at that address`: the served address answers a `History` read through `kb_pb2_grpc.KbStub` equal to an in-process one (as `_answered_from_that_store` does), after the server has said its line. `it holds what it held before`: `before` and `_store_holds_what_it_held`.

- [ ] **Decisions applied.** 4, 6.

- [ ] **Verify.** `.venv/bin/python -m pytest -q -m slice-141` → 2 passed. Review Focus 4's test lands in this task.

- [ ] **Checkpoint.** `plan status 141 green`; `plan log` where the start sits in `kb serve`'s order.

### Task 5: Slice 142 — a start refused while serving leaves no store

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts

- [ ] **Scenarios** (`@slice-142`, 2 scenarios, 4 collected): operate-a-store / Serving with --start a directory holding no store without naming which role is refused; / Serving with --start a directory holding no store at an address it cannot be served at is refused (3 examples).

- [ ] **Why each is red today**: `StepDefinitionNotFoundError` for the new When and for "serving is rejected because a store can only be started under a role named through KB_ACTOR"; "an address another server already holds" fails only at bind, after Task 4 has started a store, so without the take-back the directory is left holding one.

- [ ] **Where the change lands.** `staging.py`: the take-back (decision 6), only of the store this run placed; `cli.py`: the role refusal's words (decision 7). Two of the three address examples ("names no port", "beyond the last") are refused when the address is read, before anything is started (decision 6), so they need no take-back; the third does.

- [ ] **Steps to reuse.** `UNSERVABLE` and `_held_by_another_server` in tests/test_look_after_a_store.py (the three address rows are the same); `serving the store is rejected because the store cannot be served at that address, and the address is named back` (the new Then reads "serving is rejected because ..."; bind the new text to the same assertion); `nothing is served` (`served.owned(root).close()` needs a `kb/` to open its lock in: for a directory holding no store, "nothing is served" means nothing listens at the address and there is no `kb/`); `that directory still holds no store` asserts no `<root>/kb` and no staging leftover (the root as it was: `held.apart_from_the_store` before and after).

- [ ] **Decisions applied.** 6, 7.

- [ ] **Verify.** `.venv/bin/python -m pytest -q -m slice-142` → 4 passed.

- [ ] **Checkpoint.** `plan status 142 green`; `plan log` how the take-back is guarded to a store this run placed.

### Task 6: Slice 143 — kb serve --start refused where kb serve is

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts

- [ ] **Scenarios** (`@slice-143`, 2 scenarios, 6 collected): operate-a-store / Serving with --start a directory that sits inside a store is refused; / Serving with --start is refused wherever serving without it is refused (5 examples: a store at an address with no port; a store another server owns; an earlier kb's store; a later kb's store; a connection and no store).

- [ ] **Why each is red today**: `StepDefinitionNotFoundError` for the outline's Givens and its Then; after Tasks 4 and 5 the behaviour should already follow decision 6, so record which examples are red for another reason.

- [ ] **Where the change lands.** Test code; `cli.py`/`staging.py` only where an example shows decision 6's order is not what was built.

- [ ] **Steps to reuse.** `a directory that sits inside a store` and `the store it sits inside holds what it held before` (tests/conftest.py); `held.made_by_an_earlier_kb`, `held.made_by_a_later_kb`; a store another server owns: `serving.hosted(root, request, clock=None)` (as `_held_by_another_server` uses it); a connection: `serving.connection(root, address)`; `_kb` for both runs (decision 9). `nothing is served` as Task 5 defines it for the inside-a-store scenario.

- [ ] **Decisions applied.** 6, 8, 9.

- [ ] **Verify.** `.venv/bin/python -m pytest -q -m slice-143` → 6 passed.

- [ ] **Checkpoint.** `plan status 143 green`.

### Task 7: Slice 144 — kb serve on an unreadable database is refused

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts

- [ ] **Scenarios** (`@slice-144`, 1 scenario outline, 2 collected): answer-a-damaged-file / The operator runs kb serve on a store whose database cannot be read (2 examples).

- [ ] **Why it is red today**: no module binds it (`tests/test_every_scenario_is_bound.py` fails on it); tests/test_answer_a_damaged_file.py binds its scenarios one by one with `@scenario`. The behaviour exists: `tests/test_serving_what_cannot_be_served.py`'s "a damaged database" case already asserts exit 2, rule `unreadable`, nothing listening. Expect it green on binding; if not, record why.

- [ ] **Where the change lands.** tests/test_answer_a_damaged_file.py only: a `@scenario` binding and steps. No production change is expected.

- [ ] **Steps to reuse.** `DAMAGES` and `the store's database <damage>` already in tests/test_answer_a_damaged_file.py; `a directory holding a store` and `nothing is served` live in tests/test_look_after_a_store.py: move both into tests/conftest.py (unchanged) so both modules use them. "Giving an address": `127.0.0.1:` at a port the system gave and let go (`_free_port` in tests/test_serving_what_cannot_be_served.py: move it to tests/serving.py beside `closed_port`, or use `serving.closed_port`). "The database is named": the refusal's message names the store's database path.

- [ ] **Decisions applied.** none.

- [ ] **Verify.** `.venv/bin/python -m pytest -q -m slice-144` → 2 passed; `tests/test_every_scenario_is_bound.py` passes.

- [ ] **Checkpoint.** `plan status 144 green`.

### Task 8: Slice 145 — kb's image serves a store beside its callers

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts

- [ ] **Check**: `make image-check` exits 0, having checked in a throwaway compose project: `kb init --seed` lands a small seed, and a refused seed leaves the volume holding no store; `up` becomes healthy; a second container reaches `kb:50051` through a connection given by a compose config, reads and makes a change; `docker compose run --rm kb validate` answers; a stop and a start keep the store; an empty volume with no `KB_ACTOR` exits 2 with the role's line. Red today: there is no `Dockerfile`, no `image` or `image-check` target in the Makefile, and no script.

- [ ] **Where the change lands** (outside `src/kb/`; the module map is unchanged): a root `Dockerfile` and `.dockerignore` (the binding values above, decision 10); `docker/compose.example.yaml`, the compose file of the design note's section 1, building from `https://github.com/dstengle/shopsystem-kb.git#v0.7.0`; the check script under `docker/` (a Python script run with the checkout's venv, or a shell script; it writes its compose project under a temporary directory with a project name of its own, building from the checkout rather than the tag, and runs `docker compose down -v` at the end however it ended); `Makefile` targets `image` (build, tagged `shopsystem-kb:dev`) and `image-check` (run the script), with a comment like `bench`'s saying they are not part of `test`; CLAUDE.md's Working here names `make image` and `make image-check`. The caller container in the check is the same image with its entry point overridden to a short Python program that uses `kb.client.connect()` under `KB_ROOT=/kb-connection` to read and to create through the server (it needs a type: define one first through the same client).

- [ ] **Release.** `pyproject.toml` version 0.7.0. README: "The contract: v1 (kb 0.7.0)", one sentence saying 0.7.0 adds `kb init --seed`, `kb serve --start` and the image; a section "Running kb in Docker" holding the compose example, the seed step (`docker compose run --rm -v ./seed:/seed:ro kb init /data --seed /seed`), the operator's commands (`docker compose run --rm kb validate`, `docker compose exec kb kb validate`), the empty-store trap and `docker compose down -v`, the bind mount's ownership and `--user`, and that a command serving at another port needs its own healthcheck. The `<root>/.kb-starting/` place is not mentioned.

- [ ] **The unknown.** Whether the daemon sees this environment's paths (decision 11). Probe it first (`docker run --rm -v "$PWD":/x alpine ls /x` from the checkout) and log the result; build the check so it passes either way.

- [ ] **Decisions applied.** 10, 11.

- [ ] **Verify.** `make image-check` → exit 0, each check named on its own line as it passes; `docker compose ls` and `docker volume ls` show nothing of the check's project afterwards. Review Focus 5's case lands in the check.

- [ ] **Checkpoint.** `plan status 145 green`; `plan log "Probe: ..."` for the bind-mount probe, the base image's exact tag, and the check's run time.
