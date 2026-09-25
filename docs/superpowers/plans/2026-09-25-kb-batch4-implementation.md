# kb Batch 4 Implementation Plan: slices 14, 21, 23, 25, 27 and 29

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Each task is one slice of `docs/superpowers/plans/2026-09-24-kb-slices.md`. Inside a task, follow `shopsystem-bdd:bdd-red-green` scenario by scenario. Its stop conditions, hand-back, and checkpoint apply, and they override any step here that conflicts with them.

**Goal:** The next six slices:
- Items keep their names when a client puts them in a different order, and a link into an item still lands.
- A client can read an artifact at every depth: one section, the whole of it, and with its links followed as far as asked.
- A change bumps the version and brings an artifact behind its type up to date, and a change to a name the store lacks is refused.
- Create gives a name the client never chose, and gives two parts with the same title names of their own.
- A type that does not match the type that describes types is refused.
- A client can list the artifacts of a kind, narrowed by a field, as stubs or as names.

**Architecture:** kb is the Python package `kb` in `/home/vscode/shopsystem-kb`. A protobuf contract (`kb.contract`) sits in front of `KbServicer`, which works over a `Store`. The store is one canonical YAML file per artifact under `<root>/kb/`, and that directory is itself a git repository. `kb.values` holds the boundary conversions. `kb.validation` checks content against a type. `KbServicer._land` is the one write path: it applies operations to a `store.Draft`, checks them there, and writes only when all of them pass. This plan:
- gives each item of a part collection a name from its title or, with no title, from its place. A Write keeps the name an item already carries, and a link may name a part after `#` (slice 14);
- gives `Read` a section level (slice 21);
- lists stale artifacts in `Validate`, and refuses a Write to a name the store lacks (slice 23);
- numbers a part's name when another item in its collection has it, by the rule that numbers artifacts (slice 25);
- adds the `List` rpc (slice 29).

Slice 27 needs no code.

**Provenance:** Every code block here was assembled in a scratch clone of this repository (`/tmp/batch4/kb`, cloned at `0f3eba7`) on 2026-09-25. It was run with this checkout's `.venv` and `PYTHONPATH=/tmp/batch4/kb/src`, and the tasks were applied in order. The red and green results, the suite counts, and the Review Focus reproductions below are what those runs gave. The plan was then replayed from its own text and code blocks on a fresh clone (`/tmp/batch4-replay`) by an agent that had not seen the scratch run. Every red and green matched, and the replay's `src/` and `tests/` were identical to the scratch run's. This repository was not touched except to write this plan.

**Tech Stack:** Python 3.11, setuptools (src layout), protobuf + grpcio + grpcio-tools (generated code is committed; `make contract` regenerates it), python-jsonschema 4.26 with `referencing`, ruamel.yaml 0.19 (YAML 1.2), git via subprocess, pytest 9 + pytest-bdd 8.

**Spec:** `docs/superpowers/specs/2026-09-23-kb-design.md`, in particular:
- "Artifact model": Fields (a reference into a part) and Parts;
- "Schema language": `ref` with `parts: bool`, and the metaschema;
- "The contract": the `Read` row (the section level), `Write`, `List`, `Validate` (stale artifacts listed), and "Resolution";
- "Write path", step 5: a write to a stale artifact.

The slice plan is `docs/superpowers/plans/2026-09-24-kb-slices.md`, slices 14, 21, 23, 25, 27 and 29, and the feature files are in `features/`. Each slice's scenarios carry `@slice-<n>`, so `.venv/bin/python -m pytest -q -m slice-21` runs one slice.

## Global Constraints

- Feature files are read-only for the implementer. Only `slicing-into-increments` edits a tag line, and only `formulating-features` edits a Given, When, or Then. Any other diff under `features/` is a stop condition.
- Code only what a scenario asserts (bdd-red-green). Where the scenarios are silent, the code is silent too, and the silence goes into the checkpoint entry as an open question. The decisions this plan makes are listed below, each tied to the spec line or scenario that asks for it.
- **Extend, never add beside.**
  - Content is converted by `values.content`, one function for Create, Write and Apply.
  - A link is converted by `values.target`, which is `values.locator` over the text either side of `#`; nothing parses a link a second way.
  - Links are found by `validation.references` and `validation.links`, and checked by `validation._lands`.
  - Stubs are made by `KbServicer._stub`, which List uses too. The not-found fault is made by `_not_found`, which Read, Refs and now Write share.
  - A clashing name gets its number from `_numbered`, which artifact names (`_unclaimed`) and part names (`_name_items`) share.
  - Every write goes through `_land`.
  - Test helpers live in `tests/calls.py`. A type or helper two feature files need moves there rather than being copied.
- Spec, parts: "Each item carries an `id` unique within its collection, first in key order, minted by kb and never supplied by the client: from the item's `title` when the item schema has one, otherwise from the item's position, with the same collision suffix as artifacts. An id is minted once and never recomputed: removing or reordering items does not rename the others. … On a `Write` of a collection, an item carrying an id is the existing item of that id, moved or changed in place; an item without one is new and is minted an id. An id that names no existing item is refused."
- Spec, fields: "A reference is a field type: a string `decision/adr-0007` or, into a part, `process/x#steps/draft`. The schema declares target types, cardinality, whether part paths are allowed, and the delete rule."
- Spec, contract: "`Read` | locator, level (`summary`, `section` with title, `whole`), resolve depth"; "`List` | type, field filters, output form (`stubs` or `ids`) | matches"; "`Validate` | nothing | every violation as artifact, path, message; stale artifacts listed". `Write`, `Append`, and `Delete` of an id the store does not hold are refused with a fault naming the id, as `Read` is.
- Spec, write path: "a write to a stale artifact validates against the current version; passing, it clears the staleness; failing, it is refused like any invalid write".
- Errors are a typed list of `{ artifact, path, rule, message }`. A response that carries faults is a refusal, and nothing was written.
- kb is exercised through its in-process transport.
- Each checkout has its own virtualenv. `make test` runs the suite (`.venv/bin/python -m pytest -q`). `make contract` regenerates `kb_pb2.py`, `kb_pb2.pyi` and `kb_pb2_grpc.py` from `kb.proto`, and every regenerated file is committed with the `.proto`.
- The contract's version stays `0.1` in the `.proto` header and in `CONTRACT_VERSION`, and `pyproject.toml` stays `0.1.0`, though this batch adds a rpc and fields. Bumping the version and tagging are the user's call and are not part of this plan (see "After slice 29").
- Work on `main` in `/home/vscode/shopsystem-kb`. A worktree needs its own `.venv` first (`make dev`).
- shop-knowledge pins kb at `v0.1.0`. Nothing here touches or runs its suite.
- Commits: `git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit`, the message ending with the Co-Authored-By line of the model that made the commit, e.g. `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- The suite prints pytest-bdd `PytestRemovedIn10Warning`s. That is the baseline, not a fault. The summary lines quoted as Expected leave out the `, N warnings in Xs` that pytest adds.
- Baseline before Task 1: `make test` → `61 failed, 57 passed`. After Tasks 1 to 6 the suite reads `60/58`, `54/64`, `48/70`, `44/74`, `43/75` and `40/78` (failed/passed).

## Decisions this plan makes (the spec left them open or silent)

1. **An item's name.**
   - `_name_items(schema, content, keep_named)` in `servicer.py` names every item of every part collection. An item is named from its title when it carries one, otherwise from its place in the collection, counted from 1 (`"1"`, `"2"`, …). The spec says only "from the item's position", so counting from 1 is this plan's choice. It is a text name, like any other, and is written `'1'` on disk.
   - Create names every item, as it did before (`keep_named=False`).
   - A Write keeps the name an item already carries and names only the items that carry none (`keep_named=True`). This is the spec's Write of a collection. It settles slice 14's unknown, on the reading slice 14 was cut on (the 2026-09-23 question): the client writes the collection back carrying the names kb gave.
   - A node write aimed at a part (`options/go-monthly`) now keeps that part's name: `_placed` puts the name back on the node it puts in place. Batch 3's review found the same write raising `KeyError: 'id'`. With `_name_items` in place and no fix in `_placed`, it would instead rename the part. The spec says an id "is minted once and never recomputed".
   - From Task 4 on, a name that another item of the collection already has gets `-2`, `-3` and so on, through `_numbered`, the loop `_unclaimed` used for artifacts. On a write, the names items already carry are taken first.
   - An item carrying a name that no existing item has is not refused: the scenarios are silent (Review Focus 3).
2. **A link into a part.** A link is `<kind>/<name>` or `<kind>/<name>#<collection>/<item>[/<collection>/<item>…]`. `values.target(text)` converts it by splitting at `#` and passing both halves to `values.locator`, so the place is checked like any locator's. `validation._lands` now takes the field's whole `ref` dict. A link with a place lands only when:
   - the ref says `parts: true`;
   - the artifact is of a kind the ref targets, and the store holds it;
   - the place names, pair by pair, a collection and an item by its name.

   Slice 14's "anything pointing at one of them still lands" is observed through this rule and through `Validate`. The link that slice 14's finding carries, `checklist/closing-checks#checks/2`, could not be written before.
3. **The section read.** `ReadRequest.Level` gains `SECTION = 2`, and `ReadRequest` gains `string section = 4`, the title asked for. The answer is:
   - the first section with that title, looking at each section before the ones inside it;
   - with the artifact's identity fields, and `content` holding only that section;
   - with no references, parts or inbound counts.

   A title the artifact holds no section under is refused with rule `not-found`: `'<id>' holds no section titled '<title>'`. No scenario pins that refusal, so Task 2 logs it.
4. **Types two feature files share.** `TAG_TYPE` and `tagged_decision_type()` move from `tests/test_follow_the_links.py` to `tests/calls.py`, and read-an-artifact's Background defines the tagged decision type. `PROCESS_TYPE`, a process with a `steps` collection whose items may `branches` to other steps by name, is added to `calls.py` in Task 1 and used again in Task 2. The helper `everything_under` moves from `tests/test_create_an_artifact.py` to `calls.py` in Task 3.
5. **Stale.** `ValidateResponse` gains `repeated Stale stale = 3`, where `Stale` is `{ artifact, schema_version, current }`. An artifact is stale when its `schema_version` is below its type's `version`. Validate still checks it against the current version, as before. A step makes a decision stale by writing the decision type at version 2.
6. **Write of a name the store lacks.** `_replace` refuses it with `_not_found`, before reading the content, where it used to raise `FileNotFoundError` (batch 2's question, pinned by slice 23).
7. **List.**
   - `rpc List(ListRequest) returns (ListResponse)`.
   - `ListRequest { type; map<string, string> fields; Form form }`, where `Form` is `STUBS = 0` or `IDS = 1`.
   - `ListResponse { repeated Stub stubs; repeated string ids; repeated Fault faults }`.
   - A field filter matches when the artifact has the field and `content.text` of its value equals the text given. So `true` matches `"true"` and `12` matches `"12"`, the way a title is compared.
   - Matches come in path order. A stub's `field` is empty.
   - The kind is checked by `values.kind`, and one that is not plain is refused with that fault.
8. **A malformed type.** No code. `schema/schema`'s own `schema` field is `$ref: https://json-schema.org/draft/2020-12/schema`, and jsonschema resolves it, so a type whose `schema` says `type: label` is refused at `schema/type` with rule `anyOf`. The scratch run showed it green on its step definitions alone.

## Review Focus

In this project, tests are scenarios, and the feature files are the human gate, so no unit tests are added. Instead, each line below goes into the owning task's checkpoint entry as a `QUESTION FOR THE SPEC`, with the reproduction given here. Each was reproduced in scratch after all six tasks, over a store holding slice 14's checklist and finding.

1. **A link into a part breaks every read that meets it.** Reproduction: after Task 1, `read(client, "finding/the-till-was-short")` (a summary), `refs(client, "finding/the-till-was-short", 1)` and `read(client, "finding/the-till-was-short", whole=True, depth=1)` each raise `values.Refused` through the client. The stub and resolution code converts the link with `values.artifact_id`, which refuses the `#`. The spec says a reference may point into a part and that nothing raises, but it does not say what a stub or a filled-in link of a part is. Task 1 logs it.
2. **A write that takes one item out and adds another can give the new item the old one's name.** Reproduction: after Task 1, write the checklist's `checks` as `[{"id": "3", "says": "Door locked"}, {"says": "Alarm set"}]`. The new item is named `"2"` from its place, and the finding's link `checklist/closing-checks#checks/2` now lands on "Alarm set". `Validate` reports nothing. The removed item was pointed at, and nothing refused its removal either. Task 1 logs it.
3. **An item carrying a name no item has is kept.** Reproduction: after Task 1, write the checklist's `checks` with a first item `{"id": "my-own", "says": "Lights off"}`. It answers no fault, and the item is stored as `my-own`. The spec says such an id is refused. Task 1 logs it.
4. **List breaks on a file it cannot read.** Reproduction: after Task 6, write `title: [` into a stored decision's file, and `listing(client, "decision")` raises `store.Unreadable` through the client. Read answers the same file with a fault. Task 6 logs it.
5. **List of a kind the store holds no type for answers nothing.** Reproduction: after Task 6, `listing(client, "invoice")` answers no stubs and no fault. Create refuses the same kind as its own fault. Task 6 logs it.

---

### Task 1: Slice 14, items keep their names when put in a different order

**Slice plan entry:** Slice 14, capability. Unknown: how does an item keep the name kb minted for it across a write that moves it, when the client never chooses names and an item named by its place no longer sits there? Scenario:

1. kb / add-an-item-to-a-collection / Putting items in a different order does not rename them

**Files:**
- Modify: `src/kb/values.py` (new `target`)
- Modify: `src/kb/validation.py` (`validate` passes the whole ref; `_lands` takes it; new `_holds_part`)
- Modify: `src/kb/servicer.py` (`_create` and `_replace` name items through `_name_items`; `_placed` keeps a part's name; new module function `_name_items`)
- Modify: `tests/calls.py` (new `PROCESS_TYPE`)
- Rewrite: `tests/test_add_an_item_to_a_collection.py`
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `tests/calls.py`: `CLIENT`, `create`, `define`, `read(client, id, whole=True)`, `write(client, id, content, message=…)`. The `root` fixture. `values.locator(kb_pb2.Locator) -> Locator`, `values.slug`.
- Produces:
  - `values.target(text: str) -> values.Locator`.
  - `validation._lands(target: str, ref: dict, corpus) -> bool` and `validation._holds_part(node: dict, place: tuple) -> bool`.
  - `servicer._name_items(schema: dict, content: dict, keep_named: bool) -> None`, which names items in place. Task 4 changes its body.
  - `calls.PROCESS_TYPE`, which Task 2 uses.

- [ ] **Step 1: Run it red**

```bash
cd /home/vscode/shopsystem-kb && .venv/bin/python -m pytest -q -m slice-14 2>&1 | grep -E "^E |passed|failed" | tail -2
```

Expected: `1 failed`, a `StepDefinitionNotFoundError` for `Given "a store holding a process with two steps and a shared step other processes use"`.

- [ ] **Step 2: The steps**

Append to `tests/calls.py`:

```python


PROCESS_TYPE = {
    "title": "Process",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {"title": {"type": "string"}},
        "required": ["title"],
        "parts": {
            "steps": {
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "body": {"type": "string"},
                        "branches": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["title"],
                }
            }
        },
    },
}
```

Replace the whole of `tests/test_add_an_item_to_a_collection.py` with:

```python
from pytest_bdd import given, scenarios, then, when

from calls import CLIENT, PROCESS_TYPE, create, define, read, write
from kb import client as kb_client
from kb.content import loads
from kb.contract import kb_pb2

scenarios("add-an-item-to-a-collection.feature")

STEP_TYPE = {
    "title": "Step",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {"title": {"type": "string"}, "body": {"type": "string"}},
        "required": ["title"],
    },
}
CHECKLIST_TYPE = {
    "title": "Checklist",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {"title": {"type": "string"}},
        "required": ["title"],
        "parts": {
            "checks": {
                "items": {"type": "object", "properties": {"says": {"type": "string"}}, "required": ["says"]},
            }
        },
    },
}
FINDING_TYPE = {
    "title": "Finding",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "check": {
                "type": "string",
                "ref": {"targets": ["checklist"], "cardinality": "one", "parts": True, "on_delete": "refuse"},
            },
        },
        "required": ["title"],
    },
}
CHECKLIST = "checklist/closing-checks"
FINDING = "finding/the-till-was-short"
CHECKS = [{"says": "Lights off"}, {"says": "Till counted"}, {"says": "Door locked"}]


@given("a store holding a process with two steps and a shared step other processes use", target_fixture="client")
def _store_with_a_process(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, STEP_TYPE)
    define(client, PROCESS_TYPE)
    create(client, "step", {"title": "Count the till", "body": "Count every note and coin.\n"})
    create(client, "process", {"title": "Open the shop", "steps": [
        {"title": "Unlock the door", "body": "Front door first."},
        {"title": "Turn on the lights", "body": "Shop floor, then the stockroom."},
    ]})
    return client


@given(
    "an artifact holding a collection whose items carry no title of their own, each named by its place when it was added",
    target_fixture="named",
)
def _checklist_named_by_place(client):
    define(client, CHECKLIST_TYPE)
    define(client, FINDING_TYPE)
    create(client, "checklist", {"title": "Closing checks", "checks": CHECKS})
    create(client, "finding", {"title": "The till was short", "check": f"{CHECKLIST}#checks/2"})
    checks = loads(read(client, CHECKLIST, whole=True).content)["checks"]
    assert checks == [{"id": str(place), **check} for place, check in enumerate(CHECKS, start=1)]
    return {check["id"]: check for check in checks}


@when("the client puts the items of that collection in a different order, saying which role and why", target_fixture="reordered")
def _reorder_the_checks(client, named):
    reordered = [named["3"], named["1"], named["2"]]
    response = write(client, CHECKLIST, {"checks": reordered}, message="Lock up before the lights")
    assert not response.faults, response.faults
    return loads(read(client, CHECKLIST, whole=True).content)["checks"]


@then("every item keeps the name it was given when it was added")
def _names_kept(named, reordered):
    assert [check["id"] for check in reordered] == ["3", "1", "2"]
    assert all(check == named[check["id"]] for check in reordered)


@then("anything pointing at one of them still lands on the same item")
def _link_still_lands(client, named, reordered):
    assert loads(read(client, FINDING, whole=True).content)["check"] == f"{CHECKLIST}#checks/2"
    assert next(check for check in reordered if check["id"] == "2") == {"id": "2", "says": "Till counted"}
    assert not client.Validate(kb_pb2.ValidateRequest()).violations
```

Run Step 1's command again with `tail -3`. Expected: `1 failed`, ending `E               KeyError: 'title'` at `src/kb/servicer.py`. `_create` names every item from a title, and a check carries none.

- [ ] **Step 3: The code**

In `src/kb/values.py`, just above `def named(kind: Kind, title: str) -> ArtifactId:`, add:

```python
def target(text: str) -> Locator:
    """A link as a field holds it: a name, or a name and, after `#`, a place inside that artifact. Checked as a
    locator is."""
    name, _, place = text.partition("#")
    return locator(kb_pb2.Locator(id=name, path=place))


```

In `src/kb/validation.py`, in `validate`, change `        if not _lands(target, allowed[field]["targets"], corpus):` to `        if not _lands(target, allowed[field], corpus):`, and replace `_lands` with:

```python
def _lands(target: str, ref: dict, corpus) -> bool:
    """Whether a link lands: on an artifact of a kind the field allows that the corpus holds, and, when it names a
    place after `#` and the field allows parts, on a part that artifact holds."""
    try:
        link = values.target(target)
    except values.Refused:
        return False
    if link.place and not ref.get("parts"):
        return False
    if link.id.kind.name not in ref["targets"] or not corpus.holds(link.id):
        return False
    return not link.place or _holds_part(corpus.load(link.id), link.place)


def _holds_part(node: dict, place: tuple) -> bool:
    """Whether a place, pairs of a collection and the name of an item in it, names a part the node holds."""
    if len(place) % 2:
        return False
    for collection, name in zip(place[::2], place[1::2]):
        items = node.get(collection)
        if not isinstance(items, list):
            return False
        node = next((item for item in items if isinstance(item, dict) and item.get("id") == name), None)
        if node is None:
            return False
    return True
```

In `src/kb/servicer.py`, in `_create`, replace

```python
        for collection in schema["schema"].get("parts", {}):
            for item in content.get(collection, []):
                item["id"] = values.slug(item["title"])
```

with

```python
        _name_items(schema["schema"], content, keep_named=False)
```

In `_replace`, add the line `        _name_items(schema["schema"], content, keep_named=True)` after the two lines `if faults:` / `raise values.Refused(faults)` that follow its `validation.validate` call, so that this part of the method reads:

```python
        faults = validation.validate(str(locator.id), {"title": current["title"], **content}, schema["schema"], draft)
        if faults:
            raise values.Refused(faults)
        _name_items(schema["schema"], content, keep_named=True)
        artifact = {
```

In `_placed`, change `            items[index] = node` to `            items[index] = node if collection == "sections" else {"id": name, **node}`. Just above `def _not_found(artifact_id: ArtifactId) -> kb_pb2.Fault:`, add:

```python
def _name_items(schema: dict, content: dict, keep_named: bool) -> None:
    """Every item of every part collection given its name: from its title when it carries one, otherwise from its
    place in the collection, counted from 1. On a write an item already carrying a name is the item of that name,
    moved or changed where it stands, and keeps it; a name is minted once and never worked out again."""
    for collection in schema.get("parts", {}):
        for place, item in enumerate(content.get(collection, []), start=1):
            if keep_named and "id" in item:
                continue
            item["id"] = values.slug(item["title"]) if "title" in item else str(place)


```

- [ ] **Step 4: Run it green, and the suite**

```bash
.venv/bin/python -m pytest -q -m slice-14 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `1 passed, 117 deselected`; `60 failed, 58 passed`.

- [ ] **Step 5: Commit**

```bash
git add src/kb/values.py src/kb/validation.py src/kb/servicer.py tests/calls.py tests/test_add_an_item_to_a_collection.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 14: items keep their names when put in a different order

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 6: Checkpoint**

In `docs/superpowers/plans/2026-09-24-kb-slices.md`, set slice 14's Status to `green`. Append at the very end of the Log, and check with `tail` that it is last:

```
- <date> slice 14 green. Someone can now: put the items of a collection in a different order, each item carrying the name kb gave it, and find every item under its name and a link to one still landing on it.
  Assumption "a Write keeps the name an item carries and names only those that carry none, from the title or else the place counted from 1": <held or not>. Evidence: <the ids after the reorder, ['3', '1', '2'], each with its own text; the finding's link checklist/closing-checks#checks/2 unchanged and Validate reporting nothing>.
  Surprised by: <nothing, or what>.
  Open questions:
  - ANSWERED: a node write aimed at a part (options/go-monthly) keeps that part's name instead of raising KeyError 'id' (slice 13's question, batch 3's review).
  - QUESTION FOR THE SPEC: a link into a part makes a summary Read, a whole Read following links, and Refs of the artifact holding it raise values.Refused through the client. What is the stub, or the filled-in link, of a part? (Review Focus 1)
  - QUESTION FOR THE SPEC: a write that takes an item out and adds another can give the new item the removed one's name, so a link to the removed item lands on the new one with no fault; nor is the removal of an item something points at refused. (Review Focus 2)
  - QUESTION FOR THE SPEC: an item carrying a name no item has is kept as a name the client chose; the spec refuses it. (Review Focus 3)
  - Items named by their place are counted from 1, a choice the spec leaves open ("from the item's position").
  Next: slice 21.
```

Commit the plan: `Slice 14 green`.

---

### Task 2: Slice 21, read an artifact at every depth

**Slice plan entry:** Slice 21, capability. Unknown: none. Scenarios:

1. kb / read-an-artifact / The client reads one section by its title
2. kb / read-an-artifact / The client reads the whole artifact
3. kb / read-an-artifact / Without being asked to follow them, links come back as names
4. kb / read-an-artifact / The client reads the whole artifact with what it points at filled in
5. kb / read-an-artifact / The client reads an artifact following its links two steps
6. kb / read-an-artifact / The branches inside a process are not followed

Scenarios 2 to 6 go green on their step definitions alone, on the whole read slice 12 built. Each is red first for want of a step, so bdd-red-green's first stop condition is not met. Only scenario 1 needs code.

**Files:**
- Modify: `src/kb/contract/kb.proto` (`ReadRequest`: `SECTION`, `section`), then `make contract`
- Modify: `src/kb/servicer.py` (`Read` dispatches the section level; new `_section`; new module function `_find_section`)
- Modify: `tests/calls.py` (`TAG_TYPE` and `tagged_decision_type` moved here; `read` takes `section`)
- Modify: `tests/test_follow_the_links.py` (imports the two from `calls`)
- Modify: `tests/test_read_an_artifact.py` (Background on the tagged decision type; eleven steps appended)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `calls.PROCESS_TYPE` (Task 1), `calls.create`, `define`, `write`, `read(client, id, whole=…, depth=…)`, and `test_read_an_artifact.py`'s `OLDER`, `DECISION`, `_start_with_a_linked_decision`. `KbServicer._whole` (slice 12).
- Produces:
  - `kb_pb2.ReadRequest.SECTION` and `ReadRequest.section`.
  - `calls.read(client, artifact_id, whole=False, depth=0, section="")`, `calls.TAG_TYPE` and `calls.tagged_decision_type()`.
  - `servicer._find_section(sections: list, title: str) -> dict | None`.

- [ ] **Step 1: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-21 2>&1 | grep -E "^E |passed|failed" | tail -7
```

Expected: `6 failed`, each a `StepDefinitionNotFoundError`, one per scenario:
- `When "the client reads the rationale of the decision"`;
- `When "the client reads the whole decision"`;
- `When "the client reads the whole decision without asking for its links to be followed"`;
- `When "the client reads the whole decision following its links one step"`;
- `Given "the older decision is tagged "pricing""`;
- `Given "a store holding a process whose steps branch to other steps of the same process"`.

- [ ] **Step 2: The contract**

In `src/kb/contract/kb.proto`, replace the comment above `ReadRequest`, and `ReadRequest` itself, with:

```proto
// A summary by default. A whole read gives the artifact's content with
// each link followed as many steps as depth says, the target in place of
// its name; a target already filled in on the way is left as its name.
// A section read gives the section with the title named, and nothing else.
message ReadRequest {
  enum Level {
    SUMMARY = 0;
    WHOLE = 1;
    SECTION = 2;
  }
  Locator locator = 1;
  Level level = 2;
  int32 depth = 3;
  string section = 4;
}
```

Run `make contract`. `git status --short src/kb/contract` shows `kb.proto`, `kb_pb2.py` and `kb_pb2.pyi` changed. `kb_pb2_grpc.py` does not change, since no rpc changed.

- [ ] **Step 3: The helpers and the steps**

In `tests/calls.py`:
- add `import copy` and a blank line after the module docstring;
- just above `def request(`, add the block below;
- replace `read` with the one below.

The block for above `def request(`:

```python
TAG_TYPE = {
    "title": "Tag",
    "version": 1,
    "schema": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]},
}


def tagged_decision_type():
    """The decision type, whose artifacts may also carry tags."""
    decision_type = copy.deepcopy(DECISION_TYPE)
    decision_type["schema"]["properties"]["tags"] = {
        "type": "array",
        "items": {"type": "string"},
        "ref": {"targets": ["tag"], "cardinality": "many", "parts": False, "on_delete": "refuse"},
    }
    return decision_type


```

The new `read`:

```python
def read(client, artifact_id, whole=False, depth=0, section=""):
    """A summary read, a whole read following the links as many steps as depth says, or a read of the section
    with the title given."""
    level = kb_pb2.ReadRequest.SUMMARY
    if whole:
        level = kb_pb2.ReadRequest.WHOLE
    if section:
        level = kb_pb2.ReadRequest.SECTION
    return client.Read(kb_pb2.ReadRequest(
        locator=kb_pb2.Locator(id=artifact_id), level=level, depth=depth, section=section,
    ))
```

In `tests/test_follow_the_links.py`:
- delete `import copy` and the blank line after it;
- change the `calls` import to `from calls import CLIENT, TAG_TYPE, WORK_ITEM_TYPE, create, define, refs, tagged_decision_type, write`;
- delete the module's own `TAG_TYPE` and `_tagged_decision_type`, leaving two blank lines between `OLDER_SECTIONS` and `@given("a store where a decision supersedes an older decision", …)`;
- change `define(client, _tagged_decision_type())` to `define(client, tagged_decision_type())`.

In `tests/test_read_an_artifact.py`, change the imports

```python
from calls import CLIENT, DECISION_TYPE, WORK_ITEM_TYPE, create, define, read, write
from kb import client as kb_client
```

to

```python
from calls import CLIENT, PROCESS_TYPE, TAG_TYPE, WORK_ITEM_TYPE, create, define, read, tagged_decision_type, write
from kb import canonical, client as kb_client
```

After `DECISION = "decision/price-reviews-happen-weekly"`, add:

```python
PROCESS = "process/open-the-shop"
OLDER_SECTIONS = [
    {"title": "Purpose", "body": "Keep prices current.\n"},
    {"title": "Rationale", "body": "Monthly was enough once.\n"},
]
```

In `_start_with_a_linked_decision`, change `    define(client, DECISION_TYPE)` to `    define(client, tagged_decision_type())`, and replace the older decision's create

```python
    create(client, "decision", {
        "title": "Prices are reviewed monthly",
        "sections": [
            {"title": "Purpose", "body": "Keep prices current.\n"},
            {"title": "Rationale", "body": "Monthly was enough once.\n"},
        ],
    })
```

with

```python
    create(client, "decision", {"title": "Prices are reviewed monthly", "sections": OLDER_SECTIONS})
```

Append to the file:

```python


@when("the client reads the rationale of the decision", target_fixture="shown")
def _read_the_rationale(client):
    return read(client, DECISION, section="Rationale")


@then("the client is given that section and nothing else")
def _that_section_alone(shown):
    assert not shown.faults, shown.faults
    assert loads(shown.content) == {"title": "Rationale", "body": "Costs move weekly.\n"}
    assert not shown.references and not shown.parts and not shown.inbound


@when("the client reads the whole decision", target_fixture="whole")
@when("the client reads the whole decision without asking for its links to be followed", target_fixture="whole")
def _read_the_whole_decision(client):
    response = read(client, DECISION, whole=True)
    assert not response.faults, response.faults
    return response


@then("the client is given every field, every section and every part, in the order the type declares")
def _everything_in_declared_order(whole):
    assert (whole.id, whole.type, whole.schema_version, whole.revision, whole.title) == (
        DECISION, "decision", 1, 1, "Price reviews happen weekly",
    )
    content = loads(whole.content)
    assert list(content) == ["supersedes", "sections", "options"]
    assert [section["title"] for section in content["sections"]] == ["Purpose", "Rationale"]
    assert [list(option) for option in content["options"]] == [["id", "title", "body"]] * 2
    assert [option["id"] for option in content["options"]] == ["keep-weekly", "go-monthly"]


@then("the older decision is given as the name it is known by, and nothing more")
def _older_as_a_name(whole):
    assert loads(whole.content)["supersedes"] == OLDER


@when(
    parsers.re(r"the client reads the whole (?P<kind>decision|process) following its links (?P<steps>one step|two steps)"),
    target_fixture="whole",
)
def _read_the_whole_following(client, kind, steps):
    response = read(client, DECISION if kind == "decision" else PROCESS, whole=True, depth={"one step": 1, "two steps": 2}[steps])
    assert not response.faults, response.faults
    return response


@then("the older decision is given in place of the link, as the store holds it now")
def _older_as_stored(root, whole):
    assert loads(whole.content)["supersedes"] == canonical.load((root / "kb" / f"{OLDER}.yaml").read_text())


@then("what the older decision itself points at is given as names")
def _older_links_as_names(whole):
    older = loads(whole.content)["supersedes"]
    assert not any(isinstance(value, dict) for value in older.values())
    assert all(isinstance(target, str) for target in older.get("tags", []))


@given(parsers.parse('the older decision is tagged "{tag}"'))
def _older_decision_tagged(client, tag):
    define(client, TAG_TYPE)
    tagged = create(client, "tag", {"title": tag})
    changed = write(client, OLDER, {"tags": [tagged.id], "sections": OLDER_SECTIONS}, message="Tag it")
    assert not changed.faults, changed.faults


@then("the older decision is given in place of the link")
def _older_filled_in(whole):
    older = loads(whole.content)["supersedes"]
    assert (older["id"], older["title"], older["sections"]) == (OLDER, "Prices are reviewed monthly", OLDER_SECTIONS)


@then("the tag is given in place of the link inside the older decision")
def _tag_filled_in(whole):
    assert loads(whole.content)["supersedes"]["tags"] == [
        {"id": "tag/pricing", "type": "tag", "schema_version": 1, "revision": 1, "title": "pricing"},
    ]


@given("a store holding a process whose steps branch to other steps of the same process")
def _process_whose_steps_branch(client):
    define(client, PROCESS_TYPE)
    create(client, "process", {"title": "Open the shop", "steps": [
        {"title": "Check the till", "body": "Is the float there?", "branches": ["count-the-float", "call-the-manager"]},
        {"title": "Count the float", "body": "Count it into the till."},
        {"title": "Call the manager", "body": "The float is missing."},
    ]})


@then("the branches are given as written, naming the steps of that process")
def _branches_as_written(whole):
    steps = loads(whole.content)["steps"]
    assert steps[0]["branches"] == ["count-the-float", "call-the-manager"]
    assert set(steps[0]["branches"]) <= {step["id"] for step in steps}
```

Run Step 1's command again with `tail -8`. Expected: `1 failed, 5 passed`. The failure is the section scenario, `AssertionError: assert {'supersedes'...ewed-monthly'} == {'title': 'Ra...ve weekly.\n'}`: a section read is answered as a summary.

- [ ] **Step 4: The code**

In `src/kb/servicer.py`, in `Read`, change

```python
            if request.level == kb_pb2.ReadRequest.WHOLE:
                return self._whole(locator, request.depth)
            return self._summary(locator)
```

to

```python
            if request.level == kb_pb2.ReadRequest.WHOLE:
                return self._whole(locator, request.depth)
            if request.level == kb_pb2.ReadRequest.SECTION:
                return self._section(locator, request.section)
            return self._summary(locator)
```

Just above `    def _resolved(self, artifact_id: ArtifactId, depth: int, on_path: set) -> dict:`, add:

```python
    def _section(self, locator, title: str):
        """The first section with that title, at any depth, in the order the artifact holds them, and nothing else."""
        artifact = self._store.load(locator.id)
        found = _find_section(artifact.get("sections", []), title)
        if found is None:
            return kb_pb2.ReadResponse(faults=[kb_pb2.Fault(
                artifact=str(locator.id), path="sections", rule="not-found",
                message=f"{str(locator.id)!r} holds no section titled {title!r}",
            )])
        return kb_pb2.ReadResponse(
            id=artifact["id"], type=artifact["type"],
            schema_version=artifact["schema_version"], revision=artifact["revision"],
            title=artifact["title"], content=dumps(found),
        )

```

Just above `def _node_name(collection: str, item: dict) -> str:`, add:

```python
def _find_section(sections: list, title: str) -> dict | None:
    """The first section titled so, looking at each section before the sections inside it."""
    for section in sections:
        if section["title"] == title:
            return section
        found = _find_section(section.get("sections", []), title)
        if found is not None:
            return found
    return None


```

- [ ] **Step 5: Run it green, slices 11 and 12 (whose steps and types moved), and the suite**

```bash
.venv/bin/python -m pytest -q -m "slice-21 or slice-11 or slice-12" 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `8 passed, 110 deselected`; `54 failed, 64 passed`.

- [ ] **Step 6: Commit**

```bash
git add src/kb/contract/ src/kb/servicer.py tests/calls.py tests/test_follow_the_links.py tests/test_read_an_artifact.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 21: read an artifact at every depth, following its links as far as asked

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 7: Checkpoint**

Set slice 21's Status to `green`. Append at the very end of the Log:

```
- <date> slice 21 green. Someone can now: read one section of a decision by its title and get that section alone; read the decision whole, in the order its type declares, its links as names; follow its links one step or two and get what they point at in place; and read a process whose steps branch without the branches being followed.
  Surprised by: <nothing, or what>. Five of the six scenarios went green on their step definitions alone, on slice 12's whole read, each red first for want of a step; only the section read needed code.
  Open questions:
  - QUESTION FOR THE SPEC: a section read of a title the artifact holds no section under is refused with rule not-found, "'<id>' holds no section titled '<title>'"; when two sections share a title, the first, looking at each section before those inside it, is given. No scenario pins either.
  - QUESTION FOR THE SPEC: "what the older decision itself points at is given as names" cannot fail against its Background, whose older decision points at nothing; the two-step scenario is what shows depth is honoured.
  Next: slice 23.
```

Commit the plan: `Slice 21 green`.

---

### Task 3: Slice 23, change an artifact, behind its type or not, and refuse what cannot be changed

**Slice plan entry:** Slice 23, capability. Unknown: none. Scenarios:

1. kb / change-an-artifact / The client changes an artifact
2. kb / change-an-artifact / Changing an artifact that is behind its type brings it up to date
3. kb / change-an-artifact / Changing an artifact that is behind its type with content the current version will not have is refused
4. kb / change-an-artifact / A change whose content settles what only the store settles is refused
5. kb / change-an-artifact / Changing something the store does not hold is refused
6. kb / change-an-artifact / A change aimed at a name that is not a plain name writes nothing

Scenarios 1, 4 and 6 go green on their step definitions alone, each red first for want of a step. Scenarios 2 and 3 need Validate to list what is stale. Scenario 5 needs the not-found refusal on Write.

**Files:**
- Modify: `src/kb/contract/kb.proto` (`ValidateResponse.stale`, new `Stale`), then `make contract`
- Modify: `src/kb/servicer.py` (`_replace` refuses a name the store lacks; `Validate` lists stale artifacts)
- Modify: `tests/calls.py` (`everything_under` moved here)
- Modify: `tests/test_create_an_artifact.py` (uses `calls.everything_under`)
- Modify: `tests/test_change_an_artifact.py` (fifteen steps appended)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `calls.write`, `read`, `DECISION_TYPE`. `test_change_an_artifact.py`'s `DECISION`, `SECTIONS`, its Background, and slice 8's Then `reading the decision gives what it held before, at the version it held before`, which reads `attempt["response"]` and `attempt["before"]`. `servicer._not_found`.
- Produces:
  - `kb_pb2.Stale(artifact, schema_version, current)` and `ValidateResponse.stale`.
  - `calls.everything_under(directory) -> dict[Path, bytes]`.

- [ ] **Step 1: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-23 2>&1 | grep -E "^E |passed|failed" | tail -7
```

Expected: `6 failed`, each a `StepDefinitionNotFoundError`:
- `When "the client replaces the decision, saying which role and why"`;
- `Given "a decision last checked against an older version of the decision type, which still fits the current version"`;
- `Given "a decision last checked against an older version of the decision type"`;
- `When "the client replaces the decision with content carrying a version of its own, saying which role and why"`;
- `When "the client replaces an artifact by a name the store holds nothing under, saying which role and why"`;
- `When "the client replaces an artifact named "../../elsewhere", saying which role and why"`.

- [ ] **Step 2: The steps**

Append to `tests/calls.py`:

```python


def everything_under(directory):
    """Every file below a directory, with its bytes, so a step can tell whether anything was written."""
    return {path: path.read_bytes() for path in sorted(directory.rglob("*")) if path.is_file()}
```

In `tests/test_create_an_artifact.py`:
- change the `calls` import to `from calls import CLIENT, DECISION_TYPE, create, define, everything_under, read, request`;
- delete the module's own `_everything_under` and the two blank lines after it;
- change each of its four calls `_everything_under(` to `everything_under(`.

In `tests/test_change_an_artifact.py`, change the head

```python
from pytest_bdd import given, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, create, define, read, write
from kb import client as kb_client
```

to

```python
import copy

from pytest_bdd import given, parsers, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, create, define, everything_under, read, write
from kb import canonical, client as kb_client
```

and append:

```python


@when("the client replaces the decision, saying which role and why", target_fixture="changed")
def _replace_the_decision(client):
    response = write(client, DECISION, {"sections": [
        SECTIONS[0], {"title": "Rationale", "body": "Suppliers change their prices every week.\n"},
    ]}, message="Say why weekly")
    assert not response.faults, response.faults
    return response


@then("the version goes up by one")
def _version_up_by_one(client, changed):
    assert changed.revision == 2
    assert read(client, DECISION).revision == 2


@then("the artifact records the current version of its type")
def _records_the_current_version(root, client):
    current = canonical.load((root / "kb" / "schema" / "decision.yaml").read_text())["version"]
    assert read(client, DECISION).schema_version == current


def _stale(client):
    """The names the store's check lists as behind their type."""
    return [stale.artifact for stale in client.Validate(kb_pb2.ValidateRequest()).stale]


def _decision_type_at_version_2(client, schema):
    """The decision type changed to its second version, so the decision, checked against the first, is behind it."""
    changed = write(client, "schema/decision", {"version": 2, "schema": schema}, message="Decision type, version 2")
    assert not changed.faults, changed.faults
    assert read(client, DECISION).schema_version == 1
    assert _stale(client) == [DECISION]


@given("a decision last checked against an older version of the decision type, which still fits the current version")
def _behind_a_type_it_still_fits(client):
    _decision_type_at_version_2(client, DECISION_TYPE["schema"])


@given("a decision last checked against an older version of the decision type")
def _behind_a_type_that_now_wants_an_owner(client):
    schema = copy.deepcopy(DECISION_TYPE["schema"])
    schema["properties"]["owner"] = {"type": "string"}
    schema["required"] = ["title", "owner"]
    _decision_type_at_version_2(client, schema)


@when(
    "the client replaces the decision with content that fits the current version of its type, saying which role and why",
    target_fixture="changed",
)
def _replace_with_content_that_fits(client):
    response = write(client, DECISION, {"sections": SECTIONS}, message="Bring it up to date")
    assert not response.faults, response.faults
    return response


@then("the decision records the current version of its type")
def _records_version_2(client):
    assert read(client, DECISION).schema_version == 2


@then("it is no longer listed as behind its type")
def _no_longer_stale(client):
    assert DECISION not in _stale(client)


@when(
    "the client replaces the decision with content that does not fit the current version of its type, "
    "saying which role and why",
    target_fixture="attempt",
)
def _replace_with_content_that_does_not_fit(root, client):
    before = (root / "kb" / f"{DECISION}.yaml").read_bytes()
    return {"response": write(client, DECISION, {"sections": SECTIONS}, message="No owner"), "before": before}


@then(
    "the change is rejected because the content does not fit the current version of its type, "
    "like any change that does not fit"
)
def _rejected_by_the_current_version(attempt):
    refused = attempt["response"]
    assert refused.revision == 0
    assert [(fault.artifact, fault.path, fault.rule) for fault in refused.faults] == [(DECISION, "", "required")]
    assert "'owner' is a required property" in refused.faults[0].message


@then("it is still listed as behind its type")
def _still_stale(client):
    assert _stale(client) == [DECISION]


@when(
    "the client replaces the decision with content carrying a version of its own, saying which role and why",
    target_fixture="attempt",
)
def _replace_with_a_version_of_its_own(root, client):
    before = (root / "kb" / f"{DECISION}.yaml").read_bytes()
    response = write(client, DECISION, {"revision": 7, "sections": SECTIONS}, message="Set the version")
    return {"response": response, "before": before}


@then(
    "the change is rejected because content holds only what the type declares, "
    "and the thing it carried that only the store settles is named back"
)
def _rejected_for_a_version_inside(attempt):
    refused = attempt["response"]
    assert refused.revision == 0
    assert [(fault.artifact, fault.path, fault.rule) for fault in refused.faults] == [(DECISION, "revision", "identity")]
    assert "revision: 7" in refused.faults[0].message


@when(
    "the client replaces an artifact by a name the store holds nothing under, saying which role and why",
    target_fixture="attempt",
)
def _replace_a_name_the_store_lacks(root, client):
    before = everything_under(root / "kb")
    response = write(client, "decision/nothing-of-the-sort", {"sections": SECTIONS}, message="Change it")
    return {"response": response, "before": before, "after": everything_under(root / "kb")}


@then("the change is rejected because the store holds nothing by that name, and the name asked for is given back")
def _rejected_as_not_held(attempt):
    refused = attempt["response"]
    assert refused.revision == 0
    assert [(fault.artifact, fault.rule) for fault in refused.faults] == [("decision/nothing-of-the-sort", "not-found")]
    assert "decision/nothing-of-the-sort" in refused.faults[0].message


@then("nothing is written anywhere in the store")
def _nothing_written_in_the_store(attempt):
    assert attempt["after"] == attempt["before"]


@when(parsers.parse('the client replaces an artifact named "{name}", saying which role and why'), target_fixture="attempt")
def _replace_by_a_name(client, tmp_path, name):
    before = everything_under(tmp_path)
    response = write(client, name, {"sections": SECTIONS}, message="Change it")
    return {"response": response, "before": before, "after": everything_under(tmp_path)}


@then("the change is rejected because a name is a kind and a plain name of lower-case letters, digits and single hyphens")
def _rejected_as_not_a_plain_name(attempt):
    refused = attempt["response"]
    assert refused.revision == 0
    assert [fault.rule for fault in refused.faults] == ["locator"]
    assert "plain name" in refused.faults[0].message


@then("nothing is written anywhere, inside the store or outside it")
def _nothing_written_anywhere(attempt):
    assert attempt["after"] == attempt["before"]
```

Run Step 1's command again with `tail -4`. Expected: `3 failed, 3 passed`:
- the two stale scenarios fail with `AttributeError: stale`;
- the name the store lacks fails with `FileNotFoundError: [Errno 2] No such file or directory: '…/store/kb/decision/nothing-of-the-sort.yaml'`.

- [ ] **Step 3: The contract**

In `src/kb/contract/kb.proto`, replace the comment above `ValidateResponse`, and `ValidateResponse` itself, with:

```proto
// Every violation the store holds, each a fault naming the artifact, the
// place and the rule; a stored file that cannot be read is one of them.
// Every artifact last checked against an older version of its type is
// listed as stale, whether or not it still fits. With faults, a refusal:
// no store found.
message ValidateResponse {
  repeated Fault violations = 1;
  repeated Fault faults = 2;
  repeated Stale stale = 3;
}

// An artifact behind its type: the version it was last checked against,
// and the type's version now.
message Stale {
  string artifact = 1;
  int32 schema_version = 2;
  int32 current = 3;
}
```

Run `make contract`.

- [ ] **Step 4: The code**

In `src/kb/servicer.py`, in `_replace`, change

```python
        locator = values.locator(replacement.locator)
        content = values.content(str(locator.id), replacement.content, at_root=not locator.place)
```

to

```python
        locator = values.locator(replacement.locator)
        if not draft.holds(locator.id):
            raise values.Refused([_not_found(locator.id)])
        content = values.content(str(locator.id), replacement.content, at_root=not locator.place)
```

Replace `Validate` with:

```python
    def Validate(self, request, context):
        """Every artifact checked against the current version of its type, and listed as stale when it was last
        checked against an older one; a file that cannot be read is reported and the check goes on."""
        violations, stale = [], []
        for artifact_id in self._store.ids():
            try:
                artifact = self._store.load(artifact_id)
                schema = self._store.schema(artifact_id.kind)
            except Unreadable as unreadable:
                violations.append(unreadable.fault)
                continue
            if artifact["schema_version"] < schema["version"]:
                stale.append(kb_pb2.Stale(
                    artifact=str(artifact_id), schema_version=artifact["schema_version"], current=schema["version"],
                ))
            content = {key: value for key, value in artifact.items() if key not in canonical.IDENTITY[:4]}
            violations += validation.validate(str(artifact_id), content, schema["schema"], self._store)
        return kb_pb2.ValidateResponse(violations=violations, stale=stale)
```

- [ ] **Step 5: Run it green, slice 8 (whose Then these share), slice 1.20 (the check), and the suite**

```bash
.venv/bin/python -m pytest -q -m "slice-23 or slice-8 or slice-1.20" 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `8 passed, 110 deselected`; `48 failed, 70 passed`.

- [ ] **Step 6: Commit**

```bash
git add src/kb/contract/ src/kb/servicer.py tests/calls.py tests/test_create_an_artifact.py tests/test_change_an_artifact.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 23: change an artifact, behind its type or not, and refuse what cannot be changed

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 7: Checkpoint**

Set slice 23's Status to `green`. Append at the very end of the Log:

```
- <date> slice 23 green. Someone can now: replace a decision and see its version go up by one against the current version of its type; replace one behind its type and see it brought up to date, or, when the content does not fit the current version, refused with it left as it was and still listed as behind; and be refused, with nothing written, for content carrying a version, a name the store lacks, or a name that is not plain.
  Surprised by: <nothing, or what>. Three of the six scenarios (the plain change, the version in the content, the name that is not plain) went green on their step definitions alone, each red first for want of a step.
  Open questions:
  - ANSWERED: a Write of a name the store lacks is refused with the name given back, where it raised FileNotFoundError (batch 2's question).
  - For slicing (slice 43): Validate now lists every stale artifact, as { artifact, schema_version, current }; slice 43's stale scenarios read that list.
  Next: slice 25.
```

Commit the plan: `Slice 23 green`.

---

### Task 4: Slice 25, create names what it stores and refuses what breaks its type

**Slice plan entry:** Slice 25, capability. Unknown: none. Scenarios:

1. kb / create-an-artifact / The name of a new artifact is made from its title, not asked for
2. kb / create-an-artifact / Two parts with the same title are given names of their own
3. kb / create-an-artifact / An artifact missing a required section is refused
4. kb / create-an-artifact / An artifact pointing at something that is not there is refused

Scenarios 1, 3 and 4 go green on their step definitions alone, as slice 7's checkpoint predicted for 3 and 4, each red first for want of a step. Scenario 2 needs a number on a clashing part name.

**Files:**
- Modify: `src/kb/servicer.py` (`_name_items` numbers a clash; `_unclaimed` uses the new `_numbered`)
- Modify: `tests/test_create_an_artifact.py` (eight steps appended)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `servicer._name_items` (Task 1), `servicer._unclaimed` (slice 8.1). `test_create_an_artifact.py`'s `SECTIONS`, its Background, its `When the client creates a decision titled "{title}", saying which role and why` (fixture `created`), and `calls.request`, `read`.
- Produces: `servicer._numbered(name: str, taken) -> str`, where `taken` is any callable that says whether a name is taken.

- [ ] **Step 1: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-25 2>&1 | grep -E "^E |passed|failed" | tail -5
```

Expected: `4 failed`, each a `StepDefinitionNotFoundError`:
- `Then "the name the client is given is made from that title"`;
- `When "the client creates a decision carrying two options with the same title, saying which role and why"`;
- `When "the client creates a decision with a rationale and no purpose, saying which role and why"`;
- `When "the client creates a decision that supersedes a decision the store does not hold, saying which role and why"`.

- [ ] **Step 2: The steps**

Append to `tests/test_create_an_artifact.py`:

```python


TWICE = [
    {"title": "Keep weekly", "body": "Review every Monday."},
    {"title": "Keep weekly", "body": "Review every Monday, before opening."},
]


@then("the name the client is given is made from that title")
def _name_from_the_title(created):
    assert not created.faults, created.faults
    assert created.id == "decision/price-reviews-happen-weekly"


@then("the client never said what the name should be")
@then("the client never said what either name should be")
def _no_name_asked_for():
    assert set(kb_pb2.CreateRequest.DESCRIPTOR.fields_by_name) == {"type", "title", "content", "actor", "message"}
    assert all("id" not in part for part in [*SECTIONS, *TWICE])


@when(
    "the client creates a decision carrying two options with the same title, saying which role and why",
    target_fixture="created",
)
def _create_with_two_options_titled_alike(client):
    return request(client, "decision", "Price reviews happen weekly", {"sections": SECTIONS, "options": TWICE})


@then("each option is given a name of its own, the second the name of the first with a number added")
def _options_named_apart(root, client, created):
    assert not created.faults, created.faults
    assert [(stub.id, stub.title) for stub in read(client, created.id).parts] == [
        ("keep-weekly", "Keep weekly"), ("keep-weekly-2", "Keep weekly"),
    ]
    on_disk = canonical.load((root / "kb" / f"{created.id}.yaml").read_text())
    assert on_disk["options"] == [{"id": "keep-weekly", **TWICE[0]}, {"id": "keep-weekly-2", **TWICE[1]}]


@when("the client creates a decision with a rationale and no purpose, saying which role and why", target_fixture="refused")
def _create_without_a_purpose(client):
    return request(client, "decision", "Price reviews happen weekly", {"sections": SECTIONS[1:]}, message="Record it")


@then("the artifact is rejected because the sections the type requires must all be present, in order")
def _rejected_for_the_sections(refused):
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.artifact, fault.path, fault.rule) for fault in refused.faults] == [
        ("decision/price-reviews-happen-weekly", "sections", "sections"),
    ]
    assert refused.faults[0].message == (
        "the sections the type requires must all be present, in order; 'Purpose' is missing"
    )


@when(
    "the client creates a decision that supersedes a decision the store does not hold, saying which role and why",
    target_fixture="refused",
)
def _create_superseding_nothing(client):
    return request(client, "decision", "Price reviews happen weekly", {
        "supersedes": "decision/prices-are-reviewed-monthly", "sections": SECTIONS,
    }, message="Record it")


@then("the artifact is rejected because a link must land on a node of a kind the type allows")
def _rejected_for_the_link(refused):
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.artifact, fault.path, fault.rule) for fault in refused.faults] == [
        ("decision/price-reviews-happen-weekly", "supersedes", "ref"),
    ]
    assert refused.faults[0].message.startswith("a link must land on a node of a kind the type allows")
```

Run Step 1's command again. Expected: `1 failed, 3 passed`. The failure is the two options, `At index 1 diff: ('keep-weekly', 'Keep weekly') != ('keep-weekly-2', 'Keep weekly')`: the second option took the first's name.

- [ ] **Step 3: The code**

In `src/kb/servicer.py`, replace `_name_items` with:

```python
def _name_items(schema: dict, content: dict, keep_named: bool) -> None:
    """Every item of every part collection given its name: from its title when it carries one, otherwise from its
    place in the collection, counted from 1, with a number added as an artifact's name has when an item beside it
    already has that name. On a write an item already carrying a name is the item of that name, moved or changed
    where it stands, and keeps it; a name is minted once and never worked out again."""
    for collection in schema.get("parts", {}):
        items = content.get(collection, [])
        taken = {item["id"] for item in items if keep_named and "id" in item}
        for place, item in enumerate(items, start=1):
            if keep_named and "id" in item:
                continue
            item["id"] = _numbered(values.slug(item["title"]) if "title" in item else str(place), taken.__contains__)
            taken.add(item["id"])
```

and replace `_unclaimed` with `_unclaimed` and `_numbered`:

```python
def _unclaimed(draft: Draft, named: ArtifactId) -> ArtifactId:
    """The name a title gives, or, when the store or an earlier change in the set already holds it, that name with
    -2, -3 and so on added: the first that nothing holds. What already holds a name keeps it."""
    return ArtifactId(named.kind, _numbered(named.slug, lambda slug: draft.holds(ArtifactId(named.kind, slug))))


def _numbered(name: str, taken) -> str:
    """The name, or, when taken says it is taken, that name with -2, -3 and so on added: the first it does not."""
    candidate, number = name, 1
    while taken(candidate):
        number += 1
        candidate = f"{name}-{number}"
    return candidate
```

- [ ] **Step 4: Run it green, slices 8.1 and 14 (the two other users of the numbering), and the suite**

```bash
.venv/bin/python -m pytest -q -m "slice-25 or slice-8.1 or slice-14" 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `6 passed, 112 deselected`; `44 failed, 74 passed`.

- [ ] **Step 5: Commit**

```bash
git add src/kb/servicer.py tests/test_create_an_artifact.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 25: create names what it stores and refuses what breaks its type

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 6: Checkpoint**

Set slice 25's Status to `green`. Append at the very end of the Log:

```
- <date> slice 25 green. Someone can now: create a decision and be given a name made from its title that they never chose; give two options one title and find them named keep-weekly and keep-weekly-2; and be refused a decision with no purpose, or one superseding a decision the store lacks, with the rule named.
  Surprised by: <nothing, or what>. Three of the four scenarios went green on their step definitions alone, each red first for want of a step, as slice 7's checkpoint predicted for the two refusals.
  Open questions: none.
  Next: slice 27.
```

Commit the plan: `Slice 25 green`.

---

### Task 5: Slice 27, a malformed type is refused

**Slice plan entry:** Slice 27, capability. Unknown: none. Scenario:

1. kb / define-a-type / Something that is not a well-formed type is refused

It goes green on its step definitions alone (Decision 8). It is red first for want of a step, so bdd-red-green's first stop condition is not met. No production code is written.

**Files:**
- Modify: `tests/test_define_a_type.py` (two steps appended)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `calls.request`, `calls.read`, both already imported by `test_define_a_type.py`; the Background `Given a store`.
- Produces: nothing.

- [ ] **Step 1: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-27 2>&1 | grep -E "^E |passed|failed" | tail -2
```

Expected: `1 failed`, a `StepDefinitionNotFoundError` for `When "the client defines a type that does not match the type that describes types"`.

- [ ] **Step 2: The steps**

Append to `tests/test_define_a_type.py`:

```python


@when("the client defines a type that does not match the type that describes types", target_fixture="refused")
def _define_a_malformed_type(client):
    return request(client, "schema", "Shelf label", {"version": 1, "schema": {"type": "label"}}, message="Define Shelf label")


@then("the type is rejected because it does not match the type that describes types")
def _rejected_by_the_metaschema(client, refused):
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.artifact, fault.path, fault.rule) for fault in refused.faults] == [
        ("schema/shelf-label", "schema/type", "anyOf"),
    ]
    assert "'label' is not valid" in refused.faults[0].message
    assert [fault.rule for fault in read(client, "schema/shelf-label").faults] == ["not-found"]
```

- [ ] **Step 3: Run it green, and the suite**

```bash
.venv/bin/python -m pytest -q -m slice-27 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `1 passed, 117 deselected`; `43 failed, 75 passed`.

- [ ] **Step 4: Commit**

```bash
git add tests/test_define_a_type.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 27: a malformed type is refused

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 5: Checkpoint**

Set slice 27's Status to `green`. Append at the very end of the Log:

```
- <date> slice 27 green. Someone can now: define a type whose schema is not a JSON Schema and be refused because it does not match the type that describes types, with nothing stored.
  Surprised by: <nothing, or what>. The scenario went green on its step definitions alone, red first for want of a step: the metaschema's schema field already refers to JSON Schema's own, so the fault is ('schema/shelf-label', 'schema/type', 'anyOf').
  Open questions: none.
  Next: slice 29.
```

Commit the plan: `Slice 27 green`.

---

### Task 6: Slice 29, list artifacts of a kind

**Slice plan entry:** Slice 29, capability. Unknown: none. Scenarios:

1. kb / list-artifacts-of-a-kind / The client lists every artifact of a kind
2. kb / list-artifacts-of-a-kind / The client lists the artifacts matching a field
3. kb / list-artifacts-of-a-kind / The client lists names only

**Files:**
- Modify: `src/kb/contract/kb.proto` (the `List` rpc; `ListRequest`, `ListResponse`), then `make contract`
- Modify: `src/kb/servicer.py` (imports `text`; `List`; module function `_holds`)
- Modify: `src/kb/client.py` (`List`)
- Modify: `tests/calls.py` (new `listing`)
- Rewrite: `tests/test_list_artifacts_of_a_kind.py`
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `calls.CLIENT`, `DECISION_TYPE`, `create`, `define`. `KbServicer._stub(field, ArtifactId)`, `values.kind`, `content.text`, `Store.ids()`.
- Produces:
  - `kb_pb2.ListRequest(type, fields, form)` with `ListRequest.STUBS` and `ListRequest.IDS`, and `kb_pb2.ListResponse(stubs, ids, faults)`.
  - `InProcessClient.List`.
  - `calls.listing(client, type_name, fields=None, ids_only=False)`.

- [ ] **Step 1: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-29 2>&1 | grep -E "^E |passed|failed" | tail -4
```

Expected: `3 failed`, each a `StepDefinitionNotFoundError` for `Given "a store holding three decisions, one of them superseded"`.

- [ ] **Step 2: The steps**

In `tests/calls.py`, just above `def everything_under(directory):`, add:

```python
def listing(client, type_name, fields=None, ids_only=False):
    """The artifacts of a kind, those whose fields hold the values given, as stubs or as names only."""
    form = kb_pb2.ListRequest.IDS if ids_only else kb_pb2.ListRequest.STUBS
    return client.List(kb_pb2.ListRequest(type=type_name, fields=fields or {}, form=form))


```

Replace the whole of `tests/test_list_artifacts_of_a_kind.py` with:

```python
import copy

from pytest_bdd import given, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, create, define, listing
from kb import client as kb_client
from kb.content import loads
from kb.contract import kb_pb2

scenarios("list-artifacts-of-a-kind.feature")

SECTIONS = [
    {"title": "Purpose", "body": "Keep the shop running.\n"},
    {"title": "Rationale", "body": "It was agreed.\n"},
]
WEEKLY = "decision/price-reviews-happen-weekly"
MONTHLY = "decision/prices-are-reviewed-monthly"
THURSDAYS = "decision/restock-on-thursdays"


@given("a store holding three decisions, one of them superseded", target_fixture="client")
def _store_with_three_decisions(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    decision_type = copy.deepcopy(DECISION_TYPE)
    decision_type["schema"]["properties"]["status"] = {"type": "string"}
    decision_type["schema"]["summary"] = ["supersedes", "status"]
    define(client, decision_type)
    create(client, "decision", {"title": "Prices are reviewed monthly", "status": "superseded", "sections": SECTIONS})
    create(client, "decision", {
        "title": "Price reviews happen weekly", "status": "accepted", "supersedes": MONTHLY, "sections": SECTIONS,
    })
    create(client, "decision", {"title": "Restock on Thursdays", "status": "accepted", "sections": SECTIONS})
    return client


@when("the client lists the decisions", target_fixture="listed")
def _list_the_decisions(client):
    return listing(client, "decision")


@then("the client is given a stub of each of the three")
def _a_stub_of_each(listed):
    assert not listed.faults, listed.faults
    assert [(stub.id, stub.type, stub.title, loads(stub.fields)) for stub in listed.stubs] == [
        (WEEKLY, "decision", "Price reviews happen weekly", {"supersedes": MONTHLY, "status": "accepted"}),
        (MONTHLY, "decision", "Prices are reviewed monthly", {"status": "superseded"}),
        (THURSDAYS, "decision", "Restock on Thursdays", {"status": "accepted"}),
    ]
    assert not listed.ids


@when("the client lists the decisions that are superseded", target_fixture="listed")
def _list_the_superseded(client):
    return listing(client, "decision", fields={"status": "superseded"})


@then("the client is given only the superseded one")
def _only_the_superseded(listed):
    assert not listed.faults, listed.faults
    assert [(stub.id, stub.title) for stub in listed.stubs] == [(MONTHLY, "Prices are reviewed monthly")]


@when("the client lists the decisions asking for names only", target_fixture="listed")
def _list_names_only(client):
    return listing(client, "decision", ids_only=True)


@then("the client is given three names and nothing else")
def _three_names(listed):
    assert not listed.faults, listed.faults
    assert list(listed.ids) == [WEEKLY, MONTHLY, THURSDAYS]
    assert not listed.stubs
```

Run Step 1's command again. Expected: `3 failed`, each `AttributeError: module 'kb.contract.kb_pb2' has no attribute 'ListRequest'`.

- [ ] **Step 3: The contract**

In `src/kb/contract/kb.proto`, add `  rpc List(ListRequest) returns (ListResponse);` as the last line of `service Kb`, after `rpc Refs`, and append to the file:

```proto

// The artifacts of one kind, narrowed to those whose fields hold the
// values given, each value compared as the text it is written as. As
// stubs by default, or as names only.
message ListRequest {
  enum Form {
    STUBS = 0;
    IDS = 1;
  }
  string type = 1;
  map<string, string> fields = 2;
  Form form = 3;
}

// The matches in the order the store holds them, as stubs or as names.
// With faults, a refusal: a kind that is not a plain name, or no store
// found.
message ListResponse {
  repeated Stub stubs = 1;
  repeated string ids = 2;
  repeated Fault faults = 3;
}
```

Run `make contract`. This time `kb_pb2_grpc.py` changes too.

- [ ] **Step 4: The code**

In `src/kb/client.py`, after `Refs`, add:

```python

    def List(self, request, timeout=None):
        return self._call("List", request, kb_pb2.ListResponse)
```

In `src/kb/servicer.py`, change `from kb.content import dumps` to `from kb.content import dumps, text`. Just above `    def _stub(self, field, target_id: ArtifactId):`, add:

```python
    def List(self, request, context):
        """Every artifact of a kind whose fields hold the values asked for, in path order, as stubs or names."""
        try:
            kind = values.kind(request.type)
        except values.Refused as refused:
            return kb_pb2.ListResponse(faults=refused.faults)
        matched = [
            artifact_id for artifact_id in self._store.ids()
            if artifact_id.kind == kind and _holds(self._store.load(artifact_id), request.fields)
        ]
        if request.form == kb_pb2.ListRequest.IDS:
            return kb_pb2.ListResponse(ids=[str(artifact_id) for artifact_id in matched])
        return kb_pb2.ListResponse(stubs=[self._stub("", artifact_id) for artifact_id in matched])

```

Just above `def _entry(entry: dict) -> kb_pb2.Entry:`, add:

```python
def _holds(artifact: dict, fields) -> bool:
    """Whether each field named holds the value given, compared as the text the value is written as."""
    return all(field in artifact and text(artifact[field]) == value for field, value in fields.items())


```

- [ ] **Step 5: Run it green, and the suite**

```bash
.venv/bin/python -m pytest -q -m slice-29 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `3 passed, 115 deselected`; `40 failed, 78 passed`.

- [ ] **Step 6: Commit**

```bash
git add src/kb/contract/ src/kb/client.py src/kb/servicer.py tests/calls.py tests/test_list_artifacts_of_a_kind.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 29: list artifacts of a kind

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 7: Checkpoint**

Set slice 29's Status to `green`. Append at the very end of the Log:

```
- <date> slice 29 green. Someone can now: list the decisions and get a stub of each, narrow the list to those whose status is superseded, or ask for names only and get three names and nothing else.
  Surprised by: <nothing, or what>.
  Open questions:
  - QUESTION FOR THE SPEC: a field filter compares the text a value is written as, so true matches "true" and 12 matches "12"; no scenario filters on anything but text.
  - QUESTION FOR THE SPEC: List over a store holding a file it cannot read raises store.Unreadable through the client. (Review Focus 4)
  - QUESTION FOR THE SPEC: List of a kind the store holds no type for answers nothing, where Create refuses that kind as its own fault. (Review Focus 5)
  Next: the whole-batch review.
```

Commit the plan: `Slice 29 green`.

---

## After slice 29

Not a slice. Run the whole-batch review over the commits of Tasks 1 to 6, using `superpowers:requesting-code-review` with this plan and the spec as the brief. Every finding goes to `slicing-into-increments`, which places it by its unknown among the slices not yet begun. No finding is coded here.

The contract grows in this batch (a rpc, a read level, the stale list), and batch 3's three rpcs are still unreleased. The version stays `0.1.0`. Whether to bump it and tag a release is the user's call, as the 0.1 tag was, and the review should say whether anything in this batch stands in the way. The next six in the slice plan are 31, 33, 35, 37, 39 and 41.
