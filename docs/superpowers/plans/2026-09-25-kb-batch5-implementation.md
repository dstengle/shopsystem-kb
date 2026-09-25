# kb Batch 5 Implementation Plan: slices 31, 33, 35, 37, 39 and 41

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Each task is one slice of `docs/superpowers/plans/2026-09-24-kb-slices.md`. Inside a task, follow `shopsystem-bdd:bdd-red-green` scenario by scenario. Its stop conditions, hand-back, and checkpoint apply, and they override any step here that conflicts with them.

**Goal:** The next six slices:
- A client can follow the links into an artifact as well as out of it, narrowed to one link and one kind.
- A client can search within one kind, and search the fields as well as the prose.
- A client can read the journal for one role, one piece of work, or since a time, and sees from the journal alone what landed together.
- A client can snapshot what a piece of work read, as one journal entry it is given the name of.
- A client can add an item to a collection, and kb names it.
- A client can remove an artifact nothing points at, and is refused, with every link in the way, when something does.

**Architecture:** kb is the Python package `kb` in `/home/vscode/shopsystem-kb`. A protobuf contract (`kb.contract`) sits in front of `KbServicer`, which works over a `Store`. The store is one canonical YAML file per artifact under `<root>/kb/`, and that directory is itself a git repository. `kb.values` holds the boundary conversions. `kb.validation` checks content against a type. `KbServicer._land` is the one write path: it applies operations to a `store.Draft`, checks them there, and writes only when all of them pass. This plan:
- gives `Refs` a direction, a via field and a type (slice 31);
- gives `Search` a type and a scope, and searches the title and text fields (slice 33);
- gives `Journal` role, piece-of-work and time filters (slice 35);
- adds the `Snapshot` rpc and a snapshot entry in the journal (slice 37);
- adds the `Append` rpc, and an append operation in `Apply`, through `_land` (slice 39);
- adds the `Delete` rpc, and a delete operation in `Apply`, through `_land`, with a draft that can take an artifact out (slice 41).

**Provenance:** Every code block here was assembled in a scratch clone of this repository (`/tmp/batch5/kb`, cloned at `59e7e48`) on 2026-09-25. It was run with this checkout's `.venv` and `PYTHONPATH=/tmp/batch5/kb/src`, and the tasks were applied in order. The red and green results, the suite counts, and the Review Focus reproductions below are what those runs gave. The plan was then replayed from its own text and code blocks on a fresh clone (`/tmp/batch5-replay`) by an agent that had not seen the scratch run. Every red and green matched, and the replay's `src/` and `tests/` differed from the scratch run's only by two blank lines and the loop variable in `Snapshot`, which the plan names `name` so as not to hide `content.text`. This repository was not touched except to log the batch 4 findings and to write this plan.

**Tech Stack:** Python 3.11, setuptools (src layout), protobuf + grpcio + grpcio-tools (generated code is committed; `make contract` regenerates it), python-jsonschema 4.26 with `referencing`, ruamel.yaml 0.19 (YAML 1.2), git via subprocess, pytest 9 + pytest-bdd 8.

**Spec:** `docs/superpowers/specs/2026-09-23-kb-design.md`, in particular:
- "Artifact model": Parts (an id minted by kb, `Append` returns it) and Fields (the delete rule `refuse`);
- "Serialization": the journal entry, and "Snapshot entries carry `op: snapshot` and a list of `{ artifact, revision, digest }`";
- "The contract": the `Append`, `Delete`, `Apply`, `Refs`, `Search`, `Journal` and `Snapshot` rows, and "`Write`, `Append`, and `Delete` of an id the store does not hold are refused with a fault naming the id";
- "Write path", step 4: "Deletes must have no inbound references to the node or anything beneath it."

The slice plan is `docs/superpowers/plans/2026-09-24-kb-slices.md`, slices 31, 33, 35, 37, 39 and 41, and the feature files are in `features/`. Each slice's scenarios carry `@slice-<n>`, so `.venv/bin/python -m pytest -q -m slice-31` runs one slice.

## Global Constraints

- Feature files are read-only for the implementer. Only `slicing-into-increments` edits a tag line, and only `formulating-features` edits a Given, When, or Then. Any other diff under `features/` is a stop condition.
- Code only what a scenario asserts (bdd-red-green). Where the scenarios are silent, the code is silent too, and the silence goes into the checkpoint entry as an open question. The decisions this plan makes are listed below, each tied to the spec line or scenario that asks for it.
- **Extend, never add beside.**
  - A kind in a request is converted by `values.kind`, a name by `values.artifact_id` or `values.locator`, content by `values.content`. The new conversions (`values.since`, `values.item`) sit beside them in `values.py`.
  - Stubs are made by `KbServicer._stub`. The not-found fault is made by `_not_found`, which Append, Delete and Snapshot share with Read, Refs and Write.
  - Links are found by `validation.links`. Whether a link lands on an artifact or a part inside it is `_points_at`, which Refs going in (Task 1) and Delete (Task 6) share.
  - Every change to an artifact goes through `_land`. Append and Delete are operations of `Apply` like Create and Write, so their rpcs are one-operation sets, as Create's and Write's are.
  - A whole or node write and an append share `_revise`, which checks the new content, names its items, raises the version and puts it in the draft.
  - Journal entries are written by `kb.journal`; a snapshot entry by `journal.snapshot`, which shares `_save` with `journal.write`.
  - Test helpers live in `tests/calls.py`. A type or helper two feature files need lives there rather than being copied.
- Spec, parts: "Each item carries an `id` unique within its collection, first in key order, minted by kb and never supplied by the client: from the item's `title` when the item schema has one, otherwise from the item's position, with the same collision suffix as artifacts. An id is minted once and never recomputed: removing or reordering items does not rename the others. `Append` returns it."
- Spec, contract: "`Append` | locator of a collection, item content, actor, message | item id, revision"; "`Delete` | locator, actor, message | revision, or the list of inbound references that block it"; "`Apply` | ordered list of Create/Write/Append/Delete, actor, message"; "`Refs` | locator, direction, optional via-field, optional type, depth | stubs with the path taken"; "`Search` | text, optional type, scope (`sections`, `fields`, `all`) | stubs with matching section title and snippet, ranked"; "`Journal` | filters: artifact, actor, execution, batch, since | entries"; "`Snapshot` | execution id, artifact ids | journal entry id". "Content that carries an identity key, `title` included, is refused as a violation naming the key, on `Create`, `Write`, and `Append` alike."
- Errors are a typed list of `{ artifact, path, rule, message }`. A response that carries faults is a refusal, and nothing was written.
- kb is exercised through its in-process transport.
- Each checkout has its own virtualenv. `make test` runs the suite (`.venv/bin/python -m pytest -q`). `make contract` regenerates `kb_pb2.py`, `kb_pb2.pyi` and `kb_pb2_grpc.py` from `kb.proto`, and every regenerated file is committed with the `.proto`.
- The contract's version stays `0.1` in the `.proto` header and in `CONTRACT_VERSION`, and `pyproject.toml` stays `0.1.0`, though this batch adds three rpcs and several fields. Bumping the version and tagging are the user's call and are not part of this plan (see "After slice 41").
- Work on `main` in `/home/vscode/shopsystem-kb`. A worktree needs its own `.venv` first (`make dev`).
- shop-knowledge pins kb at `v0.1.0`. Nothing here touches or runs its suite.
- Commits: `git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit`, the message ending with the Co-Authored-By line of the model that made the commit, e.g. `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- The suite prints pytest-bdd `PytestRemovedIn10Warning`s. That is the baseline, not a fault. The summary lines quoted as Expected leave out the `, N warnings in Xs` that pytest adds.
- Baseline before Task 1: `make test` → `40 failed, 78 passed`. After Tasks 1 to 6 the suite reads `37/81`, `35/83`, `31/87`, `30/88`, `22/96` and `19/99` (failed/passed). The 19 left are slices 43, 45, 46 and 51.

## Decisions this plan makes (the spec left them open or silent)

1. **Refs going in.** `RefsRequest` gains `Direction direction = 3` (`OUT = 0`, `IN = 1`), `string via = 4` and `string type = 5`.
   - Going in, the artifacts reached are those holding a link to the one asked about, or to a part inside it, in path order. A stub's `field`, and the hop's, is the field of the artifact reached that points back.
   - A via keeps only links through that field, and a type only artifacts of that kind, at every step. A type that is not a plain name is refused with `values.kind`'s fault.
   - The scenarios say only "follows the links", so their steps ask for depth 1. Depth 0 still reaches nothing, as before.
2. **Search.** `SearchRequest` gains `string type = 2` and `Scope scope = 3` (`SECTIONS = 0`, `FIELDS = 1`, `ALL = 2`). `Match` gains `string field = 4`.
   - The fields searched are the title and every other top-level field whose value is text, reference fields included (Review Focus 5). Nothing inside a part is searched.
   - A field's match has its name in `field`, `section` empty, and the words around the first match as the snippet. It is ranked with the sections by how often the words occur, an artifact's sections before its fields on a tie.
   - The Background step of search-the-store gains a fourth decision, "Restocking needs two people", whose prose never says restocking. The Background line ("two decisions and a process mention restocking in their prose") allows it, and the fields scenario's Then ("also given a decision whose title mentions restocking") presupposes one. None of the three in the Background has "restocking" in its title as a whole word: `Restock on Thursdays` holds "Restock". Slice 10's scenario is unchanged by it, since a prose search does not reach a title.
   - The existing step `the client searches the prose for {text}` becomes the fixed text `the client searches the prose for restocking`. With the parser, it would also take "restocking among decisions only" as its text.
3. **Journal filters.** `JournalRequest` gains `string role = 2`, `string execution = 3` and `string since = 4`. The spec's "actor" filter is the role; "execution" is the piece of work.
   - `since` is ISO 8601, read by `values.since`. A date alone means its midnight, a time with no zone means UTC, and an entry at that moment is included. A time that cannot be read is refused with rule `since`.
   - The spec's batch filter is slice 51's, and is not built here.
4. **Snapshot.** `rpc Snapshot(SnapshotRequest) returns (SnapshotResponse)`. `SnapshotRequest { Actor actor; repeated string artifacts; string message }`; the actor's execution is the piece of work. `SnapshotResponse { string entry; repeated Fault faults }`.
   - The entry, written by `journal.snapshot`, holds `id`, `at`, `actor`, `op: snapshot`, `read` (a list of `{ artifact, revision, digest }`, the digest the sha256 of the stored file now), `message` and `batch` (its own id). It carries no `artifact`, `path`, `revision`, `schema_version` or `digest` of its own. It is committed alone under the actor's role.
   - `Entry` gains `repeated Snapshotted read = 12`, where `Snapshotted` is `{ artifact, revision, digest }`. `_entry` reads the keys a snapshot entry lacks as empty.
   - A name that is not plain, or that the store lacks, is refused with its fault, and nothing is written.
5. **Append.** `rpc Append(AppendRequest) returns (AppendResponse)`. `AppendRequest { Locator locator; string content; Actor actor; string message }`, where the locator's path is the collection's name. `AppendResponse { string id; int32 revision; repeated Fault faults }`, `id` being the item's name alone (`count-the-float`).
   - `Operation` gains `Addition append = 3`, `Addition` being `{ Locator locator; string content }`, and `Result` gains `string item = 3`. So an append is an operation of `Apply` too, and goes through `_land`.
   - The item is converted by `values.item`: read like any node content, and refused with rule `identity`, path `id`, when it carries an `id`. Only `id` is refused, since an item's `title` is one of its fields.
   - A collection is a top-level part collection the type declares. Any other path is refused with rule `not-found`: `'<id>' holds no collection called '<path>'`.
   - The item goes at the end, and `_name_items` names it on the rule slice 14 built: from its title, or else its place counted from 1, with a number added when the name is taken.
   - The journal entry has op `append` and path `<collection>/<item>`.
   - `calls.PROCESS_TYPE`'s step items gain `uses`, a reference to a `step`, and `settings`, an object, for "an item that uses another artifact keeps its settings on itself". kb does not check a link inside an item (`validation.references` reads top-level fields only); no scenario asks it to.
6. **Delete.** `rpc Delete(DeleteRequest) returns (DeleteResponse)`. `DeleteRequest { Locator locator; Actor actor; string message }`. `DeleteResponse { int32 revision; repeated Fault faults }`.
   - `Operation` gains `Removal delete = 4`, `Removal` being `{ Locator locator }`. So a removal is an operation of `Apply` too, and goes through `_land`.
   - A removal is refused with one fault for each link that points at the artifact or a part inside it: `artifact` the one holding the link, `path` its place there (`tags/0`), rule `on_delete`, and the message naming both. This is the spec's "the list of inbound references that block it", carried as faults so a refusal looks like every other.
   - A locator naming a place inside an artifact is refused with rule `locator`; removing a part is not in this batch.
   - `Draft` can take an artifact out: `remove`, and `ids`, which the check for links reads so that an earlier operation in the set counts.
   - The journal entry has op `delete`, revision one more than the artifact's last, the schema version it had, and an empty digest, since nothing was written. `journal.write` takes `written=None` for that. The response's revision is that revision. The commit records the file's removal.

## Review Focus

In this project, tests are scenarios, and the feature files are the human gate, so no unit tests are added. Instead, each line below goes into the owning task's checkpoint entry as a `QUESTION FOR THE SPEC`, with the reproduction given here. Each was reproduced in scratch after all six tasks.

1. **Removing a type something is still of.** Reproduction: after Task 6, define the tag type, create `tag/pricing`, and `remove(client, "schema/tag")`. It answers no fault, since no link points at a type. Then `read(client, "tag/pricing")` and `Validate` raise `FileNotFoundError` through the client. Task 6 logs it.
2. **A create and a removal of one artifact in one set.** Reproduction: after Task 6, `apply(client, [creation("tag", "Temp", {}), Operation(delete=Removal(locator=Locator(id="tag/temp")))])` raises `CalledProcessError` at `git add`, since the file was saved and removed before the commit and git never knew it. The two journal entries are left written and uncommitted. Task 6 logs it.
3. **Delete and Refs going in over a store holding a file it cannot read.** Reproduction: after Task 6, write `title: [` into `tag/pricing`'s file. `remove(client, "tag/clearance")` and `refs(client, "tag/clearance", 1, inward=True)` raise `store.Unreadable` through the client, since each reads every artifact. Same family as List's and Search's. Tasks 1 and 6 log it.
4. **Append of an item that is not a mapping.** Reproduction: after Task 5, an `AppendRequest` to `process/open`'s `steps` whose content is `- a` raises `TypeError`, and one whose content is `just words` raises `TypeError`. Same family as batch 4's finding on a Write. Task 5 logs it.
5. **A search of the fields reaches a link.** Reproduction: after Task 2, with `decision/restock-on-thursdays` and a decision that supersedes it, `search(client, "thursdays", everywhere=True)` matches the second decision's `supersedes` field, snippet `decision/restock-on-thursdays`, as well as the first's title. Task 2 logs it.

---

### Task 1: Slice 31, follow the links one step, narrowed or not

**Slice plan entry:** Slice 31, capability. Unknown: none. Scenarios:

1. kb / follow-the-links / The client follows the links out of an artifact
2. kb / follow-the-links / The client follows the links into an artifact
3. kb / follow-the-links / The client narrows the links to one link and one kind

Scenario 1 goes green on its step definitions and the contract alone, on the Refs slice 11 built. It is red first for want of a step. Scenarios 2 and 3 need code.

**Files:**
- Modify: `src/kb/contract/kb.proto` (`RefsRequest`: `Direction`, `direction`, `via`, `type`), then `make contract`
- Modify: `src/kb/servicer.py` (`Refs` rewritten; new `_outward` and `_inward`; new module function `_points_at`)
- Modify: `tests/calls.py` (`refs` takes `inward`, `via`, `type_name`)
- Modify: `tests/test_follow_the_links.py` (six steps appended)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `test_follow_the_links.py`'s Background steps, `OLDER` and `DECISION`. `KbServicer._stub(field, ArtifactId)`, `_not_found`, `values.kind`, `values.locator`, `values.artifact_id`, `validation.links`, `Store.ids()`.
- Produces:
  - `kb_pb2.RefsRequest.OUT`, `RefsRequest.IN`, and `RefsRequest(locator, depth, direction, via, type)`.
  - `calls.refs(client, artifact_id, depth, inward=False, via="", type_name="")`.
  - Module function `servicer._points_at(target: str, artifact_id: ArtifactId) -> bool`, which Task 6 uses.

- [ ] **Step 1: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-31 2>&1 | grep -E "^E |passed|failed" | tail -4
```

Expected: `3 failed`, each a `StepDefinitionNotFoundError` for its When.

- [ ] **Step 2: The steps**

In `tests/calls.py`, replace `refs` with:

```python
def refs(client, artifact_id, depth, inward=False, via="", type_name=""):
    """The links out of an artifact, or into it when inward, followed as many steps as depth says, through the field
    via names and to artifacts of the kind type_name names when either is given."""
    direction = kb_pb2.RefsRequest.IN if inward else kb_pb2.RefsRequest.OUT
    return client.Refs(kb_pb2.RefsRequest(
        locator=kb_pb2.Locator(id=artifact_id), depth=depth, direction=direction, via=via, type=type_name,
    ))
```

Append to `tests/test_follow_the_links.py`:

```python


WORK_ITEMS = ["work-item/move-the-review-to-mondays", "work-item/tell-the-pricing-team"]


@when("the client follows the links out of the decision", target_fixture="reached")
def _follow_out(client):
    response = refs(client, DECISION, depth=1)
    assert not response.faults, response.faults
    return list(response.reached)


@then("the client is given a stub of the older decision")
def _stub_of_the_older_decision(reached):
    assert [(found.stub.field, found.stub.id, found.stub.type, found.stub.title) for found in reached] == [
        ("supersedes", OLDER, "decision", "Prices are reviewed monthly"),
    ]


@when("the client follows the links into the decision", target_fixture="reached")
def _follow_in(client):
    response = refs(client, DECISION, depth=1, inward=True)
    assert not response.faults, response.faults
    return list(response.reached)


@then("the client is given a stub of each work item")
def _stub_of_each_work_item(reached):
    assert [(found.stub.field, found.stub.id, found.stub.type, found.stub.title) for found in reached] == [
        ("decisions", WORK_ITEMS[0], "work-item", "Move the review to Mondays"),
        ("decisions", WORK_ITEMS[1], "work-item", "Tell the pricing team"),
    ]
    assert [[(hop.field, hop.id) for hop in found.route] for found in reached] == [
        [("decisions", WORK_ITEMS[0])], [("decisions", WORK_ITEMS[1])],
    ]


@when(
    "the client follows the links into the decision, only through the link a work item uses, and only from work items",
    target_fixture="reached",
)
def _follow_in_narrowed(client):
    response = refs(client, DECISION, depth=1, inward=True, via="decisions", type_name="work-item")
    assert not response.faults, response.faults
    return list(response.reached)


@then("the client is given both work items and nothing else")
def _both_work_items(reached):
    assert [found.stub.id for found in reached] == WORK_ITEMS
```

Run Step 1's command again. Expected: `3 failed`: one `AttributeError: OUT` and two `AttributeError: IN`.

- [ ] **Step 3: The contract**

In `src/kb/contract/kb.proto`, replace the `RefsRequest` message and the comment above it with:

```proto
// The links out of an artifact, or into it, followed as many steps as
// depth says. A via names the one field a link may be; a type, the one
// kind an artifact reached may be. Either narrows every step.
message RefsRequest {
  enum Direction {
    OUT = 0;
    IN = 1;
  }
  Locator locator = 1;
  int32 depth = 2;
  Direction direction = 3;
  string via = 4;
  string type = 5;
}
```

Replace the comment above `message Hop` with:

```proto
// One step of a route: the link taken and the name it landed on. Going
// in, the link is the field of the artifact landed on that points back.
```

Replace the comment above `message RefsResponse` with:

```proto
// Each artifact reached once, by the shortest route, nearest first. With
// faults, a refusal: a bad locator, a name the store lacks, a type that is
// not a plain name, or no store found.
```

Run `make contract`, then Step 1's command. Expected: `2 failed, 1 passed`. The out scenario passes. The two going in fail with `AssertionError`, given the older decision, since the direction is not yet read.

- [ ] **Step 4: The code**

In `src/kb/servicer.py`, replace the whole of `Refs` (from `    def Refs(self, request, context):` down to, not including, `    def List(self, request, context):`) with:

```python
    def Refs(self, request, context):
        """What an artifact's links reach, out of it or into it, a step at a time out to the depth asked: each artifact
        once, by the shortest route, the one asked about never. A via or a type narrows every step."""
        faults = []
        try:
            locator = values.locator(request.locator)
        except values.Refused as refused:
            faults += refused.faults
        try:
            kind = values.kind(request.type) if request.type else None
        except values.Refused as refused:
            faults += refused.faults
        if faults:
            return kb_pb2.RefsResponse(faults=faults)
        if not self._store.holds(locator.id):
            return kb_pb2.RefsResponse(faults=[_not_found(locator.id)])
        step = self._inward if request.direction == kb_pb2.RefsRequest.IN else self._outward
        reached, seen, frontier = [], {str(locator.id)}, [(locator.id, [])]
        for _ in range(request.depth):
            following = []
            for artifact_id, route in frontier:
                for field, other_id in step(artifact_id):
                    if str(other_id) in seen or (request.via and field != request.via):
                        continue
                    if kind is not None and other_id.kind != kind:
                        continue
                    seen.add(str(other_id))
                    taken = [*route, kb_pb2.Hop(field=field, id=str(other_id))]
                    reached.append(kb_pb2.Reached(stub=self._stub(field, other_id), route=taken))
                    following.append((other_id, taken))
            frontier = following
        return kb_pb2.RefsResponse(reached=reached)

    def _outward(self, artifact_id: ArtifactId) -> list[tuple[str, ArtifactId]]:
        """Each link out of an artifact, as the field and the name it points at."""
        artifact = self._store.load(artifact_id)
        schema = self._store.schema(artifact_id.kind)["schema"]
        return [(field, values.artifact_id(target)) for field, _, target in validation.links(artifact, schema, self._store)]

    def _inward(self, artifact_id: ArtifactId) -> list[tuple[str, ArtifactId]]:
        """Each link into an artifact or a part inside it, as the field that points there and the artifact that holds
        that field, in path order."""
        found = []
        for other_id in self._store.ids():
            other = self._store.load(other_id)
            schema = self._store.schema(other_id.kind)["schema"]
            for field, _, target in validation.links(other, schema, self._store):
                if _points_at(target, artifact_id):
                    found.append((field, other_id))
        return found

```

Just above `def _holds(artifact: dict, fields) -> bool:`, add:

```python
def _points_at(target: str, artifact_id: ArtifactId) -> bool:
    """Whether a link lands on the artifact or on a part inside it."""
    return target.partition("#")[0] == str(artifact_id)


```

- [ ] **Step 5: Run it green, and the suite**

```bash
.venv/bin/python -m pytest -q -m slice-31 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `3 passed, 115 deselected`; `37 failed, 81 passed`.

- [ ] **Step 6: Commit**

```bash
git add src/kb/contract/ src/kb/servicer.py tests/calls.py tests/test_follow_the_links.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 31: follow the links one step, narrowed or not

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 7: Checkpoint**

In `docs/superpowers/plans/2026-09-24-kb-slices.md`, set slice 31's Status to `green`. Append at the very end of the Log, and check with `tail` that it is last:

```
- <date> slice 31 green. Someone can now: follow the links out of a decision and get a stub of the older decision, follow them into it and get a stub of each work item with the field that points back, or narrow that to one link and one kind.
  Surprised by: <nothing, or what>. The out scenario went green on its step definitions and the contract alone, red first for want of a step.
  Open questions:
  - QUESTION FOR THE SPEC: the narrowed scenario cannot fail on a via or type ignored, since its Background has nothing but the two work items pointing into the decision. A scenario that shows the narrowing needs something else pointing in; that is formulating-features' call.
  - QUESTION FOR THE SPEC: going in, a link into a part of the artifact counts as a link into it; going out, a link into a part still raises values.Refused (batch 4's Review Focus 1).
  - QUESTION FOR THE SPEC: Refs going in reads every artifact, so a store holding a file it cannot read makes it raise store.Unreadable through the client. (Review Focus 3)
  - The steps ask for depth 1 where the scenarios say only "follows the links"; depth 0 still reaches nothing.
  Next: slice 33.
```

Commit the plan: `Slice 31 green`.

---

### Task 2: Slice 33, search within one kind, and the fields too

**Slice plan entry:** Slice 33, capability. Unknown: none. Scenarios:

1. kb / search-the-store / The client searches within one kind
2. kb / search-the-store / The client searches the fields as well as the prose

**Files:**
- Modify: `src/kb/contract/kb.proto` (`SearchRequest`: `Scope`, `type`, `scope`; `Match.field`), then `make contract`
- Modify: `src/kb/search.py` (`Hit.field`; `rank` takes `sections` and `fields`; new `_fields`)
- Modify: `src/kb/servicer.py` (`Search`)
- Modify: `tests/calls.py` (`search` takes `type_name` and `everywhere`)
- Modify: `tests/test_search_the_store.py` (a fourth decision in the Background; the prose step fixed; four steps appended)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `calls.create`, `define`, `DECISION_TYPE`. `KbServicer._stub`, `values.kind`, `canonical.IDENTITY`, `Store.artifacts()`.
- Produces:
  - `kb_pb2.SearchRequest(text, type, scope)` with `SearchRequest.SECTIONS`, `FIELDS`, `ALL`, and `Match.field`.
  - `search.rank(artifacts, text, sections=True, fields=False) -> list[Hit]`, `Hit(artifact, section, field, snippet, count)`.
  - `calls.search(client, text, type_name="", everywhere=False)`.

- [ ] **Step 1: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-33 2>&1 | grep -E "^E |passed|failed" | tail -3
```

Expected: `2 failed`: a `StepDefinitionNotFoundError` for `Then "the client is given the two decisions and not the process"` (the prose step's parser takes the When, with "restocking among decisions only" as its text) and one for `When "the client searches the fields and the prose for restocking"`.

- [ ] **Step 2: The steps**

In `tests/calls.py`, replace `search` with:

```python
def search(client, text, type_name="", everywhere=False):
    """A search of the prose for the text, or of the fields and the prose when everywhere, among artifacts of one kind
    when type_name is given."""
    request = kb_pb2.SearchRequest(text=text)
    if type_name:
        request.type = type_name
    if everywhere:
        request.scope = kb_pb2.SearchRequest.ALL
    return client.Search(request)
```

(The fields are set only when given, so slice 10's search still runs against the contract before Step 3.)

In `tests/test_search_the_store.py`, change the first import to `from pytest_bdd import given, scenarios, then, when`. Replace everything from the process's `create(client, "process", {` in the Background step down to the end of `_search_the_prose` with:

```python
    create(client, "process", {
        "title": "Open the shop",
        "sections": [
            {"title": "Before opening", "body": "Unlock, then check whether restocking is due.\n"},
        ],
    })
    create(client, "decision", {
        "title": "Restocking needs two people",
        "sections": [
            {"title": "Purpose", "body": "Keep the stockroom safe.\n"},
            {"title": "Rationale", "body": "Heavy boxes need a second pair of hands.\n"},
        ],
    })
    return client


@when("the client searches the prose for restocking", target_fixture="found")
def _search_the_prose(client):
    response = search(client, "restocking")
    assert not response.faults, response.faults
    return list(response.matches)
```

Append to the same file:

```python


@when("the client searches the prose for restocking among decisions only", target_fixture="found")
def _search_the_decisions(client):
    response = search(client, "restocking", type_name="decision")
    assert not response.faults, response.faults
    return list(response.matches)


@then("the client is given the two decisions and not the process")
def _the_two_decisions(found):
    assert {match.stub.id for match in found} == {"decision/restock-on-thursdays", "decision/price-reviews-happen-weekly"}
    assert all(match.stub.type == "decision" for match in found)


@when("the client searches the fields and the prose for restocking", target_fixture="found")
def _search_fields_and_prose(client):
    response = search(client, "restocking", everywhere=True)
    assert not response.faults, response.faults
    return list(response.matches)


@then("the client is also given a decision whose title mentions restocking")
def _the_decision_by_its_title(found):
    assert [(match.stub.id, match.field, match.section, match.snippet) for match in found if match.field] == [
        ("decision/restocking-needs-two-people", "title", "", "Restocking needs two people"),
    ]
    assert {(match.stub.id, match.section) for match in found if not match.field} == {
        ("decision/restock-on-thursdays", "Rationale"),
        ("decision/price-reviews-happen-weekly", "Purpose"),
        ("process/open-the-shop", "Before opening"),
    }
```

Run `.venv/bin/python -m pytest -q tests/test_search_the_store.py 2>&1 | grep -E "^E  |passed|failed"`. Expected: `2 failed, 1 passed`: slice 10's scenario passes with the fourth decision in the store; the two of slice 33 fail with `AttributeError: Protocol message SearchRequest has no "type" field.` and `AttributeError: ALL`.

- [ ] **Step 3: The contract**

In `src/kb/contract/kb.proto`, replace `SearchRequest`, `Match`, and the comment above `SearchResponse`, with their comments, by:

```proto
// The words to look for in the prose, the fields, or both, among the
// artifacts of one kind when a type is given.
message SearchRequest {
  enum Scope {
    SECTIONS = 0;
    FIELDS = 1;
    ALL = 2;
  }
  string text = 1;
  string type = 2;
  Scope scope = 3;
}

// A section or a field that holds a word searched for: a stub of its
// artifact, the section's title or the field's name, and the words around
// the first match.
message Match {
  Stub stub = 1;
  string section = 2;
  string snippet = 3;
  string field = 4;
}

// The matches, the one holding the words most often first. With faults, a
// refusal: a type that is not a plain name, or no store found.
```

Run `make contract`, then Step 2's command. Expected: `2 failed, 1 passed`, both `AssertionError`: the process is among the decisions, and no field match comes back.

- [ ] **Step 4: The code**

Replace the whole of `src/kb/search.py` with:

```python
"""Search over the prose, every section at every depth of every artifact, and over the fields, the title and every
field that holds text, ranked by how often the words searched for occur in a body or a value. A word matches a whole
word, whatever its case."""
import re
from typing import NamedTuple

from kb.canonical import IDENTITY

WIDTH = 60


class Hit(NamedTuple):
    artifact: str
    section: str
    field: str
    snippet: str
    count: int


def rank(artifacts, text: str, sections: bool = True, fields: bool = False) -> list[Hit]:
    """Every section whose body, and every field whose value, holds a word of the text, as asked, most occurrences
    first; ties in the order the store and the artifact hold them, an artifact's sections before its fields."""
    words = re.findall(r"\w+", text.lower())
    if not words:
        return []
    pattern = re.compile(r"\b(?:" + "|".join(re.escape(word) for word in words) + r")\b", re.IGNORECASE)
    hits = []
    for artifact in artifacts:
        if sections:
            for section in _sections(artifact.get("sections", [])):
                found = list(pattern.finditer(section["body"]))
                if found:
                    hits.append(Hit(artifact["id"], section["title"], "", _snippet(section["body"], found[0]), len(found)))
        if fields:
            for name, value in _fields(artifact):
                found = list(pattern.finditer(value))
                if found:
                    hits.append(Hit(artifact["id"], "", name, _snippet(value, found[0]), len(found)))
    return sorted(hits, key=lambda hit: -hit.count)


def _fields(artifact: dict):
    """The title, then every other field that holds text, in the order the artifact holds them."""
    yield "title", artifact["title"]
    for name, value in artifact.items():
        if name not in IDENTITY and name != "sections" and isinstance(value, str):
            yield name, value


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

In `src/kb/servicer.py`, replace the whole of `Search` with:

```python
    def Search(self, request, context):
        """Every section whose prose, or field whose value, holds a word searched for, as the scope asks, among the
        artifacts of one kind when a type is given, with a stub of its artifact, most often first."""
        try:
            kind = values.kind(request.type) if request.type else None
        except values.Refused as refused:
            return kb_pb2.SearchResponse(faults=refused.faults)
        artifacts = (artifact for artifact in self._store.artifacts() if kind is None or artifact["type"] == kind.name)
        scope = request.scope
        hits = search.rank(
            artifacts, request.text,
            sections=scope != kb_pb2.SearchRequest.FIELDS, fields=scope != kb_pb2.SearchRequest.SECTIONS,
        )
        return kb_pb2.SearchResponse(matches=[
            kb_pb2.Match(
                stub=self._stub("", values.artifact_id(hit.artifact)), section=hit.section, field=hit.field,
                snippet=hit.snippet,
            )
            for hit in hits
        ])
```

- [ ] **Step 5: Run it green, and the suite**

```bash
.venv/bin/python -m pytest -q tests/test_search_the_store.py 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `3 passed`; `35 failed, 83 passed`.

- [ ] **Step 6: Commit**

```bash
git add src/kb/contract/ src/kb/search.py src/kb/servicer.py tests/calls.py tests/test_search_the_store.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 33: search within one kind, and the fields too

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 7: Checkpoint**

Set slice 33's Status to `green`. Append at the very end of the Log:

```
- <date> slice 33 green. Someone can now: search the prose among decisions only and get the two decisions and not the process, or search the fields and the prose and also get a decision whose title carries the word, the match naming the field.
  Surprised by: <nothing, or what>.
  Open questions:
  - The Background step gained a fourth decision, "Restocking needs two people", whose title alone says restocking: the fields scenario's Then presupposes one, and none of the Background's three has the word whole in its title. The Background line allows it; slice 10's scenario is unchanged.
  - QUESTION FOR THE SPEC: the fields searched are the title and every top-level field holding text, reference fields included, so a search for "thursdays" matches a supersedes link to decision/restock-on-thursdays. Nothing inside a part is searched. (Review Focus 5)
  - QUESTION FOR THE SPEC: a field's match is ranked with the sections by how often the words occur; the spec ranks sections only.
  Next: slice 35.
```

Commit the plan: `Slice 33 green`.

---

### Task 3: Slice 35, read the journal by role, piece of work, time, or set

**Slice plan entry:** Slice 35, capability. Unknown: none. Scenarios:

1. kb / read-the-journal / The journal alone shows what landed together
2. kb / read-the-journal / The client reads the journal for one role
3. kb / read-the-journal / The client reads the journal for one piece of work
4. kb / read-the-journal / The client reads the journal since a time

Scenario 1 goes green on its step definitions alone: every entry has carried its set since slice 5, and a change made alone has named itself as its set since slice 9. It is red first for want of a step. Scenarios 2 to 4 need code.

**Files:**
- Modify: `src/kb/contract/kb.proto` (`JournalRequest`: `role`, `execution`, `since`), then `make contract`
- Modify: `src/kb/values.py` (new `since`)
- Modify: `src/kb/servicer.py` (imports `datetime`; `Journal`)
- Modify: `tests/calls.py` (`journal` takes `role`, `execution`, `since`)
- Modify: `tests/test_read_the_journal.py` (imports; eleven steps appended)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `test_read_the_journal.py`'s Background steps, the clock fixture, `DECISION`. `calls.apply`, `creation`, `create`. `journal.entries`.
- Produces:
  - `kb_pb2.JournalRequest(artifact, role, execution, since)`.
  - `values.since(text: str) -> datetime`, aware, refusing with rule `since`.
  - `calls.journal(client, artifact="", role="", execution="", since="")`.

- [ ] **Step 1: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-35 2>&1 | grep -E "^E |passed|failed" | tail -5
```

Expected: `4 failed`: a `StepDefinitionNotFoundError` for the Given of scenario 1 and for the When of each of the others.

- [ ] **Step 2: The steps**

In `tests/calls.py`, replace `journal` with:

```python
def journal(client, artifact="", role="", execution="", since=""):
    """The journal's entries, narrowed to those about one artifact, made by one role, for one piece of work, or at or
    after a time, by whichever are given."""
    request = kb_pb2.JournalRequest(artifact=artifact)
    for name, value in (("role", role), ("execution", execution), ("since", since)):
        if value:
            setattr(request, name, value)
    return client.Journal(request)
```

In `tests/test_read_the_journal.py`, change the `calls` import to:

```python
from calls import CLIENT, DECISION_TYPE, apply, create, creation, define, journal, write
```

Append to the same file:

```python


SECTIONS = [
    {"title": "Purpose", "body": "Keep the shop running.\n"},
    {"title": "Rationale", "body": "It was agreed.\n"},
]
TOGETHER = ["decision/restock-on-thursdays", "decision/count-the-till-nightly"]
ALONE = "decision/close-early-on-sundays"


@given("a store where two artifacts were changed in one go and a third was changed on its own")
def _two_together_and_one_alone(client):
    applied = apply(client, [
        creation("decision", "Restock on Thursdays", {"sections": SECTIONS}),
        creation("decision", "Count the till nightly", {"sections": SECTIONS}),
    ], message="Two decisions at once")
    assert not applied.faults, applied.faults
    create(client, "decision", {"title": "Close early on Sundays", "sections": SECTIONS}, message="One on its own")


@when("the client reads the journal", target_fixture="entries")
def _read_the_whole_journal(client):
    response = journal(client)
    assert not response.faults, response.faults
    return list(response.entries)


@then("the two entries from the one go name the same set of changes")
def _same_set(entries):
    together = [entry for entry in entries if entry.artifact in TOGETHER]
    assert [entry.artifact for entry in together] == TOGETHER
    assert together[0].batch == together[1].batch


@then("the entry for the change made on its own names itself as its own set")
def _its_own_set(entries):
    [alone] = [entry for entry in entries if entry.artifact == ALONE]
    assert alone.batch == alone.id


@then("the client can tell what landed together from the journal without reading anything else")
def _grouped_by_the_journal_alone(entries):
    sets = {}
    for entry in entries:
        sets.setdefault(entry.batch, []).append(entry.artifact)
    assert [artifacts for artifacts in sets.values() if len(artifacts) > 1] == [TOGETHER]


def _journal_of(client, **narrowed):
    response = journal(client, **narrowed)
    assert not response.faults, response.faults
    return [(entry.op, entry.artifact, entry.actor.role, entry.actor.execution) for entry in response.entries]


@when("the client reads the journal for the shopkeeper", target_fixture="narrowed")
def _for_the_shopkeeper(client):
    return _journal_of(client, role="shopkeeper")


@then("the client is given only the creation of the decision")
def _only_the_creation(narrowed):
    assert narrowed == [("create", DECISION, "shopkeeper", "")]


@when("the client reads the journal for that piece of work", target_fixture="narrowed")
def _for_the_piece_of_work(client):
    return _journal_of(client, execution="restock-run-12")


@then("the client is given only the change the agent made")
def _only_the_agents_change(narrowed):
    assert narrowed == [("write", DECISION, "agent", "restock-run-12")]


@when(parsers.parse("the client reads the journal since {day}"), target_fixture="narrowed")
def _since(client, day):
    return _journal_of(client, since=day)


@then("the client is given only the change made today")
def _only_todays_change(narrowed):
    assert narrowed == [("write", DECISION, "agent", "restock-run-12")]
```

Run Step 1's command again. Expected: `3 failed, 1 passed`. Scenario 1 passes. The others fail with `AttributeError: Protocol message JournalRequest has no "role" field.`, and likewise `"execution"` and `"since"`.

- [ ] **Step 3: The contract**

In `src/kb/contract/kb.proto`, replace `JournalRequest` and the comment above it with:

```proto
// Narrows the journal to the entries about one artifact, made under one
// role, for one piece of work, or at or after a time (ISO 8601, a date
// alone meaning its midnight, UTC unless it says otherwise), by each one
// given; with none, every entry.
message JournalRequest {
  string artifact = 1;
  string role = 2;
  string execution = 3;
  string since = 4;
}
```

Replace the comment above `message JournalResponse` with:

```proto
// The entries, oldest first. With faults, a refusal: a name that is not a
// plain name, a time that cannot be read, or no store found.
```

Run `make contract`, then Step 1's command. Expected: `3 failed, 1 passed`, each failure an `AssertionError` listing every entry.

- [ ] **Step 4: The code**

In `src/kb/values.py`, add `from datetime import datetime, timezone` after `from dataclasses import dataclass`, and just above `def named(kind: Kind, title: str) -> ArtifactId:` add:

```python
def since(text: str) -> datetime:
    """A time as a request names it: ISO 8601, a date alone meaning its midnight, in UTC unless it says otherwise."""
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        raise Refused([kb_pb2.Fault(
            rule="since", message=f"a time is written in ISO 8601, as 2026-09-22 or 2026-09-22T09:00:00Z; {text!r} is not",
        )]) from None
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


```

In `src/kb/servicer.py`, add `from datetime import datetime` after `import copy`, and replace the whole of `Journal` with:

```python
    def Journal(self, request, context):
        """The journal's entries, oldest first, narrowed by each of artifact, role, piece of work and time given."""
        faults = []
        try:
            artifact = str(values.artifact_id(request.artifact)) if request.artifact else ""
        except values.Refused as refused:
            faults += refused.faults
        try:
            since = values.since(request.since) if request.since else None
        except values.Refused as refused:
            faults += refused.faults
        if faults:
            return kb_pb2.JournalResponse(faults=faults)
        return kb_pb2.JournalResponse(entries=[
            _entry(entry) for entry in journal.entries(self._store.dir)
            if (not artifact or entry["artifact"] == artifact)
            and (not request.role or entry["actor"]["role"] == request.role)
            and (not request.execution or entry["actor"]["execution"] == request.execution)
            and (since is None or datetime.fromisoformat(entry["at"]) >= since)
        ])
```

- [ ] **Step 5: Run it green, and the suite**

```bash
.venv/bin/python -m pytest -q -m slice-35 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `4 passed, 114 deselected`; `31 failed, 87 passed`.

- [ ] **Step 6: Commit**

```bash
git add src/kb/contract/ src/kb/values.py src/kb/servicer.py tests/calls.py tests/test_read_the_journal.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 35: read the journal by role, piece of work, time, or set

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 7: Checkpoint**

Set slice 35's Status to `green`. Append at the very end of the Log:

```
- <date> slice 35 green. Someone can now: read the journal for the shopkeeper and get only the decision's creation, for a piece of work and get only the agent's change, or since yesterday and get only today's change; and tell from the journal alone that two entries landed together and a third on its own.
  Surprised by: <nothing, or what>. "The journal alone shows what landed together" went green on its step definitions alone, red first for want of a step.
  Open questions:
  - QUESTION FOR THE SPEC: since is ISO 8601, a date alone meaning its midnight and a time with no zone UTC, and an entry at that moment is included; a time that cannot be read is refused with rule since. No scenario pins any but a date.
  - The spec's batch filter is slice 51's.
  Next: slice 37.
```

Commit the plan: `Slice 35 green`.

---

### Task 4: Slice 37, snapshot what a piece of work read

**Slice plan entry:** Slice 37, capability. Unknown: none. Scenario:

1. kb / snapshot-what-a-piece-of-work-read / The client snapshots what a piece of work read

**Files:**
- Modify: `src/kb/contract/kb.proto` (`rpc Snapshot`; `Entry.read`; `Snapshotted`, `SnapshotRequest`, `SnapshotResponse`), then `make contract`
- Modify: `src/kb/client.py` (`Snapshot`)
- Modify: `src/kb/journal.py` (new `snapshot`; `write` and `snapshot` share `_save`)
- Modify: `src/kb/servicer.py` (`Snapshot`; `Journal` and `_entry` read an entry with no artifact of its own)
- Modify: `tests/calls.py` (new `snapshot`)
- Rewrite: `tests/test_snapshot_what_a_piece_of_work_read.py`
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `calls.CLIENT`, `DECISION_TYPE`, `PROCESS_TYPE`, `create`, `define`, `journal` (Task 3), `write`. `journal.digest`, `journal.now`, `Store.path`, `Store.commit`, `_not_found`.
- Produces:
  - `kb_pb2.SnapshotRequest(actor, artifacts, message)`, `kb_pb2.SnapshotResponse(entry, faults)`, `kb_pb2.Snapshotted(artifact, revision, digest)`, `Entry.read`.
  - `InProcessClient.Snapshot`.
  - `journal.snapshot(store_dir, *, actor, read: list[dict], message) -> Path`.
  - `calls.snapshot(client, execution, artifacts, message="Say what was read", role="agent")`.

- [ ] **Step 1: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-37 2>&1 | grep -E "^E |passed|failed" | tail -2
```

Expected: `1 failed`, a `StepDefinitionNotFoundError` for `Given "a store holding a decision at its third version and a process at its first"`.

- [ ] **Step 2: The steps**

In `tests/calls.py`, just above `def search(client,`, add:

```python
def snapshot(client, execution, artifacts, message="Say what was read", role="agent"):
    """A snapshot of the artifacts named, as they stand now, for the piece of work named, under the role given."""
    return client.Snapshot(kb_pb2.SnapshotRequest(
        actor=kb_pb2.Actor(role=role, execution=execution), artifacts=artifacts, message=message,
    ))


```

Replace the whole of `tests/test_snapshot_what_a_piece_of_work_read.py` with:

```python
import hashlib

from pytest_bdd import given, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, PROCESS_TYPE, create, define, journal, snapshot, write
from kb import client as kb_client
from kb.contract import kb_pb2

scenarios("snapshot-what-a-piece-of-work-read.feature")

DECISION = "decision/price-reviews-happen-weekly"
PROCESS = "process/open-the-shop"
EXECUTION = "restock-run-12"


def _sections(rationale):
    return [{"title": "Purpose", "body": "Keep prices in step with costs.\n"}, {"title": "Rationale", "body": rationale}]


@given("a store holding a decision at its third version and a process at its first", target_fixture="client")
def _store_with_a_decision_and_a_process(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    define(client, PROCESS_TYPE)
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": _sections("Costs move.\n")})
    for rationale in ("Costs move weekly.\n", "Costs move weekly, and the suppliers say so.\n"):
        changed = write(client, DECISION, {"sections": _sections(rationale)})
        assert not changed.faults, changed.faults
    create(client, "process", {"title": "Open the shop", "steps": [{"title": "Unlock the door"}]})
    return client


@when("the client snapshots the decision and the process for a piece of work", target_fixture="snapshotted")
def _snapshot(client):
    response = snapshot(client, EXECUTION, [DECISION, PROCESS], message="Read before restocking")
    assert not response.faults, response.faults
    return response


@then("the journal holds one entry listing each of them with the version read and a fingerprint of it")
def _one_entry_listing_each(client, root):
    [entry] = [entry for entry in journal(client).entries if entry.op == "snapshot"]
    fingerprint = {name: hashlib.sha256((root / "kb" / f"{name}.yaml").read_bytes()).hexdigest() for name in (DECISION, PROCESS)}
    assert [(read.artifact, read.revision, read.digest) for read in entry.read] == [
        (DECISION, 3, fingerprint[DECISION]), (PROCESS, 1, fingerprint[PROCESS]),
    ]
    assert (entry.actor.role, entry.actor.execution, entry.message) == ("agent", EXECUTION, "Read before restocking")


@then("the client is given the name of that entry")
def _given_the_entry(client, snapshotted):
    [entry] = [entry for entry in journal(client).entries if entry.op == "snapshot"]
    assert snapshotted.entry == entry.id
```

Run Step 1's command again. Expected: `1 failed`, `AttributeError: 'InProcessClient' object has no attribute 'Snapshot'`.

- [ ] **Step 3: The contract, and the client**

In `src/kb/contract/kb.proto`, add `  rpc Snapshot(SnapshotRequest) returns (SnapshotResponse);` as the last line of `service Kb`, after `rpc List`. Replace the comment above `message Entry` with:

```proto
// One journal entry, as the store holds it. `at` is ISO 8601 in UTC; a
// change made alone names itself as its batch. A snapshot's entry has op
// `snapshot`, lists what was read, and names no artifact of its own.
```

In `message Entry`, after `  string batch = 11;`, add `  repeated Snapshotted read = 12;`, and just after the closing `}` of `Entry` add:

```proto

// An artifact a piece of work read: the version read and the fingerprint
// of the file the store held at that version.
message Snapshotted {
  string artifact = 1;
  int32 revision = 2;
  string digest = 3;
}
```

Append to the file:

```proto

// What a piece of work read, as the store holds it now: the actor names
// the role and the piece of work, the message says why.
message SnapshotRequest {
  Actor actor = 1;
  repeated string artifacts = 2;
  string message = 3;
}

// The name of the journal entry that records the snapshot. With faults, a
// refusal: a name that is not a plain name, a name the store lacks, or no
// store found, and nothing was written.
message SnapshotResponse {
  string entry = 1;
  repeated Fault faults = 2;
}
```

Run `make contract`; `kb_pb2_grpc.py` changes too. In `src/kb/client.py`, after `List`, add:

```python

    def Snapshot(self, request, timeout=None):
        return self._call("Snapshot", request, kb_pb2.SnapshotResponse)
```

Run Step 1's command. Expected: `1 failed`, `AttributeError: 'NoneType' object has no attribute 'set_code'`: the generated base servicer's `Snapshot` answers "not implemented" on a context the in-process transport does not have.

- [ ] **Step 4: The code**

In `src/kb/journal.py`, replace the last four lines of `write` (from `    target = store_dir / "journal"` to `    return target`) with the following, which also adds `snapshot` and `_save` after it:

```python
    return _save(store_dir, at, entry)


def snapshot(store_dir: Path, *, actor, read: list[dict], message: str) -> Path:
    """Write the entry recording what a piece of work read, each artifact as { artifact, revision, digest }, and
    return its file. It names no artifact of its own and is a set of its own."""
    at = now()
    entry_id = f"{at.strftime('%Y%m%dT%H%M%S%fZ')}-1"
    entry = {
        "id": entry_id,
        "at": at.isoformat(),
        "actor": {"role": actor.role, "execution": actor.execution},
        "op": "snapshot",
        "read": read,
        "message": message,
        "batch": entry_id,
    }
    return _save(store_dir, at, entry)


def _save(store_dir: Path, at: datetime, entry: dict) -> Path:
    target = store_dir / "journal" / at.strftime("%Y") / at.strftime("%m") / at.strftime("%d") / f"{entry['id']}.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(canonical.dump(entry))
    return target
```

In `src/kb/servicer.py`, in `Journal`, change `(not artifact or entry["artifact"] == artifact)` to `(not artifact or entry.get("artifact") == artifact)`. Just above `    def _stub(self, field, target_id: ArtifactId):`, add:

```python
    def Snapshot(self, request, context):
        """One journal entry listing each artifact named with its version now and the fingerprint of its file, under
        the actor and the message given, in a commit of its own."""
        named, faults = [], []
        for name in request.artifacts:
            try:
                artifact_id = values.artifact_id(name)
            except values.Refused as refused:
                faults += refused.faults
                continue
            if not self._store.holds(artifact_id):
                faults.append(_not_found(artifact_id))
                continue
            named.append(artifact_id)
        if faults:
            return kb_pb2.SnapshotResponse(faults=faults)
        read = [
            {
                "artifact": str(artifact_id), "revision": self._store.load(artifact_id)["revision"],
                "digest": journal.digest(self._store.path(artifact_id)),
            }
            for artifact_id in named
        ]
        entry = journal.snapshot(self._store.dir, actor=request.actor, read=read, message=request.message)
        self._store.commit([entry], request.actor.role, request.message)
        return kb_pb2.SnapshotResponse(entry=entry.stem)

```

Replace the whole of `_entry` with:

```python
def _entry(entry: dict) -> kb_pb2.Entry:
    """An entry as the contract carries it. A snapshot's entry has no artifact, place, version or fingerprint of its
    own, only what was read."""
    return kb_pb2.Entry(
        id=entry["id"], at=entry["at"], actor=kb_pb2.Actor(**entry["actor"]), op=entry["op"],
        artifact=entry.get("artifact", ""), path=entry.get("path", ""), revision=entry.get("revision", 0),
        schema_version=entry.get("schema_version", 0), digest=entry.get("digest", ""), message=entry["message"],
        batch=entry["batch"], read=[kb_pb2.Snapshotted(**read) for read in entry.get("read", [])],
    )
```

- [ ] **Step 5: Run it green, and the suite**

```bash
.venv/bin/python -m pytest -q -m slice-37 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `1 passed, 117 deselected`; `30 failed, 88 passed`.

- [ ] **Step 6: Commit**

```bash
git add src/kb/contract/ src/kb/client.py src/kb/journal.py src/kb/servicer.py tests/calls.py tests/test_snapshot_what_a_piece_of_work_read.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 37: snapshot what a piece of work read

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 7: Checkpoint**

Set slice 37's Status to `green`. Append at the very end of the Log:

```
- <date> slice 37 green. Someone can now: snapshot a decision at its third version and a process at its first for a piece of work, and find one journal entry listing each with its version and fingerprint, under the name they were given.
  Surprised by: <nothing, or what>.
  Open questions:
  - QUESTION FOR THE SPEC: a snapshot entry names no artifact of its own, so reading the journal for one artifact does not return the snapshots that list it.
  - QUESTION FOR THE SPEC: a snapshot of no artifacts writes an entry listing nothing.
  - QUESTION FOR THE SPEC: the actor carries the piece of work, and the request a message, neither in the spec's row; a snapshot with no role or no message raises CalledProcessError at the commit, as Create has since slice 1 (batch 4's minor findings).
  Next: slice 39.
```

Commit the plan: `Slice 37 green`.

---

### Task 5: Slice 39, add an item to a collection, named by kb

**Slice plan entry:** Slice 39, capability. Unknown: none. Scenarios:

1. kb / add-an-item-to-a-collection / The client adds an item to a collection
2. kb / add-an-item-to-a-collection / An item that uses another artifact keeps its settings on itself
3. kb / add-an-item-to-a-collection / The name of a new item comes from its title
4. kb / add-an-item-to-a-collection / An item of a kind that carries no title is named by its place
5. kb / add-an-item-to-a-collection / A second item with a title already used in the collection gets a name of its own
6. kb / add-an-item-to-a-collection / Taking an item out does not rename the items left
7. kb / add-an-item-to-a-collection / An item whose content settles what only the store settles is refused
8. kb / add-an-item-to-a-collection / Adding an item to something the store does not hold is refused

Scenario 6 goes green on its step definitions alone: a Write that leaves an item out keeps the names of the others, as slice 14 built. It is red first for want of a step. The other seven need code.

**Files:**
- Modify: `src/kb/contract/kb.proto` (`rpc Append`; `Operation.append`; `Addition`; `Result.item`; `AppendRequest`, `AppendResponse`), then `make contract`
- Modify: `src/kb/client.py` (`Append`)
- Modify: `src/kb/values.py` (new `item`)
- Modify: `src/kb/servicer.py` (new `Change`; `Append`; `_land` and `_apply` carry a `Change`; `_replace` ends in `_revise`; new `_append`; new module functions `_revise` and `_content_of`, which `_placed` uses)
- Modify: `tests/calls.py` (new `append`; `PROCESS_TYPE`'s items gain `uses` and `settings`)
- Modify: `tests/test_add_an_item_to_a_collection.py` (imports; constants; twenty steps appended)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `test_add_an_item_to_a_collection.py`'s Background, `STEP_TYPE`, `CHECKLIST_TYPE`, `CHECKLIST`, `CHECKS`, and slice 14's Given with its `named` fixture. `calls.everything_under`, `journal`, `read`, `write`, `define`, `create`. `_name_items`, `_placed`, `_not_found`, `values.content`, `values.locator`.
- Produces:
  - `kb_pb2.AppendRequest(locator, content, actor, message)`, `kb_pb2.AppendResponse(id, revision, faults)`, `kb_pb2.Addition(locator, content)`, `Operation.append`, `Result.item`.
  - `InProcessClient.Append`.
  - `values.item(artifact: str, text: str) -> dict`.
  - `servicer.Change(op, artifact_id, path="", item="")`, a `NamedTuple`; `_apply` returns one. Task 6 adds the op `delete`.
  - Module functions `servicer._revise(draft, artifact_id, current, content) -> None` and `servicer._content_of(artifact) -> dict`.
  - `calls.append(client, artifact_id, collection, content, message="Add an item", actor=CLIENT)`.

- [ ] **Step 1: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-39 2>&1 | grep -E "^E |passed|failed" | tail -9
```

Expected: `8 failed`, each a `StepDefinitionNotFoundError`, for a When, or, in scenario 4, for its Given.

- [ ] **Step 2: The steps**

In `tests/calls.py`, just above `def journal(client,`, add:

```python
def append(client, artifact_id, collection, content, message="Add an item", actor=CLIENT):
    """An Append of one item to the collection named inside an artifact, under the client's role unless another actor
    is given. Returns the response, faults and all."""
    return client.Append(kb_pb2.AppendRequest(
        locator=kb_pb2.Locator(id=artifact_id, path=collection), content=dumps(content), actor=actor, message=message,
    ))


```

In `PROCESS_TYPE`, after the item property `"branches": {"type": "array", "items": {"type": "string"}},`, add:

```python
                        "uses": {
                            "type": "string",
                            "ref": {"targets": ["step"], "cardinality": "one", "parts": False, "on_delete": "refuse"},
                        },
                        "settings": {"type": "object"},
```

In `tests/test_add_an_item_to_a_collection.py`, change the first two imports to:

```python
from pytest_bdd import given, parsers, scenarios, then, when

from calls import CLIENT, PROCESS_TYPE, append, create, define, everything_under, journal, read, write
```

After the line `CHECKS = [{"says": "Lights off"}, {"says": "Till counted"}, {"says": "Door locked"}]`, add:

```python
PROCESS = "process/open-the-shop"
SHARED = "step/count-the-till"
STEPS = [
    {"id": "unlock-the-door", "title": "Unlock the door", "body": "Front door first."},
    {"id": "turn-on-the-lights", "title": "Turn on the lights", "body": "Shop floor, then the stockroom."},
]
```

Append to the same file:

```python


def _steps(client):
    return loads(read(client, PROCESS, whole=True).content)["steps"]


def _added(client, content, collection="steps", artifact_id=PROCESS, message="Add a step before opening"):
    response = append(client, artifact_id, collection, content, message=message)
    assert not response.faults, response.faults
    return {"response": response, "sent": content}


@when("the client adds a step to the process, saying which role and why", target_fixture="added")
def _add_a_step(client):
    return _added(client, {"title": "Count the float", "body": "Every note and coin in the till."})


@then("the client is given the new item's name and the artifact's new version")
def _given_name_and_version(client, added):
    assert (added["response"].id, added["response"].revision) == ("count-the-float", 2)
    entry = journal(client, PROCESS).entries[-1]
    assert (entry.op, entry.path, entry.revision, entry.actor.role, entry.message) == (
        "append", "steps/count-the-float", 2, "client", "Add a step before opening",
    )


@then("the new item comes after the items already there")
def _after_the_others(client):
    assert _steps(client) == [
        *STEPS, {"id": "count-the-float", "title": "Count the float", "body": "Every note and coin in the till."},
    ]


@when(parsers.parse('the client adds a step titled "{title}" to the process, saying which role and why'), target_fixture="added")
def _add_a_titled_step(client, title):
    return _added(client, {"title": title})


@then("the name the client is given for the new item is made from that title")
def _named_from_its_title(client, added):
    assert added["response"].id == "count-what-is-on-the-shelf"
    assert _steps(client)[-1] == {"id": "count-what-is-on-the-shelf", "title": "Count what is on the shelf"}


@then("the client never said what the name should be")
def _never_said(added):
    assert "id" not in added["sent"]
    assert set(kb_pb2.AppendRequest.DESCRIPTOR.fields_by_name) == {"locator", "content", "actor", "message"}


@given("an artifact holding a collection whose items carry no title of their own")
def _checklist(client):
    define(client, CHECKLIST_TYPE)
    create(client, "checklist", {"title": "Closing checks", "checks": CHECKS})


@when("the client adds an item to that collection, saying which role and why", target_fixture="added")
def _add_a_check(client):
    return _added(client, {"says": "Alarm set"}, collection="checks", artifact_id=CHECKLIST, message="Set the alarm too")


@then("the name the client is given for the new item is made from its place in the collection")
def _named_from_its_place(client, added):
    assert added["response"].id == "4"
    checks = loads(read(client, CHECKLIST, whole=True).content)["checks"]
    assert [check["id"] for check in checks] == ["1", "2", "3", "4"]
    assert checks[3] == {"id": "4", "says": "Alarm set"}


@when("the client adds a step whose title is already used by a step of that process, saying which role and why", target_fixture="added")
def _add_a_step_with_a_used_title(client):
    return _added(client, {"title": "Unlock the door", "body": "The back door too."})


@then("the name the client is given for the new item is the name already taken with a number added")
def _numbered(client, added):
    assert added["response"].id == "unlock-the-door-2"
    assert _steps(client)[-1] == {"id": "unlock-the-door-2", "title": "Unlock the door", "body": "The back door too."}


@then("the step already there keeps the name it had")
def _first_keeps_its_name(client):
    assert _steps(client)[0] == STEPS[0]


@when("the client takes the first item out of that collection, saying which role and why", target_fixture="left")
def _take_the_first_out(client, named):
    response = write(client, CHECKLIST, {"checks": [named["2"], named["3"]]}, message="Lights are on a timer now")
    assert not response.faults, response.faults
    return loads(read(client, CHECKLIST, whole=True).content)["checks"]


@then("every item left keeps the name it was given when it was added")
def _left_keep_their_names(named, left):
    assert left == [named["2"], named["3"]]


@then("no item is named again from where it now sits")
def _not_named_from_its_place(left):
    assert [check["id"] for check in left] == ["2", "3"]
    assert left[0]["id"] != "1"


@when("the client adds a step that points at the shared step together with its settings, saying which role and why", target_fixture="added")
def _add_a_step_using_the_shared_one(client):
    return _added(client, {"title": "Count the till", "uses": SHARED, "settings": {"float": 150}})


@then("the settings are held by the new item")
def _settings_on_the_item(client, added):
    assert _steps(client)[-1] == {"id": "count-the-till", "title": "Count the till", "uses": SHARED, "settings": {"float": 150}}


@then("the shared step is unchanged")
def _shared_step_unchanged(client):
    shared = read(client, SHARED, whole=True)
    assert (shared.revision, loads(shared.content)) == (1, {"body": "Count every note and coin.\n"})


@when("the client adds a step whose content carries a name of its own, saying which role and why", target_fixture="attempt")
def _add_a_step_naming_itself(client):
    before = read(client, PROCESS, whole=True)
    response = append(client, PROCESS, "steps", {"id": "count-the-float", "title": "Count the float"})
    return {"response": response, "before": before}


@then(
    "the item is rejected because content holds only what the type declares, and the thing it carried that only the "
    "store settles is named back"
)
def _rejected_for_its_name(attempt):
    assert [(fault.artifact, fault.path, fault.rule) for fault in attempt["response"].faults] == [(PROCESS, "id", "identity")]
    assert "'count-the-float'" in attempt["response"].faults[0].message


@then("the process holds the steps it held before, at the version it held before")
def _process_as_it_was(client, attempt):
    after = read(client, PROCESS, whole=True)
    assert (after.revision, loads(after.content)) == (attempt["before"].revision, loads(attempt["before"].content))
    assert _steps(client) == STEPS


@when("the client adds a step to a process by a name the store holds nothing under, saying which role and why", target_fixture="attempt")
def _add_to_nothing(root, client):
    before = everything_under(root)
    response = append(client, "process/close-the-shop", "steps", {"title": "Lock the door"})
    return {"response": response, "before": before, "after": everything_under(root)}


@then("the item is rejected because the store holds nothing by that name, and the name asked for is given back")
def _rejected_for_nothing(attempt):
    assert [(fault.artifact, fault.rule) for fault in attempt["response"].faults] == [("process/close-the-shop", "not-found")]
    assert "'process/close-the-shop'" in attempt["response"].faults[0].message


@then("nothing is written anywhere in the store")
def _nothing_written(attempt):
    assert attempt["after"] == attempt["before"]
```

Run Step 1's command again. Expected: `7 failed, 1 passed`. "Taking an item out does not rename the items left" passes; the seven fail with `AttributeError: 'InProcessClient' object has no attribute 'Append'`. Run `.venv/bin/python -m pytest -q -m "slice-14 or slice-21" 2>&1 | tail -1` too: `7 passed`, since `PROCESS_TYPE`'s new item fields change nothing they assert.

- [ ] **Step 3: The contract, and the client**

In `src/kb/contract/kb.proto`, add `  rpc Append(AppendRequest) returns (AppendResponse);` as the last line of `service Kb`, after `rpc Snapshot`. Replace `Operation` and the comment above it with:

```proto
// One change in a set: a create, a replacement, or an item added, with no
// role or message of its own, since the set carries those.
message Operation {
  oneof operation {
    Creation create = 1;
    Replacement write = 2;
    Addition append = 3;
  }
}
```

Just above the comment `// Every operation lands, in order, as one change, or none does.`, add:

```proto
// One item for a collection inside an artifact the store holds: the
// locator's path is the collection's name. kb names the item.
message Addition {
  Locator locator = 1;
  string content = 2;  // canonical YAML: the item's fields, never its id
}

```

Replace `message Result` with:

```proto
// The artifact changed and its version now; for an item added, the name
// kb gave it.
message Result {
  string id = 1;
  int32 revision = 2;
  string item = 3;
}
```

Append to the file:

```proto

// One item added at the end of a collection inside an artifact the store
// holds: the locator's path is the collection's name, and kb names the
// item.
message AppendRequest {
  Locator locator = 1;
  string content = 2;  // canonical YAML: the item's fields, never its id
  Actor actor = 3;
  string message = 4;
}

// The name kb gave the item, and the artifact's version now. With faults,
// a refusal, and the artifact is as it was.
message AppendResponse {
  string id = 1;
  int32 revision = 2;
  repeated Fault faults = 3;
}
```

Run `make contract`. In `src/kb/client.py`, after `Snapshot`, add:

```python

    def Append(self, request, timeout=None):
        return self._call("Append", request, kb_pb2.AppendResponse)
```

Run Step 1's command. Expected: `7 failed, 1 passed`, the seven with `AttributeError: 'NoneType' object has no attribute 'set_code'`.

- [ ] **Step 4: The code**

In `src/kb/values.py`, just above `def root(text: str) -> Path:`, add:

```python
def item(artifact: str, text: str) -> dict:
    """An item as a request carries it: read plainly, and never carrying its own name, which kb gives. Refused with
    the fault that names what it carried."""
    tree = content(artifact, text, at_root=False)
    if "id" in tree:
        raise Refused([kb_pb2.Fault(
            artifact=artifact, path="id", rule="identity",
            message=f"content holds only what the type declares; an item's id is settled by the store, and the content carried id: {tree['id']!r}",
        )])
    return tree


```

In `src/kb/servicer.py`:

1. After `from datetime import datetime`, add `from typing import NamedTuple`.
2. After `METASCHEMA_ID = ArtifactId(Kind("schema"), "schema")`, add:

```python


class Change(NamedTuple):
    """What one operation did, to which artifact, at which place in it, and, for an item added, the item's name."""
    op: str
    artifact_id: ArtifactId
    path: str = ""
    item: str = ""
```

3. Just above `    def Apply(self, request, context):`, add:

```python
    def Append(self, request, context):
        addition = kb_pb2.Addition(locator=request.locator, content=request.content)
        landed = self._land([kb_pb2.Operation(append=addition)], request.actor, request.message)
        if landed.faults:
            return kb_pb2.AppendResponse(faults=landed.faults)
        return kb_pb2.AppendResponse(id=landed.results[0].item, revision=landed.results[0].revision)

```

4. In `_land`, replace everything from `        texts = []` down to, not including, `        self._store.commit(written, actor.role, message)` with:

```python
        texts = []
        for change in touched:
            try:
                texts.append((change, canonical.dump(draft.load(change.artifact_id))))
            except canonical.NotCanonical as fault:
                faults.append(kb_pb2.Fault(artifact=str(change.artifact_id), rule="content", message=str(fault)))
        if faults:
            return kb_pb2.ApplyResponse(faults=faults)
        written, results, batch = [], [], ""
        for seq, (change, text) in enumerate(texts, start=1):
            artifact = draft.load(change.artifact_id)
            path = self._store.save(change.artifact_id, text)
            entry = journal.write(
                self._store.dir, actor=actor, op=change.op, artifact=str(change.artifact_id), path=change.path,
                revision=artifact["revision"], schema_version=artifact["schema_version"],
                written=path, message=message, seq=seq, batch=batch,
            )
            batch = batch or entry.stem
            written += [path, entry]
            results.append(kb_pb2.Result(id=str(change.artifact_id), revision=artifact["revision"], item=change.item))
```

5. Replace the whole of `_apply` with:

```python
    def _apply(self, draft: Draft, operation: kb_pb2.Operation) -> Change:
        """One operation applied to the draft. Returns what it did; raises values.Refused."""
        which = operation.WhichOneof("operation")
        if which == "create":
            return Change("create", self._create(draft, operation.create))
        if which == "append":
            return self._append(draft, operation.append)
        return Change("write", self._replace(draft, operation.write))
```

6. In `_replace`, replace everything from `        schema = draft.schema(locator.id.kind)` to the end of the method with the following, which also adds `_append` after it:

```python
        _revise(draft, locator.id, current, content)
        return locator.id

    def _append(self, draft: Draft, addition: kb_pb2.Addition) -> Change:
        """One item put at the end of a collection the artifact's type declares, and named there."""
        locator = values.locator(addition.locator)
        if not draft.holds(locator.id):
            raise values.Refused([_not_found(locator.id)])
        item = values.item(str(locator.id), addition.content)
        collection = "/".join(locator.place)
        if collection not in draft.schema(locator.id.kind)["schema"].get("parts", {}):
            raise values.Refused([kb_pb2.Fault(
                artifact=str(locator.id), path=collection, rule="not-found",
                message=f"{str(locator.id)!r} holds no collection called {collection!r}",
            )])
        current = draft.load(locator.id)
        content = _content_of(current)
        content.setdefault(collection, []).append(item)
        _revise(draft, locator.id, current, content)
        return Change("append", locator.id, f"{collection}/{item['id']}", item["id"])
```

7. Just above `def _placed(artifact: dict, locator: values.Locator, node: dict) -> dict:`, add:

```python
def _revise(draft: Draft, artifact_id: ArtifactId, current: dict, content: dict) -> None:
    """The artifact's next version put in the draft: the content checked against the current version of its type,
    its items named, its version up by one, its title kept. Raises values.Refused with every fault."""
    schema = draft.schema(artifact_id.kind)
    faults = validation.validate(str(artifact_id), {"title": current["title"], **content}, schema["schema"], draft)
    if faults:
        raise values.Refused(faults)
    _name_items(schema["schema"], content, keep_named=True)
    artifact = {
        **content,
        "id": current["id"], "type": current["type"],
        "schema_version": schema["version"], "revision": current["revision"] + 1, "title": current["title"],
    }
    draft.put(artifact_id, canonical.order(artifact, schema["schema"]))


def _content_of(artifact: dict) -> dict:
    """A copy of what an artifact holds but its identity keys, to be changed without changing it."""
    return copy.deepcopy({key: value for key, value in artifact.items() if key not in canonical.IDENTITY})


```

8. In `_placed`, replace `    content = copy.deepcopy({key: value for key, value in artifact.items() if key not in canonical.IDENTITY})` with `    content = _content_of(artifact)`.

(`_name_items` names the new item in place, on the same dict `values.item` gave, so `item["id"]` is its name once `_revise` returns.)

- [ ] **Step 5: Run it green, and the suite**

```bash
.venv/bin/python -m pytest -q -m slice-39 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `8 passed, 110 deselected`; `22 failed, 96 passed`.

- [ ] **Step 6: Commit**

```bash
git add src/kb/contract/ src/kb/client.py src/kb/values.py src/kb/servicer.py tests/calls.py tests/test_add_an_item_to_a_collection.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 39: add an item to a collection, named by kb

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 7: Checkpoint**

Set slice 39's Status to `green`. Append at the very end of the Log:

```
- <date> slice 39 green. Someone can now: add a step to a process and be given its name and the process's new version, the step last; have it named from its title, from its place when items carry no title, or with a number added when the title is used; add a step that uses the shared step with its own settings, kept on the step; take an item out and find the others keep their names; and be refused an item carrying its own name, or an add to a process the store lacks, with nothing written.
  Surprised by: <nothing, or what>. "Taking an item out does not rename the items left" went green on its step definitions alone, on the Write slice 14 built, red first for want of a step.
  Open questions:
  - QUESTION FOR THE SPEC: an item whose content is not a mapping (`- a`, or a bare scalar) raises TypeError through the client, as batch 4 found for a Write. (Review Focus 4)
  - QUESTION FOR THE SPEC: an append names a top-level collection the type declares; any other path is refused with rule not-found, and a nested collection cannot be added to. No scenario pins either.
  - QUESTION FOR THE SPEC: a link inside an item (the new step's uses) is not checked for landing, since only top-level fields are read for links.
  - An append is an operation of Apply too, through _land, as the spec's Apply row lists it; no scenario adds an item in a set.
  Next: slice 41.
```

Commit the plan: `Slice 39 green`.

---

### Task 6: Slice 41, remove an artifact, or be refused

**Slice plan entry:** Slice 41, capability. Unknown: none. Scenarios:

1. kb / remove-an-artifact / The client removes an artifact nothing points at
2. kb / remove-an-artifact / A removal something points at is refused
3. kb / remove-an-artifact / Removing something the store does not hold is refused

**Files:**
- Modify: `src/kb/contract/kb.proto` (`rpc Delete`; `Operation.delete`; `Removal`; `DeleteRequest`, `DeleteResponse`), then `make contract`
- Modify: `src/kb/client.py` (`Delete`)
- Modify: `src/kb/store.py` (`Store.remove`; `Draft.remove`, `Draft.ids`, and `holds` and `put` aware of what was removed)
- Modify: `src/kb/journal.py` (`write` takes `written=None`)
- Modify: `src/kb/servicer.py` (`Delete`; `_land` writes a removal; `_apply` dispatches `delete`; new `_delete`)
- Modify: `tests/calls.py` (new `remove`)
- Rewrite: `tests/test_remove_an_artifact.py`
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `calls.CLIENT`, `TAG_TYPE`, `tagged_decision_type`, `create`, `define`, `everything_under`, `journal`, `listing`, `read`. `servicer.Change` (Task 5), `_points_at` (Task 1), `_not_found`, `validation.links`, `values.locator`.
- Produces:
  - `kb_pb2.DeleteRequest(locator, actor, message)`, `kb_pb2.DeleteResponse(revision, faults)`, `kb_pb2.Removal(locator)`, `Operation.delete`.
  - `InProcessClient.Delete`.
  - `Store.remove(artifact_id) -> Path`; `Draft.remove(artifact_id) -> None`, `Draft.ids() -> list[ArtifactId]`.
  - `journal.write(..., written: Path | None, ...)`.
  - `calls.remove(client, artifact_id, message="Remove an artifact", actor=CLIENT)`.

- [ ] **Step 1: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-41 2>&1 | grep -E "^E |passed|failed" | tail -4
```

Expected: `3 failed`, each a `StepDefinitionNotFoundError` for `Given "a store holding a tag nothing points at"`.

- [ ] **Step 2: The steps**

In `tests/calls.py`, just above `def journal(client,`, add:

```python
def remove(client, artifact_id, message="Remove an artifact", actor=CLIENT):
    """A Delete of a whole artifact, under the client's role unless another actor is given. Returns the response,
    faults and all."""
    return client.Delete(kb_pb2.DeleteRequest(locator=kb_pb2.Locator(id=artifact_id), actor=actor, message=message))


```

Replace the whole of `tests/test_remove_an_artifact.py` with:

```python
import subprocess

from pytest_bdd import given, scenarios, then, when

from calls import CLIENT, TAG_TYPE, create, define, everything_under, journal, listing, read, remove, tagged_decision_type
from kb import client as kb_client
from kb.contract import kb_pb2

scenarios("remove-an-artifact.feature")

LOOSE = "tag/clearance"
HELD = "tag/pricing"
DECISION = "decision/price-reviews-happen-weekly"


@given("a store holding a tag nothing points at", target_fixture="client")
def _store_with_a_loose_tag(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, TAG_TYPE)
    define(client, tagged_decision_type())
    create(client, "tag", {"title": "Clearance"})
    return client


@given("a tag a decision points at")
def _a_tag_in_use(client):
    create(client, "tag", {"title": "Pricing"})
    create(client, "decision", {
        "title": "Price reviews happen weekly",
        "tags": [HELD],
        "sections": [
            {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
            {"title": "Rationale", "body": "Costs move weekly.\n"},
        ],
    })


@when("the client removes the tag nothing points at, saying which role and why", target_fixture="removed")
def _remove_the_loose_tag(client):
    response = remove(client, LOOSE, message="Nothing is on clearance")
    assert not response.faults, response.faults
    return response


@then("the store no longer holds it")
def _no_longer_held(client, root):
    assert [fault.rule for fault in read(client, LOOSE).faults] == ["not-found"]
    assert not (root / "kb" / f"{LOOSE}.yaml").exists()
    assert list(listing(client, "tag", ids_only=True).ids) == [HELD]


@then("the removal is recorded like any other change")
def _recorded(client, root, removed):
    entry = journal(client, LOOSE).entries[-1]
    assert (entry.op, entry.revision, entry.actor.role, entry.message, entry.batch) == (
        "delete", 2, "client", "Nothing is on clearance", entry.id,
    )
    assert removed.revision == 2
    git = ["git", "-C", str(root / "kb")]
    assert subprocess.run([*git, "log", "-1", "--format=%an%x09%s"], capture_output=True, text=True, check=True).stdout.strip() == (
        "client\tNothing is on clearance"
    )
    changed = subprocess.run([*git, "show", "--name-status", "--format=", "HEAD"], capture_output=True, text=True, check=True).stdout
    assert f"D\t{LOOSE}.yaml" in changed.splitlines()


@when("the client removes the tag the decision points at, saying which role and why", target_fixture="attempt")
def _remove_the_held_tag(root, client):
    before = everything_under(root)
    response = remove(client, HELD, message="Pricing is everywhere anyway")
    return {"response": response, "before": before, "after": everything_under(root)}


@then("the removal is rejected because something still points at it")
def _rejected_while_pointed_at(client, attempt):
    assert attempt["response"].faults
    assert {fault.rule for fault in attempt["response"].faults} == {"on_delete"}
    assert attempt["after"] == attempt["before"]
    assert not read(client, HELD).faults


@then("the client is given every link that blocks it")
def _every_blocking_link(attempt):
    assert [(fault.artifact, fault.path) for fault in attempt["response"].faults] == [(DECISION, "tags/0")]
    assert f"'{HELD}'" in attempt["response"].faults[0].message


@when("the client removes an artifact by a name the store holds nothing under, saying which role and why", target_fixture="attempt")
def _remove_nothing(root, client):
    before = everything_under(root)
    response = remove(client, "tag/seasonal", message="No more seasons")
    return {"response": response, "before": before, "after": everything_under(root)}


@then("the removal is rejected because the store holds nothing by that name, and the name asked for is given back")
def _rejected_for_nothing(attempt):
    assert [(fault.artifact, fault.rule) for fault in attempt["response"].faults] == [("tag/seasonal", "not-found")]
    assert "'tag/seasonal'" in attempt["response"].faults[0].message


@then("the store holds what it held before")
def _held_as_before(attempt):
    assert attempt["after"] == attempt["before"]
```

Run Step 1's command again. Expected: `3 failed`, each `AttributeError: 'InProcessClient' object has no attribute 'Delete'`.

- [ ] **Step 3: The contract, and the client**

In `src/kb/contract/kb.proto`, add `  rpc Delete(DeleteRequest) returns (DeleteResponse);` as the last line of `service Kb`, after `rpc Append`. Replace `Operation` and the comment above it with:

```proto
// One change in a set: a create, a replacement, an item added, or a
// removal, with no role or message of its own, since the set carries those.
message Operation {
  oneof operation {
    Creation create = 1;
    Replacement write = 2;
    Addition append = 3;
    Removal delete = 4;
  }
}
```

Just above the comment `// Every operation lands, in order, as one change, or none does.`, add:

```proto
// A whole artifact the store holds, to be taken out.
message Removal {
  Locator locator = 1;
}

```

Append to the file:

```proto

// A whole artifact the store holds, taken out, as long as nothing points
// at it.
message DeleteRequest {
  Locator locator = 1;
  Actor actor = 2;
  string message = 3;
}

// The version the removal left behind. With faults, a refusal, and the
// store is as it was: a bad locator, a name the store lacks, or, one fault
// each, every link that points at the artifact, naming the artifact that
// holds it and its place there.
message DeleteResponse {
  int32 revision = 1;
  repeated Fault faults = 2;
}
```

Run `make contract`. In `src/kb/client.py`, after `Append`, add:

```python

    def Delete(self, request, timeout=None):
        return self._call("Delete", request, kb_pb2.DeleteResponse)
```

Run Step 1's command. Expected: `3 failed`, each `AttributeError: 'NoneType' object has no attribute 'set_code'`.

- [ ] **Step 4: The code**

In `src/kb/store.py`, just above `    def holds(self, artifact_id: ArtifactId) -> bool:` in `Store`, add:

```python
    def remove(self, artifact_id: ArtifactId) -> Path:
        """Take an artifact's file out, and return where it was."""
        path = self.path(artifact_id)
        path.unlink()
        return path

```

In the same file, replace `Draft`'s docstring, `__init__`, `put` and `holds` with:

```python
class Draft:
    """The store as a set of changes would leave it: artifacts put here stand over the stored ones, artifacts removed
    here are no longer held, and nothing is written. Read like the store: holds, load, schema, ids."""

    def __init__(self, store: Store):
        self._store = store
        self._pending: dict[ArtifactId, dict] = {}
        self._removed: set[ArtifactId] = set()

    def put(self, artifact_id: ArtifactId, artifact: dict) -> None:
        self._removed.discard(artifact_id)
        self._pending[artifact_id] = artifact

    def remove(self, artifact_id: ArtifactId) -> None:
        self._removed.add(artifact_id)

    def holds(self, artifact_id: ArtifactId) -> bool:
        if artifact_id in self._removed:
            return False
        return artifact_id in self._pending or self._store.holds(artifact_id)

    def ids(self) -> list[ArtifactId]:
        """The name of every artifact the draft holds, in the order their paths would sort."""
        held = (set(self._store.ids()) | set(self._pending)) - self._removed
        return sorted(held, key=lambda artifact_id: f"{artifact_id}.yaml")
```

(`load` and `schema` stay as they are.)

In `src/kb/journal.py`, replace the first three lines of `write` (its signature's two lines and its docstring) with:

```python
def write(store_dir: Path, *, actor, op: str, artifact: str, path: str, revision: int,
          schema_version: int, written: Path | None, message: str, seq: int = 1, batch: str = "") -> Path:
    """Write one entry and return its file; its stem is the entry's id. A change made alone names itself as its batch.
    A removal wrote nothing, so its entry's fingerprint is empty."""
```

and change `        "digest": digest(written),` to `        "digest": digest(written) if written is not None else "",`.

In `src/kb/servicer.py`:

1. Just above `    def Apply(self, request, context):`, add:

```python
    def Delete(self, request, context):
        removal = kb_pb2.Removal(locator=request.locator)
        landed = self._land([kb_pb2.Operation(delete=removal)], request.actor, request.message)
        if landed.faults:
            return kb_pb2.DeleteResponse(faults=landed.faults)
        return kb_pb2.DeleteResponse(revision=landed.results[0].revision)

```

2. In `_land`, replace

```python
        for change in touched:
            try:
```

with

```python
        for change in touched:
            if change.op == "delete":
                texts.append((change, None))
                continue
            try:
```

and replace the writing loop (from `        for seq, (change, text) in enumerate(texts, start=1):` down to, not including, `        self._store.commit(written, actor.role, message)`) with:

```python
        for seq, (change, text) in enumerate(texts, start=1):
            if text is None:
                removed = self._store.load(change.artifact_id)
                revision, schema_version = removed["revision"] + 1, removed["schema_version"]
                path, saved = self._store.remove(change.artifact_id), None
            else:
                artifact = draft.load(change.artifact_id)
                revision, schema_version = artifact["revision"], artifact["schema_version"]
                path = saved = self._store.save(change.artifact_id, text)
            entry = journal.write(
                self._store.dir, actor=actor, op=change.op, artifact=str(change.artifact_id), path=change.path,
                revision=revision, schema_version=schema_version,
                written=saved, message=message, seq=seq, batch=batch,
            )
            batch = batch or entry.stem
            written += [path, entry]
            results.append(kb_pb2.Result(id=str(change.artifact_id), revision=revision, item=change.item))
```

3. In `_apply`, after the two lines that dispatch `append`, add:

```python
        if which == "delete":
            return self._delete(draft, operation.delete)
```

4. Just above `    def Read(self, request, context):`, add:

```python
    def _delete(self, draft: Draft, removal: kb_pb2.Removal) -> Change:
        """A whole artifact taken out of the draft, refused with one fault for each link that still points at it."""
        locator = values.locator(removal.locator)
        if not draft.holds(locator.id):
            raise values.Refused([_not_found(locator.id)])
        if locator.place:
            raise values.Refused([kb_pb2.Fault(
                artifact=str(locator.id), path="/".join(locator.place), rule="locator",
                message=f"a removal takes out a whole artifact; {'/'.join(locator.place)!r} is a place inside {str(locator.id)!r}",
            )])
        blocking = []
        for other_id in draft.ids():
            if other_id == locator.id:
                continue
            schema = draft.schema(other_id.kind)["schema"]
            for field, place, target in validation.links(draft.load(other_id), schema, draft):
                if _points_at(target, locator.id):
                    blocking.append(kb_pb2.Fault(
                        artifact=str(other_id), path=place, rule="on_delete",
                        message=f"{str(locator.id)!r} cannot be removed while {str(other_id)!r} points at it at {place!r}",
                    ))
        if blocking:
            raise values.Refused(blocking)
        draft.remove(locator.id)
        return Change("delete", locator.id)

```

(`git add` of a removed file that git tracks stages its removal, so `Store.commit` needs no change.)

- [ ] **Step 5: Run it green, and the suite**

```bash
.venv/bin/python -m pytest -q -m slice-41 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `3 passed, 115 deselected`; `19 failed, 99 passed`. The 19 are slices 43, 45, 46 and 51.

- [ ] **Step 6: Commit**

```bash
git add src/kb/contract/ src/kb/client.py src/kb/store.py src/kb/journal.py src/kb/servicer.py tests/calls.py tests/test_remove_an_artifact.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 41: remove an artifact, or be refused

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 7: Checkpoint**

Set slice 41's Status to `green`. Append at the very end of the Log:

```
- <date> slice 41 green. Someone can now: remove a tag nothing points at and find it gone, with the removal in the journal and the history like any other change; be refused removing a tag a decision points at, given every link in the way; and be refused removing a name the store lacks, with the name given back and nothing written.
  Surprised by: <nothing, or what>.
  Open questions:
  - QUESTION FOR THE SPEC: removing a type something is still of is not refused, since no link points at a type; every read of that kind, and Validate, then raise FileNotFoundError through the client. (Review Focus 1)
  - QUESTION FOR THE SPEC: a create and a removal of one artifact in one set raise CalledProcessError at git add, leaving the set's journal entries written and uncommitted. (Review Focus 2)
  - QUESTION FOR THE SPEC: Delete reads every artifact for links, so a store holding a file it cannot read makes it raise store.Unreadable through the client. (Review Focus 3)
  - QUESTION FOR THE SPEC: a removal's entry records one more than the last version and an empty fingerprint, since nothing was written; the response gives that version. A locator naming a place inside an artifact is refused with rule locator: removing a part is not built.
  - A removal is an operation of Apply too, through _land, as the spec's Apply row lists it; no scenario removes in a set.
  Next: the whole-batch review.
```

Commit the plan: `Slice 41 green`.

---

## After slice 41

Not a slice. Run the whole-batch review over the commits of Tasks 1 to 6, using `superpowers:requesting-code-review` with this plan and the spec as the brief. Every finding goes to `slicing-into-increments`, which places it by its unknown among the slices not yet begun. No finding is coded here.

The contract grows in this batch (three rpcs, an operation each for Append and Delete in `Apply`, and filters on Refs, Search and Journal), and batches 3 and 4's additions are still unreleased. The version stays `0.1.0`. Whether to bump it and tag a release is the user's call, as the 0.1 tag was, and the review should say whether anything in this batch stands in the way. The next slices in the slice plan are 43, 45, 46 and 51.
