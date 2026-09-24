# kb Batch 3 Implementation Plan: slices 8.1, 9, 10, 11, 12 and 13

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Each task is one slice of `docs/superpowers/plans/2026-09-24-kb-slices.md`. Inside a task, follow `shopsystem-bdd:bdd-red-green` scenario by scenario. Its stop conditions, hand-back, and checkpoint apply, and they override any step here that conflicts with them.

**Goal:** The next six slices, starting with the fix for a data-loss defect in kb 0.1:
- A second artifact whose title is already used gets a numbered name of its own, so it no longer overwrites the first.
- Every change can be read back from the journal.
- A client can search the prose, ranked.
- A client can follow the links two steps out and see the route to each artifact reached.
- A whole read follows links and stops at a loop.
- A write can be aimed at one section inside an artifact.

**Architecture:** kb is the Python package `kb` in `/home/vscode/shopsystem-kb`. A protobuf contract (`kb.contract`) sits in front of `KbServicer`, which works over a `Store`. The store is one canonical YAML file per artifact under `<root>/kb/`, and that directory is itself a git repository. `kb.values` holds the boundary conversions. `kb.validation` checks content against a type. `KbServicer._land` is the one write path: it applies operations to a `store.Draft`, checks them there, and writes only when all of them pass. This plan:
- names a create by the first name neither the store nor the set's draft holds (slice 8.1);
- adds three rpcs, each a contract message pair and an `InProcessClient` method: `Journal` (slice 9), `Search` (slice 10, in a new module `kb.search`) and `Refs` (slice 11);
- gives `Read` a whole level with a resolve depth (slice 12);
- lets a `Write` locator name a node inside the artifact. The node is put in place and the whole artifact is re-checked (slice 13).

**Provenance:** Every code block here was assembled in a scratch clone of this repository (`/tmp/batch3/kb`, cloned at `870dd3e`) on 2026-09-24. It was run with this checkout's `.venv` and `PYTHONPATH=/tmp/batch3/kb/src`, and the tasks were applied in order. The red and green results, the suite counts, and the Review Focus reproductions below are what those runs gave. The plan was then replayed from its own code blocks on a fresh clone (`/tmp/batch3-replay`): every red and green matched, and the result's `src/` and `tests/` were identical to the scratch run's. This repository was not touched except to write this plan.

**Tech Stack:** Python 3.11, setuptools (src layout), protobuf + grpcio + grpcio-tools (generated code is committed; `make contract` regenerates it), python-jsonschema 4.26 with `referencing`, ruamel.yaml 0.19 (YAML 1.2), git via subprocess, pytest 9 + pytest-bdd 8.

**Spec:** `docs/superpowers/specs/2026-09-23-kb-design.md`, in particular "Identity keys" (`id`), "Serialization" (journal entry), "The contract" (the `Read`, `Write`, `Refs`, `Search` and `Journal` rows, and "Resolution"), and "Artifact model" (nodes and paths). The slice plan is `docs/superpowers/plans/2026-09-24-kb-slices.md`, slices 8.1, 9, 10, 11, 12 and 13, and the feature files are in `features/`. Each slice's scenarios carry `@slice-<n>`, so `.venv/bin/python -m pytest -q -m slice-9` runs one slice, and the quoted form `-m "slice-8.1"` works for a dotted number.

## Global Constraints

- Feature files are read-only for the implementer. Only `slicing-into-increments` edits a tag line, and only `formulating-features` edits a Given, When, or Then. Any other diff under `features/` is a stop condition.
- Code only what a scenario asserts (bdd-red-green). Where the scenarios are silent, the code is silent too, and the silence goes into the checkpoint entry as an open question. The decisions this plan makes are listed below, each tied to the spec line or scenario that asks for it.
- **Extend, never add beside.**
  - Content is converted by `values.content`, one function for Create, Write and Apply. A node write extends it with `at_root=False` and does not add a second parser.
  - Links are found by `validation.references` and `validation.links`, the functions the link rule uses. Refs and the whole read find them there too.
  - Stubs are made by `KbServicer._stub`. Search and Refs use it.
  - The not-found fault is made in one place, `_not_found`, which Read and Refs share.
  - Every write goes through `_land`. A node write is a `Replacement` like any other.
- Spec, identity: "`<type>/<slug>`, minted by kb from the title on create and never supplied by the client. On collision kb appends `-2`, `-3`, and so on. Stable for the artifact's life".
- Spec, journal entry: "`id`, `at`, `actor: { role, execution }`, `op`, `artifact`, `path`, `revision`, `schema_version`, `digest` (sha256 of the canonical bytes after the write), `message`, and `batch`".
- Spec, contract: "`Refs` | locator, direction, optional via-field, optional type, depth | stubs with the path taken"; "`Search` | text, optional type, scope (`sections`, `fields`, `all`) | stubs with matching section title and snippet, ranked"; "`Journal` | filters: artifact, actor, execution, batch, since | entries". This batch builds only the parts its scenarios reach. The other filters and options arrive with slices 31, 33 and 35.
- Spec, resolution: "Depth 1 inlines each direct reference target in place of its id; depth n follows references n hops. A target already inlined on the current resolution path is returned as a reference, not inlined again, so a cycle terminates."
- Spec, nodes: "Every node is addressable by a path from the artifact root, such as `steps/draft/branches/0` or `sections/purpose/sections/rationale`."
- Errors are a typed list of `{ artifact, path, rule, message }`. A response that carries faults is a refusal, and nothing was written.
- kb is exercised through its in-process transport. The one thing a step replaces is `kb.journal.now`, the clock (Decision 2).
- Each checkout has its own virtualenv. `make test` runs the suite (`.venv/bin/python -m pytest -q`). `make contract` regenerates `kb_pb2.py`, `kb_pb2.pyi` and `kb_pb2_grpc.py` from `kb.proto`, and the four files are committed together.
- Work on `main` in `/home/vscode/shopsystem-kb`. A worktree needs its own `.venv` first (`make dev`).
- shop-knowledge pins kb at `v0.1.0`. Nothing here touches or runs its suite. Tagging a release with slice 8.1 and bumping the pin are not part of this plan (see "After slice 13").
- Commits: `git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit`, the message ending with the Co-Authored-By line of the model that made the commit, e.g. `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- The suite prints pytest-bdd `PytestRemovedIn10Warning`s. That is the baseline, not a fault.
- Baseline before Task 1: `make test` → `67 failed, 51 passed`. Each task adds exactly one passing scenario.

## Decisions this plan makes (the spec left them open or silent)

1. **The clash rule.** `_unclaimed(draft, named) -> ArtifactId` in `servicer.py` returns the name the title gives if nothing holds it. Otherwise it tries `-2`, `-3` and so on until it finds a name nothing holds. It asks the `Draft`, which answers for the store and for everything earlier operations in the same set have put there. So two creates with one title in one set get `monthly` and `monthly-2`; this was checked in scratch. This settles slice 8.1's unknown. A create refused for its content names the numbered name in its faults, since that is the artifact it would have been. Pinned by slice 8.1.
2. **Setting the clock.** kb stamps journal entries from `kb.journal.now()`, which exists "so a later slice can set it from outside". The step `today is <day>` monkeypatches it with a clock that moves on one second at every stamp. It does not freeze, because an entry's id is its timestamp plus its place in its set. Two entries with the same stamp would share a file name, and the second would overwrite the first. A step sets the clock back to make a change on an earlier day. kb gains no clock setting of its own. This settles slice 9's unknown.
3. **Journal.**
   - `rpc Journal(JournalRequest) returns (JournalResponse)`.
   - `JournalRequest { artifact }` only. The name is checked by `values.artifact_id`, and a bad one is refused with that fault. Role, execution, batch and since arrive with slice 35.
   - `Entry` carries every key of the stored entry. `actor` is an `Actor`, and `at` is the stored ISO 8601 text.
   - Entries come oldest first. They are sorted by the stamp in their id and then by their place in the set as a number, because as text `-10` would sort before `-2`.
   - `journal.entries(store_dir)` reads them.
4. **Search.**
   - `rpc Search(SearchRequest) returns (SearchResponse)`. `SearchRequest { text }`. Kind and scope arrive with slice 33.
   - A `Match` is `{ stub, section, snippet }`, with a `Stub` of the artifact whose `field` is empty.
   - The words are the `\w+` runs of the text. A section matches on whole words, in any case, in its body only; titles and fields are slice 33's scope. The sections searched are those at every depth of every artifact.
   - A section's score is how many matches its body holds. Results come highest first. Ties keep the order the store holds artifacts in (path order), then the artifact's order of sections.
   - The snippet is up to 60 characters either side of the first match, with whitespace collapsed and `…` where it was cut.
   - The ranking is computed on each call, with no index. The spec's search index and cache are "measured, not specified". This settles slice 10's unknown.
5. **Refs.**
   - `rpc Refs(RefsRequest) returns (RefsResponse)`. `RefsRequest { locator, depth }`. Direction, via-field and type arrive with slice 31.
   - A `Hop` is `{ field, id }`, and `Reached` is `{ stub, route }`, where the route is the hops from the artifact asked about. The stub's `field` is the last hop's.
   - Refs goes breadth first, depth steps out. Each artifact is reached once, by its shortest route. The artifact asked about is never reached.
   - The locator is checked, and a name the store lacks is refused with `_not_found`, as Read refuses it. This settles slice 11's unknown.
6. **Whole reads.**
   - `ReadRequest` gains `enum Level { SUMMARY = 0; WHOLE = 1; }`, `level = 2` and `depth = 3`. SUMMARY is the default, so every existing read is unchanged. The section level arrives with slice 21.
   - A whole read answers the typed identity fields, with `content` holding everything but the identity keys.
   - A link filled in is the whole stored artifact, identity keys included, and itself resolved one step less.
   - The set of names on the current path starts with the artifact being read, so a link back to anything on the path stays a name. This settles slice 12's unknown.
7. **Node writes.**
   - A `Write` whose locator has a place replaces the node there and checks the whole artifact.
   - A place is pairs of a list and an item in it, and may end in a field. A section is named by the name its title gives (`sections/rationale`), and a part by its `id`.
   - Node content is read by `values.content(..., at_root=False)`, which skips the identity check. A section's own `title` is not the artifact's, and the scratch run showed the check refusing it.
   - A place that names nothing is refused with rule `not-found`: `'<id>' holds nothing at '<place>'`. Otherwise the lookup would fail as a bare `StopIteration`. No scenario pins this refusal, so Task 6 logs it as a question.
   - The journal entry of a node write still says path `""` (Review Focus 4).

## Review Focus

In this project, tests are scenarios, and the feature files are the human gate, so no unit tests are added. Instead, each line below goes into the owning task's checkpoint entry as a `QUESTION FOR THE SPEC`, with the reproduction given here. Each was reproduced in scratch after all six tasks.

1. **A write aimed at a part raises.** Reproduction: `write(client, DECISION, {"title": "Go monthly", "body": "y"}, path="options/go-monthly")` raises `KeyError: 'id'` through the client, because the new item carries no id. This is batch 2's first finding reached a new way. Task 6 logs it.
2. **A file that cannot be read breaks Search and Journal.** Reproduction: write `title: [` into a stored artifact's file, and `search(client, "restocking")` raises `store.Unreadable`. Write `id: [` into a file under `kb/journal/`, and `journal(client)` raises `canonical.NotCanonical`. Read answers the first case with a fault, and Validate reports it. Tasks 2 and 3 log them.
3. **Refs with no depth reaches nothing.** Reproduction: `refs(client, DECISION, 0)` answers no `reached`. Slice 31's scenarios follow links "out of" and "into" an artifact and name no depth. Task 4 logs it for slice 31.
4. **A node write's journal entry says path "".** Reproduction: the entry for the write of `sections/rationale` has `path: ""`. The spec's entry carries the place written. Task 6 logs it.
5. **Refs ignores a place in its locator.** Reproduction: `Refs` with `locator {id: DECISION, path: "sections/rationale"}` answers the decision's own links. Task 4 logs it.

---

### Task 1: Slice 8.1, a second artifact with a title already used gets a name of its own

**Slice plan entry:** Slice 8.1, capability. Unknown: when the name a title gives is taken, how does a create find the first name free, counting what earlier operations in the same set have put in the draft before any of it lands? Scenario:

1. kb / create-an-artifact / A second artifact with a title already used gets a name of its own

**Files:**
- Modify: `src/kb/servicer.py` (`_create` names through `_unclaimed`; new module function `_unclaimed`)
- Modify: `tests/test_create_an_artifact.py` (three steps appended)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `tests/calls.py`: `request(client, type_name, title, content, message=…)`, `read(client, artifact_id)`. The fixtures `root` and `client` (the Background's store holding the decision type). `values.named(kind, title) -> ArtifactId`, `Draft.holds(ArtifactId) -> bool`.
- Produces: `servicer._unclaimed(draft: Draft, named: ArtifactId) -> ArtifactId`.

- [ ] **Step 1: Run it red**

```bash
cd /home/vscode/shopsystem-kb && .venv/bin/python -m pytest -q -m "slice-8.1" 2>&1 | grep -E "^E |passed|failed" | tail -2
```

Expected: `1 failed`, a `StepDefinitionNotFoundError` for `Given "a decision the store already holds, titled "Price reviews happen weekly""`.

- [ ] **Step 2: The steps**

Append to `tests/test_create_an_artifact.py` (its imports already hold `given`, `parsers`, `then`, `when`, `read` and `request`):

```python


@given(parsers.parse('a decision the store already holds, titled "{title}"'), target_fixture="first")
def _a_decision_already_held(root, client, title):
    created = request(client, "decision", title, {"sections": SECTIONS}, message="Record it")
    assert not created.faults, created.faults
    return {"id": created.id, "title": title, "bytes": (root / "kb" / f"{created.id}.yaml").read_bytes()}


@when("the client creates another decision with that same title, saying which role and why", target_fixture="created")
def _create_another_with_that_title(client, first):
    return request(client, "decision", first["title"], {"sections": [
        {"title": "Purpose", "body": "Keep the shelf prices honest.\n"},
        {"title": "Rationale", "body": "Suppliers change their lists every week.\n"},
    ]}, message="Record it again")


@then("the client is given a name of its own for the new decision, the name already taken with a number added")
def _a_numbered_name(client, first, created):
    assert not created.faults, created.faults
    assert (created.id, created.revision) == (f"{first['id']}-2", 1)
    assert read(client, created.id).title == first["title"]


@then("the decision created first keeps the name it had")
def _the_first_keeps_its_name(root, client, first):
    kept = read(client, first["id"])
    assert (kept.id, kept.revision) == (first["id"], 1)
    assert (root / "kb" / f"{first['id']}.yaml").read_bytes() == first["bytes"]
```

Run Step 1's command again with `tail -3` in place of `tail -2`. Expected: `1 failed`, with `At index 0 diff: 'decision/price-reviews-happen-weekly' != 'decision/price-reviews-happen-weekly-2'`. That is kb 0.1's overwrite.

- [ ] **Step 3: The code**

In `src/kb/servicer.py`, in `_create`, change

```python
        try:
            artifact_id = values.named(kind, creation.title)
        except values.Refused as refused:
            faults += refused.faults
```

to

```python
        try:
            artifact_id = _unclaimed(draft, values.named(kind, creation.title))
            at = str(artifact_id)
        except values.Refused as refused:
            faults += refused.faults
```

and, just above `def _summary_fields(artifact, schema):`, add:

```python
def _unclaimed(draft: Draft, named: ArtifactId) -> ArtifactId:
    """The name a title gives, or, when the store or an earlier change in the set already holds it, that name with
    -2, -3 and so on added: the first that nothing holds. What already holds a name keeps it."""
    candidate, number = named, 1
    while draft.holds(candidate):
        number += 1
        candidate = ArtifactId(named.kind, f"{named.slug}-{number}")
    return candidate


```

- [ ] **Step 4: Run it green, and the suite**

```bash
.venv/bin/python -m pytest -q -m "slice-8.1" 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `1 passed, 117 deselected`; `66 failed, 52 passed`.

- [ ] **Step 5: Commit**

```bash
git add src/kb/servicer.py tests/test_create_an_artifact.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 8.1: a second artifact with a title already used gets a name of its own

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 6: Checkpoint**

In `docs/superpowers/plans/2026-09-24-kb-slices.md`, set slice 8.1's Status to `green`. Append at the very end of the Log, and check with `tail` that it is last:

```
- <date> slice 8.1 green. Someone can now: create a decision with a title another already has and be given that name with -2 added, the first decision reading as it was.
  Assumption "the first free name is found through the draft, so it counts what earlier operations in the set put there": <held or not>. Evidence: <created.id and the first file's bytes unchanged, from the scenario; and the ids an Apply of two creates titled "Monthly" answers, expected decision/monthly and decision/monthly-2>.
  Surprised by: <nothing, or what>.
  Open questions:
  - Still open (slice 5's question): a later operation in a set that names what an earlier one creates, by the name its title gives, lands on the older artifact holding that name when the title was already used.
  Next: slice 9.
```

Commit the plan: `Slice 8.1 green`.

---

### Task 2: Slice 9, every change leaves an entry

**Slice plan entry:** Slice 9, capability. Unknown: how do step definitions set the time kb stamps on an entry, so that two changes can be two days apart within one run? Needs: a journal entry for every operation, naming its set, which `_land` has written since slice 5; control of the clock from outside kb. Scenario:

1. kb / read-the-journal / Every change leaves an entry

**Files:**
- Modify: `src/kb/contract/kb.proto` (the `Journal` rpc; `JournalRequest`, `Entry`, `JournalResponse`), then `make contract`
- Modify: `src/kb/journal.py` (`entries`, `_order`)
- Modify: `src/kb/servicer.py` (`Journal`, module function `_entry`)
- Modify: `src/kb/client.py` (`Journal`)
- Modify: `tests/calls.py` (`request`, `create` and `write` take an actor; new `journal`)
- Rewrite: `tests/test_read_the_journal.py`
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `calls.define`, `calls.DECISION_TYPE`, the `root` fixture, `kb.journal.now` (a module function that `journal.write` looks up at each call).
- Produces:
  - `journal.entries(store_dir: Path) -> list[dict]`, oldest first.
  - `kb_pb2.JournalRequest(artifact)`, `kb_pb2.Entry`, `kb_pb2.JournalResponse(entries, faults)`, and `InProcessClient.Journal`.
  - In `tests/calls.py`: `request(…, actor=CLIENT)`, `create(…, actor=CLIENT)`, `write(client, artifact_id, content, message=…, actor=CLIENT)` and `journal(client, artifact="")`. Task 6 adds `path=""` to `write`.

- [ ] **Step 1: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-9 2>&1 | grep -E "^E |passed|failed" | tail -2
```

Expected: `1 failed`, a `StepDefinitionNotFoundError` for `Given "today is 2026-09-23"`.

- [ ] **Step 2: The helpers and the steps**

In `tests/calls.py`, replace `request`:

```python
def request(client, type_name, title, content, message="Create an artifact", actor=CLIENT):
    """A Create as the client sends it: the title beside the content. Returns the response, faults and all."""
    return client.Create(kb_pb2.CreateRequest(
        type=type_name, title=title, content=dumps(content), actor=actor, message=message,
    ))
```

In `create`, change the signature line to `def create(client, type_name, content, message="Create an artifact", actor=CLIENT):` and its call line to `    response = request(client, type_name, title, content, message, actor)`. Replace `write`, and add `journal` after it:

```python
def write(client, artifact_id, content, message="Change an artifact", actor=CLIENT):
    """A Write of a whole artifact, under the client's role unless another actor is given. Returns the response,
    faults and all."""
    return client.Write(kb_pb2.WriteRequest(
        locator=kb_pb2.Locator(id=artifact_id), content=dumps(content), actor=actor, message=message,
    ))


def journal(client, artifact=""):
    """The journal's entries, those about one artifact when it is named."""
    return client.Journal(kb_pb2.JournalRequest(artifact=artifact))
```

Replace the whole of `tests/test_read_the_journal.py` with:

```python
import hashlib
from datetime import datetime, timedelta

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, create, define, journal, write
from kb import client as kb_client
from kb import journal as kb_journal
from kb.contract import kb_pb2

scenarios("read-the-journal.feature")

DECISION = "decision/price-reviews-happen-weekly"
SHOPKEEPER = kb_pb2.Actor(role="shopkeeper")
AGENT = kb_pb2.Actor(role="agent", execution="restock-run-12")


@given(parsers.parse("today is {day}"), target_fixture="clock")
def _today_is(monkeypatch, day):
    """kb stamps each entry from journal.now. Here it reads this clock, which moves on a second at every stamp so no
    two entries share one; a step sets the clock back to make a change on an earlier day."""
    clock = {"today": datetime.fromisoformat(f"{day}T09:00:00+00:00")}
    clock["at"] = clock["today"]

    def now():
        clock["at"] += timedelta(seconds=1)
        return clock["at"]

    monkeypatch.setattr(kb_journal, "now", now)
    return clock


@pytest.fixture
def written():
    """The bytes of the decision's file after each change, in order, for the fingerprints."""
    return []


@given(
    "a store where the shopkeeper created a decision on 2026-09-21 "
    "and an agent working on a named piece of work changed it today",
    target_fixture="client",
)
def _store_with_a_decision_changed_today(root, clock, written):
    clock["at"] = datetime.fromisoformat("2026-09-21T09:00:00+00:00")
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    create(client, "decision", {
        "title": "Price reviews happen weekly",
        "sections": [
            {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
            {"title": "Rationale", "body": "Costs move weekly.\n"},
        ],
    }, message="Review prices weekly", actor=SHOPKEEPER)
    written.append((root / "kb" / f"{DECISION}.yaml").read_bytes())
    clock["at"] = clock["today"]
    changed = write(client, DECISION, {"sections": [
        {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
        {"title": "Rationale", "body": "Costs move weekly, and the suppliers say so.\n"},
    ]}, message="Say why weekly", actor=AGENT)
    assert not changed.faults, changed.faults
    written.append((root / "kb" / f"{DECISION}.yaml").read_bytes())
    return client


@when("the client reads the journal for that decision", target_fixture="entries")
def _read_the_journal_for_the_decision(client):
    response = journal(client, DECISION)
    assert not response.faults, response.faults
    return list(response.entries)


@then("there is one entry for each change")
def _one_entry_for_each_change(entries):
    assert [(entry.op, entry.artifact) for entry in entries] == [("create", DECISION), ("write", DECISION)]


@then(
    "each entry says when it happened, which role made it, for which piece of work, what it did, to which artifact "
    "and place in it, the version it left behind, a fingerprint of what was written, the message given, "
    "and which set of changes it landed with"
)
def _each_entry_says_everything(entries, written):
    assert [
        (entry.at[:10], entry.actor.role, entry.actor.execution, entry.op, entry.artifact, entry.path,
         entry.revision, entry.schema_version, entry.message)
        for entry in entries
    ] == [
        ("2026-09-21", "shopkeeper", "", "create", DECISION, "", 1, 1, "Review prices weekly"),
        ("2026-09-23", "agent", "restock-run-12", "write", DECISION, "", 2, 1, "Say why weekly"),
    ]
    assert [entry.digest for entry in entries] == [hashlib.sha256(text).hexdigest() for text in written]
    assert [entry.batch for entry in entries] == [entry.id for entry in entries]
```

Run Step 1's command again. Expected: `1 failed`, `AttributeError: 'InProcessClient' object has no attribute 'Journal'`. The Givens pass, so the clock works and both changes land.

- [ ] **Step 3: The contract**

In `src/kb/contract/kb.proto`, add `  rpc Journal(JournalRequest) returns (JournalResponse);` as the last line of `service Kb`, after `rpc Apply`. Append at the end of the file:

```proto

// Narrows the journal to the entries about one artifact; empty, every entry.
message JournalRequest {
  string artifact = 1;
}

// One journal entry, as the store holds it. `at` is ISO 8601 in UTC; a
// change made alone names itself as its batch.
message Entry {
  string id = 1;
  string at = 2;
  Actor actor = 3;
  string op = 4;
  string artifact = 5;
  string path = 6;
  int32 revision = 7;
  int32 schema_version = 8;
  string digest = 9;
  string message = 10;
  string batch = 11;
}

// The entries, oldest first. With faults, a refusal: a name that is not a
// plain name, or no store found.
message JournalResponse {
  repeated Entry entries = 1;
  repeated Fault faults = 2;
}
```

Run `make contract`.

- [ ] **Step 4: The code**

Append to `src/kb/journal.py`:

```python


def entries(store_dir: Path) -> list[dict]:
    """Every entry in the journal, oldest first: by the time in its id, then by its place in its set."""
    found = [canonical.load(path.read_text()) for path in (store_dir / "journal").rglob("*.yaml")]
    return sorted(found, key=_order)


def _order(entry: dict) -> tuple[str, int]:
    stamp, _, seq = entry["id"].rpartition("-")
    return stamp, int(seq)
```

In `src/kb/client.py`, after `Apply`, add:

```python

    def Journal(self, request, timeout=None):
        return self._call("Journal", request, kb_pb2.JournalResponse)
```

In `src/kb/servicer.py`, just above `def _stub(self, field, target_id: ArtifactId):`, add:

```python
    def Journal(self, request, context):
        """The journal's entries, oldest first, those about one artifact when the request names it."""
        try:
            artifact = str(values.artifact_id(request.artifact)) if request.artifact else ""
        except values.Refused as refused:
            return kb_pb2.JournalResponse(faults=refused.faults)
        return kb_pb2.JournalResponse(entries=[
            _entry(entry) for entry in journal.entries(self._store.dir)
            if not artifact or entry["artifact"] == artifact
        ])

```

and, just above `def _unclaimed(`, add:

```python
def _entry(entry: dict) -> kb_pb2.Entry:
    return kb_pb2.Entry(
        id=entry["id"], at=entry["at"], actor=kb_pb2.Actor(**entry["actor"]), op=entry["op"],
        artifact=entry["artifact"], path=entry["path"], revision=entry["revision"],
        schema_version=entry["schema_version"], digest=entry["digest"], message=entry["message"], batch=entry["batch"],
    )


```

- [ ] **Step 5: Run it green, and the suite**

```bash
.venv/bin/python -m pytest -q -m slice-9 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `1 passed, 117 deselected`; `65 failed, 53 passed`.

- [ ] **Step 6: Commit**

```bash
git add src/kb/contract src/kb/journal.py src/kb/servicer.py src/kb/client.py tests/calls.py tests/test_read_the_journal.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 9: every change leaves an entry the client can read

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 7: Checkpoint**

Set slice 9's Status to `green`. Append at the very end of the Log:

```
- <date> slice 9 green. Someone can now: read the journal for one artifact and see each change with when, who, for which piece of work, what, where, the version, a fingerprint, the message and its set.
  Assumption "steps set kb's clock by replacing journal.now with one that moves on a second at every stamp": <held or not>. Evidence: <the two entries as (at, role, execution, op, revision, batch == id)>.
  Surprised by: <nothing, or what>.
  Open questions:
  - QUESTION FOR THE SPEC: a journal file that cannot be read makes Journal raise canonical.NotCanonical through the client. Should it be a fault, as an unreadable artifact is? (Review Focus 2)
  Next: slice 10.
```

Commit the plan: `Slice 9 green`.

---

### Task 3: Slice 10, search the prose, ranked

**Slice plan entry:** Slice 10, capability. Unknown: what index over sections gives ranking by how often the term occurs in a section, with the section title and a snippet in each result? Scenario:

1. kb / search-the-store / The client searches the prose

**Files:**
- Create: `src/kb/search.py`
- Modify: `src/kb/contract/kb.proto` (the `Search` rpc; `SearchRequest`, `Match`, `SearchResponse`), then `make contract`
- Modify: `src/kb/servicer.py` (import `search`; `Search`)
- Modify: `src/kb/client.py` (`Search`)
- Modify: `tests/calls.py` (new `search`)
- Rewrite: `tests/test_search_the_store.py`
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `Store.artifacts()`, `KbServicer._stub(field, target_id) -> kb_pb2.Stub`, `values.artifact_id`.
- Produces: `search.rank(artifacts, text: str) -> list[search.Hit]`, where `Hit` is a NamedTuple of `artifact: str`, `section: str`, `snippet: str` and `count: int`. Also `kb_pb2.SearchRequest(text)`, `kb_pb2.Match(stub, section, snippet)`, `kb_pb2.SearchResponse(matches, faults)`, `InProcessClient.Search`, and `calls.search(client, text)`. Slice 33 extends `SearchRequest` with kind and scope.

- [ ] **Step 1: The steps**

Append to `tests/calls.py`:

```python


def search(client, text):
    """A search of the prose for the text."""
    return client.Search(kb_pb2.SearchRequest(text=text))
```

Replace the whole of `tests/test_search_the_store.py` with:

```python
from pytest_bdd import given, parsers, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, create, define, search
from kb import client as kb_client
from kb.contract import kb_pb2

scenarios("search-the-store.feature")

PROCESS_TYPE = {
    "title": "Process",
    "version": 1,
    "schema": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]},
}


@given("a store where two decisions and a process mention restocking in their prose", target_fixture="client")
def _store_mentioning_restocking(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    define(client, PROCESS_TYPE)
    create(client, "decision", {
        "title": "Restock on Thursdays",
        "sections": [
            {"title": "Purpose", "body": "Keep the shelves full before the weekend.\n"},
            {"title": "Rationale", "body": "Restocking on Thursday means restocking once, and Friday restocking is too late.\n"},
        ],
    })
    create(client, "decision", {
        "title": "Price reviews happen weekly",
        "sections": [
            {"title": "Purpose", "body": "Keep prices in step with costs, restocking included.\n"},
            {"title": "Rationale", "body": "Costs move weekly.\n"},
        ],
    })
    create(client, "process", {
        "title": "Open the shop",
        "sections": [
            {"title": "Before opening", "body": "Unlock, then check whether restocking is due.\n"},
        ],
    })
    return client


@when(parsers.parse("the client searches the prose for {text}"), target_fixture="found")
def _search_the_prose(client, text):
    response = search(client, text)
    assert not response.faults, response.faults
    return list(response.matches)


@then("each result comes with the title of the section it matched and a snippet of it")
def _section_and_snippet(found):
    assert {(match.stub.id, match.section) for match in found} == {
        ("decision/restock-on-thursdays", "Rationale"),
        ("decision/price-reviews-happen-weekly", "Purpose"),
        ("process/open-the-shop", "Before opening"),
    }
    assert all("restocking" in match.snippet.lower() for match in found)


@then("the one whose section mentions restocking most often comes first")
def _most_often_first(found):
    assert (found[0].stub.id, found[0].section) == ("decision/restock-on-thursdays", "Rationale")
```

- [ ] **Step 2: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-10 2>&1 | grep -E "^E |passed|failed" | tail -2
```

Expected: `1 failed`, `AttributeError: 'InProcessClient' object has no attribute 'Search'`.

- [ ] **Step 3: The contract**

In `src/kb/contract/kb.proto`, add `  rpc Search(SearchRequest) returns (SearchResponse);` as the last line of `service Kb`, after `rpc Journal`. Append at the end of the file:

```proto

// The words to look for in the prose.
message SearchRequest {
  string text = 1;
}

// A section that holds a word searched for: a stub of its artifact, the
// section's title, and the words around the first match.
message Match {
  Stub stub = 1;
  string section = 2;
  string snippet = 3;
}

// The matches, the section holding the words most often first. With
// faults, a refusal: no store found.
message SearchResponse {
  repeated Match matches = 1;
  repeated Fault faults = 2;
}
```

Run `make contract`.

- [ ] **Step 4: The code**

Create `src/kb/search.py`:

```python
"""Search over the prose: every section at every depth, of every artifact, ranked by how often the words searched
for occur in its body. A word matches a whole word, whatever its case."""
import re
from typing import NamedTuple

WIDTH = 60


class Hit(NamedTuple):
    artifact: str
    section: str
    snippet: str
    count: int


def rank(artifacts, text: str) -> list[Hit]:
    """Every section whose body holds a word of the text, most occurrences first; ties in the order the store and
    the artifact hold them."""
    words = re.findall(r"\w+", text.lower())
    if not words:
        return []
    pattern = re.compile(r"\b(?:" + "|".join(re.escape(word) for word in words) + r")\b", re.IGNORECASE)
    hits = []
    for artifact in artifacts:
        for section in _sections(artifact.get("sections", [])):
            found = list(pattern.finditer(section["body"]))
            if found:
                hits.append(Hit(artifact["id"], section["title"], _snippet(section["body"], found[0]), len(found)))
    return sorted(hits, key=lambda hit: -hit.count)


def _sections(sections: list):
    for section in sections:
        yield section
        yield from _sections(section.get("sections", []))


def _snippet(body: str, found: re.Match) -> str:
    """The words around the first match, on one line, marked where they were cut."""
    start, end = max(found.start() - WIDTH, 0), min(found.end() + WIDTH, len(body))
    text = " ".join(body[start:end].split())
    return ("…" if start else "") + text + ("…" if body[end:].strip() else "")
```

In `src/kb/client.py`, after `Journal`, add:

```python

    def Search(self, request, timeout=None):
        return self._call("Search", request, kb_pb2.SearchResponse)
```

In `src/kb/servicer.py`, change the import line `from kb import canonical, journal, validation, values` to `from kb import canonical, journal, search, validation, values`. Just above `def _stub(self, field, target_id: ArtifactId):`, add:

```python
    def Search(self, request, context):
        """Every section whose prose holds a word searched for, with a stub of its artifact, most often first."""
        return kb_pb2.SearchResponse(matches=[
            kb_pb2.Match(stub=self._stub("", values.artifact_id(hit.artifact)), section=hit.section, snippet=hit.snippet)
            for hit in search.rank(self._store.artifacts(), request.text)
        ])

```

- [ ] **Step 5: Run it green, and the suite**

```bash
.venv/bin/python -m pytest -q -m slice-10 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `1 passed, 117 deselected`; `64 failed, 54 passed`.

- [ ] **Step 6: Commit**

```bash
git add src/kb/search.py src/kb/contract src/kb/servicer.py src/kb/client.py tests/calls.py tests/test_search_the_store.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 10: search the prose, ranked

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 7: Checkpoint**

Set slice 10's Status to `green`. Append at the very end of the Log:

```
- <date> slice 10 green. Someone can now: search the prose for a word and get each matching section's title and a snippet, the section saying it most often first.
  Assumption "counting whole-word matches per section body on each call, with no index, gives the ranking": <held or not>. Evidence: <the matches as (id, section, snippet); in scratch the first was ('decision/restock-on-thursdays', 'Rationale', 'Restocking on Thursday means restocking once, and Friday restocking is…')>.
  Surprised by: <nothing, or what>.
  Open questions:
  - QUESTION FOR THE SPEC: a stored file that cannot be read makes Search raise store.Unreadable through the client. Should the search skip it, answer with its fault beside the matches, or be refused? (Review Focus 2)
  - QUESTION FOR THE SPEC: a word matches whole words only, so "restock" finds nothing in "restocking". The spec says only "term frequency in the section".
  Next: slice 11.
```

Commit the plan: `Slice 10 green`.

---

### Task 4: Slice 11, follow the links two steps out

**Slice plan entry:** Slice 11, capability. Unknown: how is the route to each artifact reached in two steps given back beside its stub? Scenario:

1. kb / follow-the-links / The client follows the links two steps out

**Files:**
- Modify: `src/kb/contract/kb.proto` (the `Refs` rpc; `RefsRequest`, `Hop`, `Reached`, `RefsResponse`), then `make contract`
- Modify: `src/kb/servicer.py` (`Refs`; new module function `_not_found`, which Read now uses too)
- Modify: `src/kb/client.py` (`Refs`)
- Modify: `tests/calls.py` (new `refs`)
- Rewrite: `tests/test_follow_the_links.py`
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `values.locator`, `validation.links(artifact, schema, corpus) -> [(field, place, target)]`, `KbServicer._stub`, and `calls.write(client, artifact_id, content, message=…)` from Task 2.
- Produces:
  - `kb_pb2.RefsRequest(locator, depth)`, `kb_pb2.Hop(field, id)`, `kb_pb2.Reached(stub, route)`, `kb_pb2.RefsResponse(reached, faults)` and `InProcessClient.Refs`.
  - `servicer._not_found(artifact_id: ArtifactId) -> kb_pb2.Fault`.
  - `calls.refs(client, artifact_id, depth)`.
  - In `tests/test_follow_the_links.py`, the Background steps that slice 31 reuses, `TAG_TYPE`, and `_tagged_decision_type()`.

- [ ] **Step 1: The steps**

Append to `tests/calls.py`:

```python


def refs(client, artifact_id, depth):
    """The links out of an artifact, followed as many steps as depth says."""
    return client.Refs(kb_pb2.RefsRequest(locator=kb_pb2.Locator(id=artifact_id), depth=depth))
```

Replace the whole of `tests/test_follow_the_links.py` with:

```python
import copy

from pytest_bdd import given, parsers, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, WORK_ITEM_TYPE, create, define, refs, write
from kb import client as kb_client
from kb.contract import kb_pb2

scenarios("follow-the-links.feature")

OLDER = "decision/prices-are-reviewed-monthly"
DECISION = "decision/price-reviews-happen-weekly"
OLDER_SECTIONS = [
    {"title": "Purpose", "body": "Keep prices current.\n"},
    {"title": "Rationale", "body": "Monthly was enough once.\n"},
]
TAG_TYPE = {
    "title": "Tag",
    "version": 1,
    "schema": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]},
}


def _tagged_decision_type():
    """The decision type, whose artifacts may also carry tags."""
    decision_type = copy.deepcopy(DECISION_TYPE)
    decision_type["schema"]["properties"]["tags"] = {
        "type": "array",
        "items": {"type": "string"},
        "ref": {"targets": ["tag"], "cardinality": "many", "parts": False, "on_delete": "refuse"},
    }
    return decision_type


@given("a store where a decision supersedes an older decision", target_fixture="client")
def _store_with_a_superseded_decision(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, TAG_TYPE)
    define(client, _tagged_decision_type())
    define(client, WORK_ITEM_TYPE)
    create(client, "decision", {"title": "Prices are reviewed monthly", "sections": OLDER_SECTIONS})
    create(client, "decision", {
        "title": "Price reviews happen weekly",
        "supersedes": OLDER,
        "sections": [
            {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
            {"title": "Rationale", "body": "Costs move weekly.\n"},
        ],
    })
    return client


@given("two work items point at that decision")
def _two_work_items(client):
    create(client, "work-item", {"title": "Move the review to Mondays", "decisions": [DECISION]})
    create(client, "work-item", {"title": "Tell the pricing team", "decisions": [DECISION]})


@given(parsers.parse('the older decision is tagged "{tag}"'))
def _older_decision_tagged(client, tag):
    tagged = create(client, "tag", {"title": tag})
    changed = write(client, OLDER, {"tags": [tagged.id], "sections": OLDER_SECTIONS}, message="Tag it")
    assert not changed.faults, changed.faults


@when("the client follows the links out of the decision two steps", target_fixture="reached")
def _follow_two_steps_out(client):
    response = refs(client, DECISION, depth=2)
    assert not response.faults, response.faults
    return list(response.reached)


@then("the client is given the older decision and the tag")
def _older_decision_and_tag(reached):
    assert [(found.stub.id, found.stub.type, found.stub.title) for found in reached] == [
        (OLDER, "decision", "Prices are reviewed monthly"),
        ("tag/pricing", "tag", "pricing"),
    ]


@then("each of them comes with the route taken to it")
def _each_with_its_route(reached):
    assert {found.stub.id: [(hop.field, hop.id) for hop in found.route] for found in reached} == {
        OLDER: [("supersedes", OLDER)],
        "tag/pricing": [("supersedes", OLDER), ("tags", "tag/pricing")],
    }
```

- [ ] **Step 2: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-11 2>&1 | grep -E "^E |passed|failed" | tail -2
```

Expected: `1 failed`, `AttributeError: 'InProcessClient' object has no attribute 'Refs'`. The three Givens pass.

- [ ] **Step 3: The contract**

In `src/kb/contract/kb.proto`, add `  rpc Refs(RefsRequest) returns (RefsResponse);` as the last line of `service Kb`, after `rpc Search`. Append at the end of the file:

```proto

// The links out of an artifact, followed as many steps as depth says.
message RefsRequest {
  Locator locator = 1;
  int32 depth = 2;
}

// One step of a route: the link taken and the name it landed on.
message Hop {
  string field = 1;
  string id = 2;
}

// An artifact the links reach, with the route taken to it from the one
// asked about; its stub's field is the link of the last step.
message Reached {
  Stub stub = 1;
  repeated Hop route = 2;
}

// Each artifact reached once, by the shortest route, nearest first. With
// faults, a refusal: a bad locator, a name the store lacks, or no store
// found.
message RefsResponse {
  repeated Reached reached = 1;
  repeated Fault faults = 2;
}
```

Run `make contract`.

- [ ] **Step 4: The code**

In `src/kb/client.py`, after `Search`, add:

```python

    def Refs(self, request, timeout=None):
        return self._call("Refs", request, kb_pb2.RefsResponse)
```

In `src/kb/servicer.py`, in `Read`, change

```python
        if not self._store.holds(locator.id):
            return kb_pb2.ReadResponse(faults=[kb_pb2.Fault(
                artifact=str(locator.id), rule="not-found",
                message=f"the store holds nothing by the name {str(locator.id)!r}",
            )])
```

to

```python
        if not self._store.holds(locator.id):
            return kb_pb2.ReadResponse(faults=[_not_found(locator.id)])
```

Just above `def _stub(self, field, target_id: ArtifactId):`, add:

```python
    def Refs(self, request, context):
        """What an artifact's links reach, a step at a time out to the depth asked: each artifact once, by the
        shortest route, the one asked about never."""
        try:
            locator = values.locator(request.locator)
        except values.Refused as refused:
            return kb_pb2.RefsResponse(faults=refused.faults)
        if not self._store.holds(locator.id):
            return kb_pb2.RefsResponse(faults=[_not_found(locator.id)])
        reached, seen, frontier = [], {str(locator.id)}, [(locator.id, [])]
        for _ in range(request.depth):
            following = []
            for artifact_id, route in frontier:
                artifact = self._store.load(artifact_id)
                schema = self._store.schema(artifact_id.kind)["schema"]
                for field, _, target in validation.links(artifact, schema, self._store):
                    if target in seen:
                        continue
                    seen.add(target)
                    target_id = values.artifact_id(target)
                    taken = [*route, kb_pb2.Hop(field=field, id=target)]
                    reached.append(kb_pb2.Reached(stub=self._stub(field, target_id), route=taken))
                    following.append((target_id, taken))
            frontier = following
        return kb_pb2.RefsResponse(reached=reached)

```

and, just above `def _unclaimed(`, add:

```python
def _not_found(artifact_id: ArtifactId) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(artifact_id), rule="not-found", message=f"the store holds nothing by the name {str(artifact_id)!r}",
    )


```

- [ ] **Step 5: Run it green, slice 1.7 (Read's refusals, which now use `_not_found`), and the suite**

```bash
.venv/bin/python -m pytest -q -m "slice-11 or slice-1.7" 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `5 passed, 113 deselected`; `63 failed, 55 passed`.

- [ ] **Step 6: Commit**

```bash
git add src/kb/contract src/kb/servicer.py src/kb/client.py tests/calls.py tests/test_follow_the_links.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 11: follow the links two steps out, with the route to each

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 7: Checkpoint**

Set slice 11's Status to `green`. Append at the very end of the Log:

```
- <date> slice 11 green. Someone can now: follow the links out of a decision two steps and get the older decision and its tag, each with the route taken to it.
  Assumption "a breadth-first walk giving each artifact once, by its shortest route, as hops of field and name beside a stub": <held or not>. Evidence: <the reached stubs with their routes as (field, id) lists>.
  Surprised by: <nothing, or what>.
  Open questions:
  - For slicing (slice 31): Refs with depth 0, the default, reaches nothing; slice 31's scenarios name no depth. (Review Focus 3)
  - QUESTION FOR THE SPEC: a Refs locator with a place (a node inside the artifact) follows the whole artifact's links; the place is ignored. (Review Focus 5)
  Next: slice 12.
```

Commit the plan: `Slice 11 green`.

---

### Task 5: Slice 12, a loop in the links stops

**Slice plan entry:** Slice 12, capability. Unknown: how does resolution know which artifacts are already filled in on the path it is following, so a loop comes back as a name while the same artifact reached by another path is still filled in? Scenario:

1. kb / read-an-artifact / A loop in the links stops instead of going round

**Files:**
- Modify: `src/kb/contract/kb.proto` (`ReadRequest` gains `Level`, `level`, `depth`), then `make contract`
- Modify: `src/kb/servicer.py` (`Read` dispatches on level; `_whole`, `_resolved`)
- Modify: `tests/calls.py` (`read` takes `whole` and `depth`)
- Modify: `tests/test_read_an_artifact.py` (import `write`; four steps appended)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `validation.references(schema, corpus) -> {field: ref}`, `canonical.IDENTITY`, `content.dumps`, and the `client` fixture from the read-an-artifact Background.
- Produces: `kb_pb2.ReadRequest.SUMMARY`, `kb_pb2.ReadRequest.WHOLE`, `ReadRequest.depth`; `KbServicer._whole(locator, depth)`; `KbServicer._resolved(artifact_id, depth, on_path: set) -> dict`; `calls.read(client, artifact_id, whole=False, depth=0)`. Task 6 reads whole through it. Slice 21 adds the section level.

- [ ] **Step 1: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-12 2>&1 | grep -E "^E |passed|failed" | tail -2
```

Expected: `1 failed`, a `StepDefinitionNotFoundError` for `Given "two decisions that point at each other"`.

- [ ] **Step 2: The helper and the steps**

In `tests/calls.py`, replace `read`:

```python
def read(client, artifact_id, whole=False, depth=0):
    """A summary read, or a whole read following the links as many steps as depth says."""
    level = kb_pb2.ReadRequest.WHOLE if whole else kb_pb2.ReadRequest.SUMMARY
    return client.Read(kb_pb2.ReadRequest(locator=kb_pb2.Locator(id=artifact_id), level=level, depth=depth))
```

In `tests/test_read_an_artifact.py`, change the import line `from calls import CLIENT, DECISION_TYPE, WORK_ITEM_TYPE, create, define, read` to `from calls import CLIENT, DECISION_TYPE, WORK_ITEM_TYPE, create, define, read, write`. Append:

```python


DAILY = "decision/stock-is-counted-daily"
NIGHTLY = "decision/stock-is-counted-nightly"
COUNTING = [
    {"title": "Purpose", "body": "Know what is on the shelves.\n"},
    {"title": "Rationale", "body": "Counting catches shrinkage early.\n"},
]


@given("two decisions that point at each other")
def _two_decisions_pointing_at_each_other(client):
    create(client, "decision", {"title": "Stock is counted daily", "sections": COUNTING})
    create(client, "decision", {"title": "Stock is counted nightly", "supersedes": DAILY, "sections": COUNTING})
    changed = write(client, DAILY, {"supersedes": NIGHTLY, "sections": COUNTING}, message="Point back")
    assert not changed.faults, changed.faults


@when("the client reads the whole of one of them following its links three steps", target_fixture="whole")
def _read_one_following_three_steps(client):
    response = read(client, DAILY, whole=True, depth=3)
    assert not response.faults, response.faults
    return response


@then("the other decision is given in place of the link")
def _the_other_filled_in(whole):
    other = loads(whole.content)["supersedes"]
    assert (other["id"], other["title"]) == (NIGHTLY, "Stock is counted nightly")
    assert other["sections"] == COUNTING


@then("where that one points back, the decision being read is given as a name rather than filled in again")
def _points_back_as_a_name(whole):
    assert whole.id == DAILY
    assert loads(whole.content)["supersedes"]["supersedes"] == DAILY
```

Run Step 1's command again. Expected: `1 failed`, `AttributeError: WHOLE`. The Given passes, since the pair is made with Create and Write.

Note for slice 21: the step `the older decision is given in place of the link` there is a different sentence from this one, `the other decision is given in place of the link`. Do not merge them.

- [ ] **Step 3: The contract**

In `src/kb/contract/kb.proto`, replace

```proto
message ReadRequest {
  Locator locator = 1;
}
```

with

```proto
// A summary by default. A whole read gives the artifact's content with
// each link followed as many steps as depth says, the target in place of
// its name; a target already filled in on the way is left as its name.
message ReadRequest {
  enum Level {
    SUMMARY = 0;
    WHOLE = 1;
  }
  Locator locator = 1;
  Level level = 2;
  int32 depth = 3;
}
```

Run `make contract`.

- [ ] **Step 4: The code**

In `src/kb/servicer.py`, in `Read`, change

```python
        try:
            return self._summary(locator)
        except Unreadable as unreadable:
```

to

```python
        try:
            if request.level == kb_pb2.ReadRequest.WHOLE:
                return self._whole(locator, request.depth)
            return self._summary(locator)
        except Unreadable as unreadable:
```

and, just above `def _summary(self, locator):`, add:

```python
    def _whole(self, locator, depth: int):
        artifact = self._resolved(locator.id, depth, {str(locator.id)})
        return kb_pb2.ReadResponse(
            id=artifact["id"], type=artifact["type"],
            schema_version=artifact["schema_version"], revision=artifact["revision"],
            title=artifact["title"],
            content=dumps({key: value for key, value in artifact.items() if key not in canonical.IDENTITY}),
        )

    def _resolved(self, artifact_id: ArtifactId, depth: int, on_path: set) -> dict:
        """The artifact as stored, each link followed depth steps with the target, itself resolved, in place of its
        name. A target on the path already being filled in stays a name, so a loop ends."""
        artifact = self._store.load(artifact_id)
        if depth < 1:
            return artifact
        def fill(target):
            if target in on_path:
                return target
            return self._resolved(values.artifact_id(target), depth - 1, on_path | {target})
        resolved = dict(artifact)
        for field in validation.references(self._store.schema(artifact_id.kind)["schema"], self._store):
            value = artifact.get(field)
            if isinstance(value, list):
                resolved[field] = [fill(target) for target in value]
            elif value is not None:
                resolved[field] = fill(value)
        return resolved

```

- [ ] **Step 5: Run it green, and the suite**

```bash
.venv/bin/python -m pytest -q -m slice-12 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `1 passed, 117 deselected`; `62 failed, 56 passed`. No slice-21 scenario passes yet. Each fails on a missing step.

- [ ] **Step 6: Commit**

```bash
git add src/kb/contract src/kb/servicer.py tests/calls.py tests/test_read_an_artifact.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 12: a whole read follows links and stops at a loop

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 7: Checkpoint**

Set slice 12's Status to `green`. Append at the very end of the Log:

```
- <date> slice 12 green. Someone can now: read a decision whole following its links three steps, and get the decision it points at filled in, with the link back to the one being read given as a name.
  Assumption "resolution carries the set of names on its path, starting with the artifact read, and leaves any of them as a name": <held or not>. Evidence: <the whole read's content: supersedes filled in with id decision/stock-is-counted-nightly, whose own supersedes is the string decision/stock-is-counted-daily>.
  Surprised by: <nothing, or what>.
  Open questions:
  - QUESTION FOR THE SPEC: a link filled in carries the target's identity keys (id, type, schema_version, revision, title) beside its content, so a client can tell what it is. The spec says only "inlines each direct reference target in place of its id". Slice 21's "as the store holds it now" reads this way.
  Next: slice 13.
```

Commit the plan: `Slice 12 green`.

---

### Task 6: Slice 13, change one node inside an artifact

**Slice plan entry:** Slice 13, capability. Unknown: can a write be addressed at a section inside an artifact and the whole artifact re-validated afterwards? Scenario:

1. kb / change-an-artifact / The client changes one node inside an artifact

**Files:**
- Modify: `src/kb/values.py` (`content` takes `at_root`)
- Modify: `src/kb/servicer.py` (import `copy`; `_replace` puts a node in place; new module functions `_placed`, `_node_name`)
- Modify: `tests/calls.py` (`write` takes `path`)
- Modify: `tests/test_change_an_artifact.py` (import `loads`; three steps appended)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `calls.read(client, artifact_id, whole=True)` from Task 5; `values.Locator` (`id`, `place: tuple[str, ...]`), `values.slug`, and `canonical.IDENTITY`.
- Produces: `values.content(artifact: str, text: str, at_root: bool = True) -> dict`; `servicer._placed(artifact: dict, locator: values.Locator, node: dict) -> dict`, which raises `values.Refused` with rule `not-found`; `servicer._node_name(collection: str, item: dict) -> str`; and `calls.write(…, path="")`.

- [ ] **Step 1: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-13 2>&1 | grep -E "^E |passed|failed" | tail -2
```

Expected: `1 failed`, a `StepDefinitionNotFoundError` for `When "the client replaces the rationale of the decision, saying which role and why"`.

- [ ] **Step 2: The helper and the steps**

In `tests/calls.py`, replace `write`:

```python
def write(client, artifact_id, content, message="Change an artifact", actor=CLIENT, path=""):
    """A Write of a whole artifact, or of the node at path inside it, under the client's role unless another actor is
    given. Returns the response, faults and all."""
    return client.Write(kb_pb2.WriteRequest(
        locator=kb_pb2.Locator(id=artifact_id, path=path), content=dumps(content), actor=actor, message=message,
    ))
```

In `tests/test_change_an_artifact.py`, add `from kb.content import loads` after `from kb import client as kb_client`, and append:

```python


@when("the client replaces the rationale of the decision, saying which role and why", target_fixture="changed")
def _replace_the_rationale(client):
    before = read(client, DECISION, whole=True)
    response = write(
        client, DECISION, {"title": "Rationale", "body": "Suppliers change their prices every week.\n"},
        message="Say why weekly", path="sections/rationale",
    )
    assert not response.faults, response.faults
    return {"response": response, "before": before, "after": read(client, DECISION, whole=True)}


@then("only that section changes")
def _only_the_rationale_changes(changed):
    assert changed["response"].revision == 2
    assert loads(changed["after"].content)["sections"] == [
        SECTIONS[0], {"title": "Rationale", "body": "Suppliers change their prices every week.\n"},
    ]


@then("the rest of the decision reads as before")
def _the_rest_as_before(changed):
    before, after = loads(changed["before"].content), loads(changed["after"].content)
    assert after["sections"][0] == before["sections"][0]
    assert {key: value for key, value in after.items() if key != "sections"} == {
        key: value for key, value in before.items() if key != "sections"
    }
    assert [(seen.id, seen.type, seen.title, seen.schema_version) for seen in (changed["before"], changed["after"])] == [
        (DECISION, "decision", "Price reviews happen weekly", 1),
    ] * 2
```

Run Step 1's command again. Expected: `1 failed`, with the fault `rule: "identity"` and message `a title is given alongside the content, never inside it; the content carried the title 'Rationale'`. The section's own title is refused as if it were the artifact's.

- [ ] **Step 3: The code**

In `src/kb/values.py`, change the start of `content`

```python
def content(artifact: str, text: str) -> dict:
    """Content as a request carries it: read plainly, and holding only what a type declares. Refused with every fault."""
    try:
        tree = loads(text)
    except canonical.NotCanonical as fault:
        raise Refused([kb_pb2.Fault(artifact=artifact, path=fault.path, rule="content", message=str(fault))]) from None
    faults = []
```

to

```python
def content(artifact: str, text: str, at_root: bool = True) -> dict:
    """Content as a request carries it: read plainly, and, for a whole artifact, holding only what a type declares.
    The identity keys belong to an artifact's root, so a node inside it, a section with its title, is not held to
    them. Refused with every fault."""
    try:
        tree = loads(text)
    except canonical.NotCanonical as fault:
        raise Refused([kb_pb2.Fault(artifact=artifact, path=fault.path, rule="content", message=str(fault))]) from None
    if not at_root:
        return tree
    faults = []
```

In `src/kb/servicer.py`, add `import copy` and a blank line after the module docstring, before `from kb import canonical, …`. In `_replace`, change

```python
        locator = values.locator(replacement.locator)
        content = values.content(str(locator.id), replacement.content)
        current = draft.load(locator.id)
```

to

```python
        locator = values.locator(replacement.locator)
        content = values.content(str(locator.id), replacement.content, at_root=not locator.place)
        current = draft.load(locator.id)
        if locator.place:
            content = _placed(current, locator, content)
```

and, just above `def _not_found(artifact_id: ArtifactId) -> kb_pb2.Fault:`, add:

```python
def _placed(artifact: dict, locator: values.Locator, node: dict) -> dict:
    """The artifact's content with the node at the locator's place replaced by the one given. A place is pairs of a
    list and an item in it, a section named by its title's name and a part by its id, and may end in a field."""
    content = copy.deepcopy({key: value for key, value in artifact.items() if key not in canonical.IDENTITY})
    holder, steps = content, list(locator.place)
    while len(steps) > 1:
        collection, name = steps.pop(0), steps.pop(0)
        items = holder.get(collection, [])
        index = next((index for index, item in enumerate(items) if _node_name(collection, item) == name), None)
        if index is None:
            raise values.Refused([kb_pb2.Fault(
                artifact=str(locator.id), path="/".join(locator.place), rule="not-found",
                message=f"{str(locator.id)!r} holds nothing at {'/'.join(locator.place)!r}",
            )])
        if not steps:
            items[index] = node
            return content
        holder = items[index]
    holder[steps[0]] = node
    return content


def _node_name(collection: str, item: dict) -> str:
    """How a place names an item: a section by its title's name, a part by its id."""
    return values.slug(item["title"]) if collection == "sections" else item.get("id")


```

- [ ] **Step 4: Run it green, slice 8 (the whole-artifact Write), and the suite**

```bash
.venv/bin/python -m pytest -q -m "slice-13 or slice-8" 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `2 passed, 116 deselected`; `61 failed, 57 passed`.

- [ ] **Step 5: Commit**

```bash
git add src/kb/values.py src/kb/servicer.py tests/calls.py tests/test_change_an_artifact.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 13: change one node inside an artifact

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 6: Checkpoint**

Set slice 13's Status to `green`. Append at the very end of the Log:

```
- <date> slice 13 green. Someone can now: replace only the rationale of a decision, by its place sections/rationale, and read the rest of the decision as before at the next version.
  Assumption "a node write puts the node in place in a copy of the content and checks the whole artifact, through the same _land": <held or not>. Evidence: <revision 2, and the whole read's sections before and after>.
  Surprised by: <nothing, or what>.
  Open questions:
  - ANSWERED: a Write whose locator names a node no longer replaces the whole artifact (slice 8's question, Review Focus 1 there).
  - QUESTION FOR THE SPEC: a node write to a place that names nothing is refused with rule not-found, "'<id>' holds nothing at '<place>'"; no scenario pins it.
  - QUESTION FOR THE SPEC: a node write aimed at a part (path options/go-monthly) raises KeyError 'id' through the client, as batch 2 found for a whole Write of a type with parts. (Review Focus 1)
  - QUESTION FOR THE SPEC: the journal entry of a node write records path "", not the place written; the spec's entry carries the place. (Review Focus 4)
  Next: the whole-batch review.
```

Commit the plan: `Slice 13 green`.

---

## After slice 13

Not a slice. Run the whole-batch review over the commits of Tasks 1 to 6, using `superpowers:requesting-code-review` with this plan and the spec as the brief. Every finding goes to `slicing-into-increments`, which places it by its unknown among the slices not yet begun. No finding is coded here.

Slice 8.1 fixes a data-loss defect in `v0.1.0`, which shop-knowledge pins. Whether to tag a kb release with it, and when, is the user's call, as the 0.1 tag was. The whole-batch review should say whether anything else in this batch stands in the way of such a tag.
