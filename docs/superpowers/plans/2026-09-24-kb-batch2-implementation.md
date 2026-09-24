# kb Batch 2 Implementation Plan: slices 2, 3, 5, 6, 7 and 8

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Each task is one slice of `docs/superpowers/plans/2026-09-24-kb-slices.md`. Inside a task, follow `shopsystem-bdd:bdd-red-green` scenario by scenario. Its stop conditions, hand-back, and checkpoint apply, and they override any step here that conflicts with them.

**Goal:** Types and changes, the next six slices. A type can use a shape another stored type defines, and a type can be built on a base. A client can make several changes in one go and gets a name for the set. A set with one bad change writes nothing and reports every fault. A create reports all its faults at once: a missing required section and a link that lands nowhere. A client can replace an artifact, and a refused replacement leaves it as it was.

**Architecture:** kb is the Python package `kb` in `/home/vscode/shopsystem-kb`. A protobuf contract (`kb.contract`) sits in front of a servicer over a `Store`. The store keeps one canonical YAML file per artifact under `<root>/kb/`, which is itself a git repository. `kb.values` holds the boundary conversions, one per kind of value. `kb.validation` composes a type's JSON Schema with kb's structural fragments and checks it in one pass. This plan:
- gives that one validator a `referencing` registry that finds `kb:schema/<type>` in the store (slice 2);
- reads kb's own keywords through a type's composition, base first (`validation.composition`). The required-sections rule reads it (slice 6), and so does the link rule (slice 7);
- builds one write path, `KbServicer._land`, used by Create, the new Apply, and the new Write. It applies each operation to a `store.Draft`, checks it there, and writes nothing until every operation passes. Then it saves every artifact, writes one journal entry per operation, all naming the set, and makes one commit (slices 5, 6, 8);
- moves the content conversion into `values.content`, the one function Create, Write and Apply all use.

**Provenance:** Every code block in this plan was put together in a scratch clone of this repository (`/tmp/batch2/kb`) on 2026-09-24, run with this checkout's `.venv` and `PYTHONPATH=/tmp/batch2/kb/src`. The tasks were applied in order and run. The red and green results, the suite counts, and the Review Focus reproductions below are what those runs gave. This repository was not touched except to write this plan.

**Tech Stack:** Python 3.11, setuptools (src layout), protobuf + grpcio + grpcio-tools (generated code committed; `make contract` regenerates it), python-jsonschema 4.26 (Draft 2020-12) with `referencing` 0.37, ruamel.yaml 0.19 (`YAML(typ="safe", pure=True)`, YAML 1.2), git via subprocess, pytest 9 + pytest-bdd 8.

**Spec:** `docs/superpowers/specs/2026-09-23-kb-design.md`: "Schema language", "The contract", "Input safety", "Write path". Slice plan: `docs/superpowers/plans/2026-09-24-kb-slices.md`, slices 2, 3, 5, 6, 7, 8. Feature files: `features/`. The scenarios of each slice carry `@slice-<n>`, so `.venv/bin/python -m pytest -q -m slice-5` runs a slice.

## Global Constraints

- Feature files are read-only for the implementer. Only `slicing-into-increments` edits a tag line, and only `formulating-features` edits a Given, When, or Then. Any other diff under `features/` is a stop condition.
- Code only what a scenario asserts (bdd-red-green). Where the scenarios are silent, the code is silent, and the silence goes into the checkpoint entry as an open question. The decisions this plan makes are listed below, each tied to the spec line or scenario that asks for it.
- **Extend, never add beside.** The spec says some rules are composed JSON Schema fragments or single boundary conversions. Where it does, a task extends that one thing and adds no second check next to it:
  - A cross-type `$ref` resolves in the one validator pass, through its registry. It is not a second validation.
  - The name inside a `kb:` URI goes through `values.artifact_id`, and so does the target of a link.
  - Content is converted by `values.content`, one function for Create, Write and Apply.
  - Read's stubs and inbound counts use `validation.links`, the same function the link rule uses. `_reference_fields` and `_as_list` are deleted.
  - Create is a set of one through `_land`, not a second write path.
- Spec, schema language: "Cross-schema `$ref` resolves through the `referencing` library against a registry of every `schema/*` artifact in the corpus, using URIs of the form `kb:schema/<type>#/...`."
- Spec, composition: "kb's five keywords compose through `allOf` and `$ref` as well: reference fields are collected from every composed schema, the required section tree is the base's tree followed by the type's, and `parts` and `summary` merge the same way, base first."
- Spec, code rules: "Code checks only what the schema language cannot express: a reference resolving to a node of a permitted type, required sections in their declared order, and id uniqueness in a collection."
- Spec, write path: "apply to a copy, validate the copy against the corpus, swap in only on success." Also: "Collect every error; if any, stop here." And: "Every mutating rpc returns all errors found, not the first."
- Spec, journal: "`batch`: the id of the `Apply` that wrote it, or the entry's own id for a single operation, so the journal alone shows what landed together."
- Spec, contract: "`Apply` | ordered list of Create/Write/Append/Delete, actor, message | batch id, minted by kb; per-operation results; one commit". Also: "`Write` | locator, content, actor, message | revision".
- Errors are a typed list of `{ artifact, path, rule, message }`. A response that carries faults is a refusal, and nothing was written.
- kb is exercised through its in-process transport, never mocked. kb ships no domain types.
- Each checkout has its own virtualenv. Run the suite with `make test` (`.venv/bin/python -m pytest -q`) and one slice with `.venv/bin/python -m pytest -q -m slice-<n>`. `make contract` regenerates `kb_pb2.py`, `kb_pb2.pyi` and `kb_pb2_grpc.py` from `kb.proto`, and all four files are committed together.
- Work on `main` in `/home/vscode/shopsystem-kb`. A worktree needs its own `.venv` first (`make dev`).
- shop-knowledge pins kb at `v0.1.0` (a git dependency), so nothing here touches or runs its suite. Releasing and bumping the pin is not part of this plan.
- Commits: `git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit`, the message ending with the Co-Authored-By line of the model that made the commit, e.g. `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- The suite prints pytest-bdd `PytestRemovedIn10Warning`s. That is the baseline, not a fault.
- Baseline before Task 1: `make test` → `73 failed, 45 passed`.

## Decisions this plan makes (the spec left them open or silent)

1. **How a type names another type's shape.** Every `kb:` URI is found lazily, through the `retrieve` of a `referencing.Registry` built per validation from the store the call sees: `validation.registry(corpus)`. The name after `kb:` goes through `values.artifact_id`, must be of kind `schema`, and must be held. Anything else is `NoSuchResource`, which jsonschema raises as `Unresolvable` (Review Focus 4). A shape's own `#/...` references resolve inside that shape's type; this was checked in scratch. Pinned by slice 2.
2. **The composition walk.** `validation.composition(schema, corpus) -> list[dict]` lists the schemas a type is built from, base first:
   - each `allOf` member in order, walked the same way;
   - a whole type named by `$ref: kb:schema/<type>` (no `#`), followed to that type's schema;
   - last, the schema itself.

   kb's keywords are read through this list: the required section tree in Task 4 and the reference fields in Task 5. `parts` and `summary` still read the type's top level, since no scenario in this batch observes them through a base. That is logged as an open question in Task 4.
3. **The base scenario's type.** The decision type of slice 3 writes its own keywords beside `allOf: [{$ref: kb:schema/base}]` at its top level, not inside a second `allOf` member. The walk treats both forms the same. This form was chosen because with it, slice 3's scenario fails once the sections rule exists unless the base's sections are merged first. Scratch confirmed this both ways: without the merge, "'Rationale' is out of its place"; with the type first, "'Purpose' is out of its place". So slice 3 goes green on its steps alone in Task 2, and it becomes the scenario that pins the merge in Task 4.
4. **The write path.** `KbServicer._land(operations, actor, message) -> ApplyResponse` is the only path that writes an artifact:
   - Each operation is applied in order to a `store.Draft`, which stands over the store and writes nothing. Each is checked there, against the store as the operations before it left it.
   - Every fault of every operation is collected. With any fault, nothing is written.
   - Otherwise every artifact is serialized with `canonical.dump`, and a failing dump is a fault as before. Then every artifact is saved and gets one journal entry, and there is one commit.

   Create is a set of one, and so is the new Write. So Create now leaves a journal entry, which the spec asks of every operation and which slice 9 reads.
5. **The set's name.** The batch id is the id of the set's first journal entry (`<timestamp>-1`), and every entry of the set carries it. A single operation's entry names itself, as before. The Apply request has no field for it.
6. **Apply's messages.** `Operation { oneof operation { Creation create = 1; Replacement write = 2; } }`. `Creation` is `type, title, content` and `Replacement` is `locator, content`, with no role or message of their own. `ApplyRequest { operations, actor, message }` and `ApplyResponse { batch, results, faults }`, where `Result { id, revision }`. Append and Delete join the oneof in their own slices.
7. **Pointing at what the set creates.** The second operation names the decision by the name kb will mint from its title (`decision/<slug>`). The draft holds that decision by the time the second operation is checked, so the link rule of Task 5 finds it. This is the answer to slice 5's unknown. Once slice 25 adds collision numbering, a title already taken makes that prediction wrong (Review Focus 3).
8. **kb's own rules run on content that fits the composed schema.** `validation.validate` returns the JSON Schema faults alone when there are any. Only if there are none does it run the sections and link rules and return every fault they find. This keeps slices 1.13 and 1.20, whose Thens pin exactly one fault for a section missing its title or body. It also means the rules read a well-formed tree and need no guards. Whether they should also run alongside JSON Schema faults ("returns all errors found") is logged in Task 4.
9. **The required-sections rule.**
   - Required sections come first, in declared order, at every level. Others may follow.
   - Each required section is looked for where the previous one left off. So a missing section is one fault (`'Purpose' is missing`), and a present but misplaced one is one fault (`'Purpose' is out of its place`).
   - Rule `sections`. The path is the list's node path: `sections`, or `sections/0/sections` a level down.
   - Message: `the sections the type requires must all be present, in order; '<title>' is missing`.
10. **The link rule.**
    - Rule `ref`. The path is the field, or `field/<index>` for a list.
    - Message: `a link must land on a node of a kind the type allows; '<target>' does not`.
    - The target goes through `values.artifact_id`, must be held by the draft, and must be of a kind in the field's `targets`.
    - A target naming a part (`process/x#steps/draft`) does not land yet, since no scenario in this batch writes one.
11. **Write.** `WriteRequest { locator, content, actor, message }` and `WriteResponse { revision, faults }`. A Write replaces the artifact's content, keeps its id, type and title, sets `schema_version` to the type's current version, and raises `revision` by one. Its content goes through `values.content`, so a title inside it is refused like any identity key, and a Write never changes a title.
12. **The identity check stays at the boundary.** The spec lists the identity keys among kb's composed JSON Schema fragments. Today they are checked by code, and the title has to be caught before it is merged into the tree that is validated. Task 3 moves that code unchanged into `values.content` so Write shares it, and it stays there. Making the four store-settled keys a fragment would change the rule and messages that slices 1.2 and 1.6 pin. Task 3 logs it as an open question.

## Review Focus

In this project tests are scenarios, and the feature files are the human gate, so no unit tests are added. Instead, each line below goes into the owning task's checkpoint entry as a `QUESTION FOR THE SPEC`, with the reproduction given here. Each was reproduced in scratch after all six tasks.

1. **A Write aimed at a node inside an artifact replaces the whole artifact.** Reproduction: Write with `locator {id: decision/weekly, path: sections/rationale}` and content `{sections: [Purpose, Rationale]}` answers `revision: 2`, and the whole file now holds just that content. A person would expect either the node alone to change (slice 13) or a refusal. Task 6 logs it.
2. **A Write or an Apply naming an artifact the store lacks raises.** Reproduction: `write(client, "decision/none", …)` and `apply(client, [replacement("decision/none", …)])` both raise `FileNotFoundError: … kb/decision/none.yaml` through the client. Slice 23 pins the refusal for Write. Task 6 logs Write and Task 3 logs Apply.
3. **A title already used overwrites.** Reproduction: creating `Weekly` when `decision/weekly` exists answers `decision/weekly, revision 1`, and the old file is replaced. An Apply creating `Monthly` twice answers two results named `decision/monthly`. Slice 25 builds collision numbering. After that, a set whose second operation names the first operation's artifact by its predicted name lands on the older artifact without any fault. Task 3 logs both.
4. **A type that names a type the store lacks, or names itself as its base, breaks every create of it.** Reproduction: a type with `$ref: kb:schema/nothing#/$defs/x` makes Create raise `_WrappedReferencingError: Unresolvable: kb:schema/nothing#/$defs/x`. A type with `allOf: [{$ref: kb:schema/loop}]` in `schema/loop` raises `RecursionError`. Slice 27 checks a type only against the metaschema. Task 1 logs it.
5. **A Write to an artifact whose stored file cannot be read raises.** Reproduction: after `title: [` is written by hand into `decision/weekly.yaml`, a Write raises `store.Unreadable` through the client. Read answers the same case with the fault. Task 6 logs it.

---

### Task 1: Slice 2, two types share a shape

**Slice plan entry:** Slice 2, capability. Unknown: does a reference from one stored type into another resolve through the validator's registry when every type is itself an artifact in the store? Scenario:

1. kb / define-a-type / Two types share a shape

**Files:**
- Modify: `src/kb/validation.py` (imports, new `registry`, `_type_schema`, `validate` takes the corpus)
- Modify: `src/kb/servicer.py` (the two `validation.validate` calls pass the store)
- Modify: `tests/test_define_a_type.py`
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `tests/calls.py`: `define(client, type_content)` and `request(client, type_name, title, content, message=…)`. The Background Given `a store` (conftest).
- Produces: `validation.validate(artifact_id: str, content: dict, schema: dict, corpus) -> list[kb_pb2.Fault]`, where `corpus` is anything with `holds(ArtifactId) -> bool` and `load(ArtifactId) -> dict` (`Store` now, `Draft` from Task 3). Also `validation.registry(corpus) -> referencing.Registry`, `validation._type_schema(uri, corpus) -> dict` (raises `NoSuchResource`), and `validation.TYPE_URI = "kb:"`. Task 4 uses `_type_schema` and `TYPE_URI`.

- [ ] **Step 1: Run it red**

```bash
cd /home/vscode/shopsystem-kb && .venv/bin/python -m pytest -q -m slice-2 2>&1 | grep -E "^E |passed|failed" | tail -2
```

Expected: `1 failed`, a `StepDefinitionNotFoundError` for `Given "a type that defines the shape of a binding"`.

- [ ] **Step 2: The steps**

In `tests/test_define_a_type.py`, change the first three lines

```python
from pytest_bdd import scenarios, then, when

from calls import create, define, read
```

to

```python
from pytest_bdd import given, scenarios, then, when

from calls import create, define, read, request
```

and append:

```python


TOOL_TYPE = {
    "title": "Tool",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {"title": {"type": "string"}},
        "required": ["title"],
        "$defs": {
            "binding": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "value": {"type": "string"}},
                "required": ["name", "value"],
                "additionalProperties": False,
            },
        },
    },
}

TOOL_USE_TYPE = {
    "title": "Tool use",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "bindings": {"type": "array", "items": {"$ref": "kb:schema/tool#/$defs/binding"}},
        },
        "required": ["title"],
    },
}


@given("a type that defines the shape of a binding")
def _a_type_defining_a_binding(client):
    define(client, TOOL_TYPE)


@when("the client defines a second type that refers to that shape")
def _define_a_type_referring_to_it(client):
    define(client, TOOL_USE_TYPE)


@then("artifacts of the second type are checked against the shape the first type defines")
def _checked_against_the_shared_shape(client):
    fits = request(client, "tool-use", "Weigh the flour", {"bindings": [{"name": "scale", "value": "kitchen"}]})
    assert not fits.faults, fits.faults
    misfit = request(client, "tool-use", "Weigh the sugar", {"bindings": [{"name": "scale"}]})
    assert (misfit.id, misfit.revision) == ("", 0)
    assert [(fault.path, fault.rule) for fault in misfit.faults] == [("bindings/0", "required")]
    assert "'value' is a required property" in misfit.faults[0].message
```

```bash
.venv/bin/python -m pytest -q -m slice-2 2>&1 | grep -E "^E .*(Error|Unresolvable)|passed|failed"
```

Expected: `referencing.exceptions.Unresolvable: kb:schema/tool#/$defs/binding` (after a `URLError: <urlopen error unknown url type: kb>`) and `1 failed`. jsonschema's default registry tries to fetch `kb:` over the network.

- [ ] **Step 3: The registry**

In `src/kb/validation.py`, replace

```python
from jsonschema import Draft202012Validator

from kb.contract import kb_pb2
```

with

```python
from jsonschema import Draft202012Validator
from referencing import Registry
from referencing.exceptions import NoSuchResource
from referencing.jsonschema import DRAFT202012

from kb import values
from kb.contract import kb_pb2
from kb.values import Kind

TYPE_URI = "kb:"
```

and replace the whole function `validate` with:

```python
def registry(corpus) -> Registry:
    """Every type the corpus holds, found by the URI kb:schema/<type> when a schema refers to it, and only then."""
    def retrieve(uri: str):
        return DRAFT202012.create_resource(_type_schema(uri, corpus))
    return Registry(retrieve=retrieve)


def _type_schema(uri: str, corpus) -> dict:
    """The JSON Schema of the type a kb: URI names, its name checked as any other name is. NoSuchResource if none."""
    try:
        schema_id = values.artifact_id(uri.removeprefix(TYPE_URI)) if uri.startswith(TYPE_URI) else None
    except values.Refused:
        schema_id = None
    if schema_id is None or schema_id.kind != Kind("schema") or not corpus.holds(schema_id):
        raise NoSuchResource(ref=uri)
    return corpus.load(schema_id)["schema"]


def validate(artifact_id: str, content: dict, schema: dict, corpus) -> list[kb_pb2.Fault]:
    """Every violation, as artifact, path, rule, message. A kb:schema/<type> reference resolves against the corpus."""
    return [
        kb_pb2.Fault(
            artifact=artifact_id,
            path="/".join(str(step) for step in error.absolute_path),
            rule=error.validator,
            message=error.message,
        )
        for error in Draft202012Validator(compose(schema), registry=registry(corpus)).iter_errors(content)
    ]
```

jsonschema adds the Draft 2020-12 metaschemas to any registry it is given, so the metaschema's own `$ref` to `https://json-schema.org/draft/2020-12/schema` still resolves without a network fetch.

In `src/kb/servicer.py`, change

```python
        faults = validation.validate(at, {"title": request.title, **content}, schema["schema"])
```

to

```python
        faults = validation.validate(at, {"title": request.title, **content}, schema["schema"], self._store)
```

and

```python
            violations += validation.validate(str(artifact_id), content, schema)
```

to

```python
            violations += validation.validate(str(artifact_id), content, schema, self._store)
```

- [ ] **Step 4: Run it green, and the suite**

```bash
.venv/bin/python -m pytest -q -m slice-2 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `1 passed, 117 deselected`; `72 failed, 46 passed`.

- [ ] **Step 5: Commit**

```bash
git add src/kb/validation.py src/kb/servicer.py tests/test_define_a_type.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 2: a type can use a shape another stored type defines

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 6: Checkpoint**

In `docs/superpowers/plans/2026-09-24-kb-slices.md`, set slice 2's Status to `green`. Append at the very end of the Log, and check with `tail` that it is last:

```
- <date> slice 2 green. Someone can now: define a type whose field takes a shape another stored type defines, and have its artifacts checked against that shape.
  Assumption "a reference from one stored type into another resolves through the validator's registry": <held or not>. Evidence: <the faults of the refused create, from: .venv/bin/python -m pytest -q -m slice-2 passing, and the step's assertion [("bindings/0", "required")]>.
  Surprised by: <nothing, or what>.
  Open questions:
  - QUESTION FOR THE SPEC: a type whose `$ref` names a type the store does not hold (`kb:schema/nothing#/$defs/x`) makes every create of it raise `Unresolvable` through the client; a type naming itself as its base raises `RecursionError`. Should defining such a type be refused? (Review Focus 4)
  Next: slice 3.
```

Commit the plan: `Slice 2 green`.

---

### Task 2: Slice 3, a type built on a base

**Slice plan entry:** Slice 3, capability. Unknown: do kb's own keywords (required sections, references, parts, and summary fields) merge through composition, with the base's part coming first? Scenario:

1. kb / define-a-type / A type built on a shared base carries the base's fields and sections

**Files:**
- Modify: `tests/test_define_a_type.py`
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: Task 1's registry, which makes `$ref: kb:schema/base` resolve. `define` and `request` from `tests/calls.py`. The fixture `root` (conftest).
- Produces: `BASE_TYPE`, `DECISION_ON_BASE_TYPE` and `BASE_SECTIONS` in `tests/test_define_a_type.py`. Task 4 runs this scenario as its check that the merge is base first.

This scenario is expected to go **green on its step definitions alone**. The JSON Schema half of the unknown, a required `owner` coming from the base through `allOf` and `$ref`, was settled by Task 1's registry. The kb half (the base's required sections first) cannot fail until a required-sections rule exists, and Task 4 builds that rule. The Background step (Given `a store`) exists, but the scenario's own Given has no step. So the scenario is red first on a missing step, not green before any step exists, and bdd-red-green's first stop condition is not met. This is the same case as slice 1.25 in the log. Do not hand back for it. Log it in the checkpoint as below.

- [ ] **Step 1: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-3 2>&1 | grep -E "^E |passed|failed" | tail -2
```

Expected: `1 failed`, a `StepDefinitionNotFoundError` for `Given "a base type that gives every artifact an owner and a status, and requires a purpose section"`.

- [ ] **Step 2: The steps**

In `tests/test_define_a_type.py`, change `from calls import create, define, read, request` to

```python
from calls import create, define, read, request
from kb import canonical
```

and append:

```python


BASE_TYPE = {
    "title": "Base",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {"owner": {"type": "string"}, "status": {"type": "string"}},
        "required": ["owner", "status"],
        "sections": [{"title": "Purpose"}],
    },
}

DECISION_ON_BASE_TYPE = {
    "title": "Decision",
    "version": 1,
    "schema": {
        "allOf": [{"$ref": "kb:schema/base"}],
        "type": "object",
        "properties": {"title": {"type": "string"}},
        "required": ["title"],
        "sections": [{"title": "Rationale"}],
    },
}

BASE_SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]


@given(
    "a base type that gives every artifact an owner and a status, and requires a purpose section"
)
def _a_base_type(client):
    define(client, BASE_TYPE)


@when("the client defines a decision type built on that base, adding a rationale section of its own")
def _define_a_decision_on_the_base(client):
    define(client, DECISION_ON_BASE_TYPE)


@then("a decision missing its owner is rejected because it does not fit its type")
def _rejected_without_an_owner(client):
    refused = request(client, "decision", "Price reviews happen weekly", {"status": "accepted", "sections": BASE_SECTIONS})
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.path, fault.rule) for fault in refused.faults] == [("", "required")]
    assert "'owner' is a required property" in refused.faults[0].message


@then("a decision reads back with its purpose before its rationale")
def _purpose_before_rationale(root, client):
    created = request(client, "decision", "Price reviews happen weekly", {
        "owner": "shopkeeper", "status": "accepted", "sections": BASE_SECTIONS,
    })
    assert not created.faults, created.faults
    on_disk = canonical.load((root / "kb" / f"{created.id}.yaml").read_text())
    assert [section["title"] for section in on_disk["sections"]] == ["Purpose", "Rationale"]
```

The last Then reads the stored file, as slice 1's Thens do, because Read at every depth is slice 21's.

- [ ] **Step 3: Run it, and the suite**

```bash
.venv/bin/python -m pytest -q -m slice-3 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `1 passed, 117 deselected`; `71 failed, 47 passed`. No production code is written in this task.

- [ ] **Step 4: Commit**

```bash
git add tests/test_define_a_type.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 3: a type built on a base carries the base's fields

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 5: Checkpoint**

Set slice 3's Status to `green`. Append at the very end of the Log:

```
- <date> slice 3 green. Someone can now: define a type on a base and have a decision without the base's owner refused.
  Assumption "kb's keywords merge through composition with the base first": not yet observable. The JSON Schema half held through slice 2's registry: a decision without an owner is refused at "" with rule required. The scenario went green on its step definitions alone, after failing first on a missing Given, as the task predicted. Its last Then cannot fail until a required-sections rule exists; slice 6 builds that rule over the composition, and this scenario is then what pins base first.
  Surprised by: <nothing, or what>.
  Open questions: none. Next: slice 5.
```

Commit the plan: `Slice 3 green`.

---

### Task 3: Slice 5, several changes land as one change

**Slice plan entry:** Slice 5, capability. Unknown: can the second operation in a set point at the artifact the first one creates, before either has landed? Scenario:

1. kb / make-several-changes-in-one-go / The client makes several changes in one go

**Files:**
- Modify: `src/kb/contract/kb.proto`, then regenerate `kb_pb2.py`, `kb_pb2.pyi`, `kb_pb2_grpc.py` (`make contract`)
- Modify: `src/kb/values.py` (new `content`)
- Modify: `src/kb/store.py` (`save` takes text; new `Draft`)
- Modify: `src/kb/journal.py` (`write` takes `batch`)
- Modify: `src/kb/servicer.py` (whole file: `Create` and `Apply` through `_land`)
- Modify: `src/kb/client.py` (`_call`, `Apply`)
- Modify: `tests/calls.py`, `tests/test_make_several_changes_in_one_go.py`
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `validation.validate(artifact_id, content, schema, corpus)` (Task 1). `DECISION_TYPE` and `WORK_ITEM_TYPE` in `tests/calls.py`.
- Produces:
  - contract messages `Operation`, `Creation`, `Replacement`, `ApplyRequest`, `ApplyResponse` and `Result`, and the rpc `Apply`;
  - `values.content(artifact: str, text: str) -> dict`, which raises `values.Refused`;
  - `store.Draft(store)`, with `put(ArtifactId, dict)`, `holds`, `load` and `schema`;
  - `Store.save(artifact_id, text: str) -> Path`;
  - `journal.write(…, seq=1, batch="") -> Path`, where the path's stem is the entry id;
  - `KbServicer._land(operations, actor, message) -> kb_pb2.ApplyResponse`, `_apply`, `_create(draft, creation) -> ArtifactId` and `_replace(draft, replacement) -> ArtifactId`;
  - `InProcessClient._call(rpc, request, response)`;
  - in `tests/calls.py`: `apply(client, operations, message=…)`, `creation(type_name, title, content)` and `replacement(artifact_id, content)`;
  - in the test module: the Background Given `a store holding a decision type and a work item`, and the names `DECISION`, `WORK_ITEM` and `SECTIONS`.

  Tasks 4 and 6 use all of these.

- [ ] **Step 1: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-5 2>&1 | grep -E "^E |passed|failed" | tail -2
```

Expected: `1 failed`, a `StepDefinitionNotFoundError` for `Given "a store holding a decision type and a work item"`.

- [ ] **Step 2: The steps**

Append to `tests/calls.py`:

```python


def apply(client, operations, message="Make several changes"):
    """An Apply of the operations in order, under the client's role. Returns the response, faults and all."""
    return client.Apply(kb_pb2.ApplyRequest(operations=operations, actor=CLIENT, message=message))


def creation(type_name, title, content):
    """A Create inside a set: the title beside the content, the role and message the set's."""
    return kb_pb2.Operation(create=kb_pb2.Creation(type=type_name, title=title, content=dumps(content)))


def replacement(artifact_id, content):
    """A Write of a whole artifact inside a set."""
    return kb_pb2.Operation(write=kb_pb2.Replacement(locator=kb_pb2.Locator(id=artifact_id), content=dumps(content)))
```

Replace the whole of `tests/test_make_several_changes_in_one_go.py` with:

```python
import subprocess

from pytest_bdd import given, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, WORK_ITEM_TYPE, apply, create, creation, define, replacement
from kb import canonical, client as kb_client
from kb.contract import kb_pb2

scenarios("make-several-changes-in-one-go.feature")

DECISION = "decision/price-reviews-happen-weekly"
WORK_ITEM = "work-item/move-the-review-to-mondays"
SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]


def _git(root, *args):
    return subprocess.run(["git", "-C", str(root / "kb"), *args], capture_output=True, text=True, check=True).stdout


def _journal(root):
    """Every journal entry in the store, oldest first."""
    return [canonical.load(path.read_text()) for path in sorted((root / "kb" / "journal").rglob("*.yaml"))]


@given("a store holding a decision type and a work item", target_fixture="client")
def _store_with_a_decision_type_and_a_work_item(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    define(client, WORK_ITEM_TYPE)
    create(client, "work-item", {"title": "Move the review to Mondays"})
    return client


@when(
    "the client asks, in one go, for a decision to be created and the work item to point at it, in that order, "
    "saying which role and why",
    target_fixture="applied",
)
def _create_and_point_at_it(client):
    return apply(client, [
        creation("decision", "Price reviews happen weekly", {"sections": SECTIONS}),
        replacement(WORK_ITEM, {"decisions": [DECISION]}),
    ], message="Move price reviews to weekly")


@then("the client is given one name for the set, which the client never asked for")
def _given_a_name_for_the_set(applied):
    assert not applied.faults, applied.faults
    assert applied.batch
    assert "batch" not in kb_pb2.ApplyRequest.DESCRIPTOR.fields_by_name


@then("each change also comes back with its own result")
def _a_result_for_each_change(applied):
    assert [(result.id, result.revision) for result in applied.results] == [(DECISION, 1), (WORK_ITEM, 2)]


@then("the store's history shows the set as one change")
def _one_change_in_the_history(root, applied):
    in_set = [entry for entry in _journal(root) if entry["batch"] == applied.batch]
    assert [(entry["op"], entry["artifact"], entry["revision"]) for entry in in_set] == [
        ("create", DECISION, 1), ("write", WORK_ITEM, 2),
    ]
    assert _git(root, "log", "-1", "--format=%an%x09%s").strip() == "client\tMove price reviews to weekly"
    in_commit = set(_git(root, "show", "--name-only", "--format=", "HEAD").split())
    assert {f"{DECISION}.yaml", f"{WORK_ITEM}.yaml"} <= in_commit
    assert len([name for name in in_commit if name.startswith("journal/")]) == 2
```

The second operation names the decision by the name kb mints from its title (Decision 7).

```bash
.venv/bin/python -m pytest -q -m slice-5 2>&1 | grep -E "^E .*Error|passed|failed"
```

Expected: `AttributeError: module 'kb.contract.kb_pb2' has no attribute 'Operation'` and `1 failed`.

- [ ] **Step 3: The contract**

In `src/kb/contract/kb.proto`, change

```proto
  rpc Validate(ValidateRequest) returns (ValidateResponse);
}
```

to

```proto
  rpc Validate(ValidateRequest) returns (ValidateResponse);
  rpc Apply(ApplyRequest) returns (ApplyResponse);
}
```

and append at the end of the file:

```proto

// One change in a set: a create or a replacement, with no role or message
// of its own, since the set carries those.
message Operation {
  oneof operation {
    Creation create = 1;
    Replacement write = 2;
  }
}

// What a Create carries but the role and the message.
message Creation {
  string type = 1;
  string title = 2;
  string content = 3;  // canonical YAML: fields, sections, parts
}

// A new content for an artifact the store holds; its title is kept.
message Replacement {
  Locator locator = 1;
  string content = 2;  // canonical YAML: fields, sections, parts
}

// Every operation lands, in order, as one change, or none does.
message ApplyRequest {
  repeated Operation operations = 1;
  Actor actor = 2;
  string message = 3;
}

// The set's name, minted by kb, and one result per operation in order.
// With faults, a refusal: every fault of every operation, and nothing
// was written.
message ApplyResponse {
  string batch = 1;
  repeated Result results = 2;
  repeated Fault faults = 3;
}

message Result {
  string id = 1;
  int32 revision = 2;
}
```

```bash
make contract && .venv/bin/python -m pytest -q -m slice-5 2>&1 | grep -E "^E .*Error|passed|failed"
```

Expected: `AttributeError: 'InProcessClient' object has no attribute 'Apply'` and `1 failed`.

- [ ] **Step 4: The boundary, the draft, and the journal's batch**

In `src/kb/values.py`, replace the line `from kb.contract import kb_pb2` with

```python
from kb import canonical
from kb.content import loads
from kb.contract import kb_pb2
```

and insert above `def root(text: str) -> Path:`:

```python
def content(artifact: str, text: str) -> dict:
    """Content as a request carries it: read plainly, and holding only what a type declares. Refused with every fault."""
    try:
        tree = loads(text)
    except canonical.NotCanonical as fault:
        raise Refused([kb_pb2.Fault(artifact=artifact, path=fault.path, rule="content", message=str(fault))]) from None
    faults = []
    for key in canonical.IDENTITY:
        if key not in tree:
            continue
        if key == "title":
            message = f"a title is given alongside the content, never inside it; the content carried the title {tree[key]!r}"
        else:
            message = f"content holds only what the type declares; {key} is settled by the store, and the content carried {key}: {tree[key]!r}"
        faults.append(kb_pb2.Fault(artifact=artifact, path=key, rule="identity", message=message))
    if faults:
        raise Refused(faults)
    return tree


```

This is `servicer._identity_faults` with the parsing of the content in front of it. Step 5 deletes that function.

In `src/kb/store.py`, replace the whole method `Store.save` with:

```python
    def save(self, artifact_id: ArtifactId, text: str) -> Path:
        """Write canonical text to a temp file and rename it into place."""
        path = self.path(artifact_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_name(path.name + ".tmp")
        temp.write_text(text)
        temp.replace(path)
        return path
```

and insert above `def _git(*args, env=None):`:

```python
class Draft:
    """The store as a set of changes would leave it: artifacts put here stand over the stored ones, and nothing is
    written. Read like the store: holds, load, schema."""

    def __init__(self, store: Store):
        self._store = store
        self._pending: dict[ArtifactId, dict] = {}

    def put(self, artifact_id: ArtifactId, artifact: dict) -> None:
        self._pending[artifact_id] = artifact

    def holds(self, artifact_id: ArtifactId) -> bool:
        return artifact_id in self._pending or self._store.holds(artifact_id)

    def load(self, artifact_id: ArtifactId) -> dict:
        if artifact_id in self._pending:
            return self._pending[artifact_id]
        return self._store.load(artifact_id)

    def schema(self, kind: Kind) -> dict:
        return self.load(ArtifactId(Kind("schema"), kind.name))


```

In `src/kb/journal.py`, change the signature and docstring of `write`

```python
          schema_version: int, written: Path, message: str, seq: int = 1) -> Path:
    """Write one entry and return its file. A change made alone names itself as its batch."""
```

to

```python
          schema_version: int, written: Path, message: str, seq: int = 1, batch: str = "") -> Path:
    """Write one entry and return its file; its stem is the entry's id. A change made alone names itself as its batch."""
```

and `"batch": entry_id,` to `"batch": batch or entry_id,`.

- [ ] **Step 5: One write path, and the Apply call**

Replace the whole of `src/kb/servicer.py` with:

```python
"""The contract's servicer: every rpc, over one store. Hosted in-process today; grpc.server can host it later.

Each rpc first turns what the request carries into checked values (kb.values); nothing past that point sees a
string that came from the request.
"""
from kb import canonical, journal, validation, values
from kb.content import dumps
from kb.contract import kb_pb2, kb_pb2_grpc
from kb.metaschema import METASCHEMA
from kb.store import Draft, Store, Unreadable
from kb.values import ArtifactId, Kind

METASCHEMA_ID = ArtifactId(Kind("schema"), "schema")


class KbServicer(kb_pb2_grpc.KbServicer):
    def __init__(self, root=None):
        """Over the store at root; with none, a servicer that can only start a store, taking its root from the request."""
        self._store = Store(root) if root is not None else None

    def Init(self, request, context):
        if not request.actor.role:
            return kb_pb2.InitResponse(faults=[kb_pb2.Fault(
                rule="actor", message="a store can only be started under a role",
            )])
        try:
            store = Store(values.root(request.root))
        except values.Refused as refused:
            return kb_pb2.InitResponse(faults=refused.faults)
        store.start()
        metaschema = {"id": str(METASCHEMA_ID), "type": "schema", "schema_version": 1, "revision": 1, **METASCHEMA}
        path = store.save(METASCHEMA_ID, canonical.dump(canonical.order(metaschema, METASCHEMA["schema"])))
        entry = journal.write(
            store.dir, actor=request.actor, op="create", artifact=str(METASCHEMA_ID), path="",
            revision=1, schema_version=1, written=path, message="initialise store",
        )
        store.commit([store.dir / "store.yaml", path, entry], request.actor.role, "initialise store")
        return kb_pb2.InitResponse()

    def Create(self, request, context):
        creation = kb_pb2.Creation(type=request.type, title=request.title, content=request.content)
        landed = self._land([kb_pb2.Operation(create=creation)], request.actor, request.message)
        if landed.faults:
            return kb_pb2.CreateResponse(faults=landed.faults)
        return kb_pb2.CreateResponse(id=landed.results[0].id, revision=landed.results[0].revision)

    def Apply(self, request, context):
        return self._land(request.operations, request.actor, request.message)

    def _land(self, operations, actor, message) -> kb_pb2.ApplyResponse:
        """The write path. Each operation is applied in order to a draft of the store and checked there, against the
        store as the operations before it left it; only when every one passes is anything written, each artifact
        saved, one journal entry per operation naming the set, and one commit.

        A fault anywhere refuses the whole set with every fault found, and nothing is written.
        """
        draft = Draft(self._store)
        touched, faults = [], []
        for operation in operations:
            try:
                touched.append(self._apply(draft, operation))
            except values.Refused as refused:
                faults += refused.faults
        if faults:
            return kb_pb2.ApplyResponse(faults=faults)
        texts = []
        for op, artifact_id in touched:
            try:
                texts.append((op, artifact_id, canonical.dump(draft.load(artifact_id))))
            except canonical.NotCanonical as fault:
                faults.append(kb_pb2.Fault(artifact=str(artifact_id), rule="content", message=str(fault)))
        if faults:
            return kb_pb2.ApplyResponse(faults=faults)
        written, results, batch = [], [], ""
        for seq, (op, artifact_id, text) in enumerate(texts, start=1):
            artifact = draft.load(artifact_id)
            path = self._store.save(artifact_id, text)
            entry = journal.write(
                self._store.dir, actor=actor, op=op, artifact=str(artifact_id), path="",
                revision=artifact["revision"], schema_version=artifact["schema_version"],
                written=path, message=message, seq=seq, batch=batch,
            )
            batch = batch or entry.stem
            written += [path, entry]
            results.append(kb_pb2.Result(id=str(artifact_id), revision=artifact["revision"]))
        self._store.commit(written, actor.role, message)
        return kb_pb2.ApplyResponse(batch=batch, results=results)

    def _apply(self, draft: Draft, operation: kb_pb2.Operation) -> tuple[str, ArtifactId]:
        """One operation applied to the draft. Returns what it did and to which artifact; raises values.Refused."""
        if operation.WhichOneof("operation") == "create":
            return "create", self._create(draft, operation.create)
        return "write", self._replace(draft, operation.write)

    def _create(self, draft: Draft, creation: kb_pb2.Creation) -> ArtifactId:
        kind = values.kind(creation.type)
        if not draft.holds(ArtifactId(Kind("schema"), kind.name)):
            raise values.Refused([kb_pb2.Fault(
                rule="kind", message=f"a kind must name a type the store holds; the store holds no type called {kind.name!r}",
            )])
        at = f"{kind.name}/{values.slug(creation.title)}"
        faults = []
        try:
            artifact_id = values.named(kind, creation.title)
        except values.Refused as refused:
            faults += refused.faults
        try:
            content = values.content(at, creation.content)
        except values.Refused as refused:
            faults += refused.faults
        if faults:
            raise values.Refused(faults)
        schema = draft.schema(kind)
        faults = validation.validate(at, {"title": creation.title, **content}, schema["schema"], draft)
        if faults:
            raise values.Refused(faults)
        for collection in schema["schema"].get("parts", {}):
            for item in content.get(collection, []):
                item["id"] = values.slug(item["title"])
        artifact = {
            **content,
            "id": str(artifact_id), "type": kind.name,
            "schema_version": schema["version"], "revision": 1, "title": creation.title,
        }
        draft.put(artifact_id, canonical.order(artifact, schema["schema"]))
        return artifact_id

    def _replace(self, draft: Draft, replacement: kb_pb2.Replacement) -> ArtifactId:
        locator = values.locator(replacement.locator)
        content = values.content(str(locator.id), replacement.content)
        current = draft.load(locator.id)
        schema = draft.schema(locator.id.kind)
        faults = validation.validate(str(locator.id), {"title": current["title"], **content}, schema["schema"], draft)
        if faults:
            raise values.Refused(faults)
        artifact = {
            **content,
            "id": current["id"], "type": current["type"],
            "schema_version": schema["version"], "revision": current["revision"] + 1, "title": current["title"],
        }
        draft.put(locator.id, canonical.order(artifact, schema["schema"]))
        return locator.id

    def Read(self, request, context):
        try:
            locator = values.locator(request.locator)
        except values.Refused as refused:
            return kb_pb2.ReadResponse(faults=refused.faults)
        if not self._store.holds(locator.id):
            return kb_pb2.ReadResponse(faults=[kb_pb2.Fault(
                artifact=str(locator.id), rule="not-found",
                message=f"the store holds nothing by the name {str(locator.id)!r}",
            )])
        try:
            return self._summary(locator)
        except Unreadable as unreadable:
            return kb_pb2.ReadResponse(faults=[unreadable.fault])

    def _summary(self, locator):
        artifact = self._store.load(locator.id)
        schema = self._store.schema(locator.id.kind)["schema"]
        response = kb_pb2.ReadResponse(
            id=artifact["id"], type=artifact["type"],
            schema_version=artifact["schema_version"], revision=artifact["revision"],
            title=artifact["title"],
            content=dumps(_summary_fields(artifact, schema)),
        )
        for field in _reference_fields(schema):
            for target_id in _as_list(artifact.get(field)):
                response.references.append(self._stub(field, values.artifact_id(target_id)))
        for collection in schema.get("parts", {}):
            for item in artifact.get(collection, []):
                response.parts.append(kb_pb2.PartStub(collection=collection, id=item["id"], title=item["title"]))
        for (type_name, field), count in self._inbound(str(locator.id)).items():
            response.inbound.append(kb_pb2.InboundCount(type=type_name, field=field, count=count))
        return response

    def Validate(self, request, context):
        """Every artifact checked against its type; a file that cannot be read is reported and the check goes on."""
        violations = []
        for artifact_id in self._store.ids():
            try:
                artifact = self._store.load(artifact_id)
                schema = self._store.schema(artifact_id.kind)["schema"]
            except Unreadable as unreadable:
                violations.append(unreadable.fault)
                continue
            content = {key: value for key, value in artifact.items() if key not in canonical.IDENTITY[:4]}
            violations += validation.validate(str(artifact_id), content, schema, self._store)
        return kb_pb2.ValidateResponse(violations=violations)

    def _stub(self, field, target_id: ArtifactId):
        target = self._store.load(target_id)
        schema = self._store.schema(target_id.kind)["schema"]
        return kb_pb2.Stub(
            field=field, id=target["id"], type=target["type"], title=target["title"],
            fields=dumps(_summary_fields(target, schema)),
        )

    def _inbound(self, artifact_id: str):
        """How many artifacts point at this one, by their type and the field they use."""
        counts = {}
        for other in self._store.artifacts():
            schema = self._store.schema(values.kind(other["type"]))["schema"]
            for field in _reference_fields(schema):
                if artifact_id in _as_list(other.get(field)):
                    key = (other["type"], field)
                    counts[key] = counts.get(key, 0) + 1
        return counts


def _summary_fields(artifact, schema):
    return {name: artifact[name] for name in schema.get("summary", []) if name in artifact}


def _reference_fields(schema):
    return [name for name, field in schema.get("properties", {}).items() if "ref" in field]


def _as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]
```

Compared with before: `Create` is a set of one through `_land`, and `Apply` is new. The body of the old `Create` is now `_create`, checking against the draft. `_replace` is new, used by the Write operation. `Init` hands `save` the dumped text. `_identity_faults` is gone, since it is now `values.content`. `Read`, `Validate` and their helpers are unchanged.

In `src/kb/client.py`, replace everything from `    def Create(self, request, timeout=None):` up to (not including) `def connect(` with:

```python
    def _call(self, rpc: str, request, response):
        """The rpc on the store this call finds, or the response carrying the fault that says none was found."""
        servicer, refusal = self._servicer()
        if refusal is not None:
            return response(faults=[refusal])
        return getattr(servicer, rpc)(request, None)

    def Create(self, request, timeout=None):
        return self._call("Create", request, kb_pb2.CreateResponse)

    def Read(self, request, timeout=None):
        return self._call("Read", request, kb_pb2.ReadResponse)

    def Validate(self, request, timeout=None):
        return self._call("Validate", request, kb_pb2.ValidateResponse)

    def Apply(self, request, timeout=None):
        return self._call("Apply", request, kb_pb2.ApplyResponse)


```

- [ ] **Step 6: Run it green, and the suite**

```bash
.venv/bin/python -m pytest -q -m slice-5 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `1 passed, 117 deselected`; `70 failed, 48 passed`. The slices already green stay green, including 1.4's single journal entry after Init (Init still journals on its own) and 1.2 and 1.6's identity faults, which now come from `values.content`.

- [ ] **Step 7: Commit**

```bash
git add src/kb/contract src/kb/values.py src/kb/store.py src/kb/journal.py src/kb/servicer.py src/kb/client.py tests/calls.py tests/test_make_several_changes_in_one_go.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 5: several changes land as one change, named by kb

Create and Apply share one write path over a draft of the store; every
operation leaves a journal entry naming its set, and the set is one commit.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 8: Checkpoint**

Set slice 5's Status to `green`. Append at the very end of the Log:

```
- <date> slice 5 green. Someone can now: create a decision and point a work item at it in one go, be given a name for the set, a result for each change, and find the two as one commit whose journal entries name the set.
  Assumption "the second operation can point at the artifact the first creates before either lands": <held or not>. Evidence: <the two journal entries of the set, as (op, artifact, revision, batch), printed from the scenario's store>. The second operation names the decision by the name kb mints from its title, and the draft holds it when the second is checked.
  Surprised by: <nothing, or what>. (Create now leaves a journal entry, since it is a set of one; slice 9 reads them.)
  Open questions:
  - QUESTION FOR THE SPEC: a create whose title another artifact already has overwrites it (revision 1 again), alone or twice in one set; once slice 25 numbers clashes, a set's later operation naming the earlier one's artifact by its title's name lands on the older artifact without a fault. How does an operation in a set name what an earlier one creates? (Review Focus 3)
  - QUESTION FOR THE SPEC: an Apply replacing an artifact the store lacks raises FileNotFoundError through the client. Slice 23 pins it for Write. (Review Focus 2)
  - QUESTION FOR THE SPEC: the spec counts the identity keys among kb's composed JSON Schema fragments; they are checked by code at the boundary (values.content), since the title must be caught before it is merged into the tree that is validated. Is a boundary check what the spec means, or should the four keys the store settles become a fragment, changing the rule and message slices 1.2 and 1.6 pin?
  Next: slice 6.
```

Commit the plan: `Slice 5 green`.

---

### Task 4: Slice 6, a bad set changes nothing

**Slice plan entry:** Slice 6, capability. Unknown: does a refusal at the second operation leave no trace of the first, both on disk and in the store as the same client then reads it? Scenario:

1. kb / make-several-changes-in-one-go / One bad change in a set leaves the store untouched

**Files:**
- Modify: `src/kb/validation.py` (whole file: the composition walk and the required-sections rule)
- Modify: `tests/test_make_several_changes_in_one_go.py`
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `_land` and `Draft` (Task 3). `apply`, `creation` and `read` from `tests/calls.py`. The Background, `DECISION` and `SECTIONS` (Task 3). `_type_schema` and `TYPE_URI` (Task 1). Slice 3's scenario (Task 2).
- Produces: `validation.composition(schema: dict, corpus) -> list[dict]`, and the sections rule inside `validation.validate` (rule `sections`). Task 5 reads references through `composition`, and slice 25's missing-section scenario uses the rule.

- [ ] **Step 1: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-6 2>&1 | grep -E "^E |passed|failed" | tail -2
```

Expected: `1 failed`, a `StepDefinitionNotFoundError` for `Given "a set whose second change is missing a section its type requires"`.

- [ ] **Step 2: The steps**

In `tests/test_make_several_changes_in_one_go.py`, add `read` to the `from calls import …` line (after `define`), and append:

```python


def _everything_under(directory):
    """Every file below a directory, with its bytes, so a step can tell whether anything was written."""
    return {path: path.read_bytes() for path in sorted(directory.rglob("*")) if path.is_file()}


@given("a set whose second change is missing a section its type requires", target_fixture="bad_set")
def _a_set_with_a_bad_second_change():
    return [
        creation("decision", "Price reviews happen weekly", {"sections": SECTIONS}),
        creation("decision", "Prices are reviewed monthly", {"sections": []}),
    ]


@when("the client asks for the set, saying which role and why", target_fixture="attempt")
def _ask_for_the_set(root, client, bad_set):
    before = _everything_under(root)
    response = apply(client, bad_set, message="Record two decisions")
    return {"response": response, "before": before, "after": _everything_under(root)}


@then("the set is rejected because a change in it does not fit its type")
def _set_rejected(attempt):
    refused = attempt["response"]
    assert (refused.batch, list(refused.results)) == ("", [])
    assert {(fault.artifact, fault.rule) for fault in refused.faults} == {("decision/prices-are-reviewed-monthly", "sections")}


@then("the store holds neither change")
def _neither_change_held(client, attempt):
    assert attempt["after"] == attempt["before"]
    for name in (DECISION, "decision/prices-are-reviewed-monthly"):
        assert [fault.rule for fault in read(client, name).faults] == ["not-found"]


@then("every fault in the set comes back, not only the first")
def _every_fault_back(attempt):
    assert [(fault.path, fault.message) for fault in attempt["response"].faults] == [
        ("sections", "the sections the type requires must all be present, in order; 'Purpose' is missing"),
        ("sections", "the sections the type requires must all be present, in order; 'Rationale' is missing"),
    ]
```

The second change has no sections at all, so it breaks the rule twice, and "every fault" can be told from "the first".

```bash
.venv/bin/python -m pytest -q -m slice-6 2>&1 | grep -E "^E |passed|failed" | head -4
```

Expected: `AssertionError` at `(refused.batch, list(refused.results)) == ("", [])`, the batch a name like `'20260924T…Z-1'`, and `1 failed`. Without the rule, the set lands.

- [ ] **Step 3: The composition walk and the sections rule**

Replace the whole of `src/kb/validation.py` with:

```python
"""Schema validation: the type's JSON Schema composed with kb's own structural rules, checked in one pass, then
what the schema language cannot say, checked in code: required sections in their declared order.

kb's keywords are read through the type's composition, so a type built on a base carries the base's first.
"""
from jsonschema import Draft202012Validator
from referencing import Registry
from referencing.exceptions import NoSuchResource
from referencing.jsonschema import DRAFT202012

from kb import values
from kb.contract import kb_pb2
from kb.values import Kind

TYPE_URI = "kb:"

SECTION = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "body": {"type": "string"},
        "sections": {"type": "array", "items": {"$ref": "#/$defs/kb-section"}},
    },
    "required": ["title", "body"],
    "additionalProperties": False,
}

STRUCTURE = {"properties": {"sections": {"type": "array", "items": {"$ref": "#/$defs/kb-section"}}}}


def compose(schema: dict) -> dict:
    """One effective schema: the type's, with kb's structural rules beside it under allOf.

    The type stays the root, so its own `#` references still resolve; kb's shapes sit under `$defs/kb-*`.
    """
    return {
        **schema,
        "allOf": [*schema.get("allOf", []), STRUCTURE],
        "$defs": {**schema.get("$defs", {}), "kb-section": SECTION},
    }


def registry(corpus) -> Registry:
    """Every type the corpus holds, found by the URI kb:schema/<type> when a schema refers to it, and only then."""
    def retrieve(uri: str):
        return DRAFT202012.create_resource(_type_schema(uri, corpus))
    return Registry(retrieve=retrieve)


def _type_schema(uri: str, corpus) -> dict:
    """The JSON Schema of the type a kb: URI names, its name checked as any other name is. NoSuchResource if none."""
    try:
        schema_id = values.artifact_id(uri.removeprefix(TYPE_URI)) if uri.startswith(TYPE_URI) else None
    except values.Refused:
        schema_id = None
    if schema_id is None or schema_id.kind != Kind("schema") or not corpus.holds(schema_id):
        raise NoSuchResource(ref=uri)
    return corpus.load(schema_id)["schema"]


def validate(artifact_id: str, content: dict, schema: dict, corpus) -> list[kb_pb2.Fault]:
    """Every violation, as artifact, path, rule, message. A kb:schema/<type> reference resolves against the corpus.

    kb's own rules read content that fits the composed schema, so they run only when it does.
    """
    faults = [
        kb_pb2.Fault(
            artifact=artifact_id,
            path="/".join(str(step) for step in error.absolute_path),
            rule=error.validator,
            message=error.message,
        )
        for error in Draft202012Validator(compose(schema), registry=registry(corpus)).iter_errors(content)
    ]
    if faults:
        return faults
    required = [section for part in composition(schema, corpus) for section in part.get("sections", [])]
    return _sections(artifact_id, content.get("sections", []), required, "sections")


def composition(schema: dict, corpus) -> list[dict]:
    """The schema and every schema it is built on, base first: its allOf members in order, a whole type it names by
    $ref followed to that type's schema, and last the schema itself. kb's keywords are read through this list."""
    built_on = []
    for member in schema.get("allOf", []):
        built_on += composition(member, corpus)
    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith(TYPE_URI) and "#" not in ref:
        built_on += composition(_type_schema(ref, corpus), corpus)
    return [*built_on, schema]


def _sections(artifact_id: str, sections: list, required: list, place: str) -> list[kb_pb2.Fault]:
    """The required sections first, in their declared order, at every level of the tree; any others may follow.

    Each required section is looked for where the one before it left off, so one missing section is one fault.
    """
    faults, at = [], 0
    titles = [section["title"] for section in sections]
    for wanted in required:
        if titles[at:at + 1] == [wanted["title"]]:
            faults += _sections(
                artifact_id, sections[at].get("sections", []), wanted.get("sections", []), f"{place}/{at}/sections",
            )
            at += 1
            continue
        where = "is out of its place" if wanted["title"] in titles else "is missing"
        faults.append(kb_pb2.Fault(
            artifact=artifact_id, path=place, rule="sections",
            message=f"the sections the type requires must all be present, in order; {wanted['title']!r} {where}",
        ))
    return faults
```

Here the required section tree is the concatenation of every composed schema's `sections`, base first. The rule runs only on content that fits the composed schema (Decision 8). A section without a title or body therefore still gives slices 1.13 and 1.20 their one `required` fault and nothing more.

- [ ] **Step 4: Run it green, the base scenario, and the suite**

```bash
.venv/bin/python -m pytest -q -m "slice-6 or slice-3" 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `2 passed, 116 deselected`; `69 failed, 49 passed`.

Slice 3 is now the scenario that pins the merge, and its unknown can be observed. To see it, change `    return [*built_on, schema]` to `    return [schema]` and run `-m slice-3`. Expected: `1 failed` with `'Rationale' is out of its place`. Put the line back, run it again, and expect `1 passed`. Record both outputs for the checkpoint.

- [ ] **Step 5: Commit**

```bash
git add src/kb/validation.py tests/test_make_several_changes_in_one_go.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 6: a set with a change that breaks its type changes nothing

The sections a type requires, its base's first, are checked in order.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 6: Checkpoint**

Set slice 6's Status to `green`. Append at the very end of the Log:

```
- <date> slice 6 green. Someone can now: send a set whose second change lacks the sections its type requires and be refused with every fault, the store holding neither change as the same client reads it.
  Assumption "a refusal at the second operation leaves no trace of the first, on disk or as the client reads it": <held or not>. Evidence: <every file under the root byte-identical before and after, and Read of both names answering not-found>.
  Slice 3's unknown, now observable: <the output of -m slice-3 with composition returning [schema] ("'Rationale' is out of its place"), and with it restored (1 passed)>. The required section tree is the base's followed by the type's.
  Surprised by: <nothing, or what>.
  Open questions:
  - QUESTION FOR THE SPEC: kb's own rules (sections, and from slice 7 links) run only when the content fits the composed JSON Schema, so an artifact with a JSON Schema fault and a missing section reports the first only. Slices 1.13 and 1.20 pin a single fault for a section missing its title or body. Should kb's rules run alongside, "all errors found"?
  - QUESTION FOR THE SPEC: `parts` and `summary` are still read from a type's top level, not through its composition; no scenario yet has a base declaring either.
  Next: slice 7.
```

Commit the plan: `Slice 6 green`.

---

### Task 5: Slice 7, every fault at once

**Slice plan entry:** Slice 7, capability. Unknown: can violations from the JSON Schema validator and from kb's own rules be collected into one list, with the place given in the node-path form the contract uses? Scenario:

1. kb / create-an-artifact / An artifact with several faults reports them all

**Files:**
- Modify: `src/kb/validation.py` (whole file: the link rule, `references`, `links`, `_lands`)
- Modify: `src/kb/servicer.py` (`_summary` and `_inbound` use `validation.links`; `_reference_fields` and `_as_list` deleted)
- Modify: `tests/test_create_an_artifact.py`
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `validation.composition` and the sections rule (Task 4). `Draft.holds` (Task 3). In `tests/test_create_an_artifact.py`: the Background, `SECTIONS`, `request` and `_everything_under`.
- Produces: `validation.references(schema, corpus) -> dict[str, dict]`, `validation.links(artifact, schema, corpus) -> list[tuple[field, place, target]]`, and the link rule inside `validate` (rule `ref`). The Then `the store is unchanged`.

- [ ] **Step 1: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-7 2>&1 | grep -E "^E |passed|failed" | tail -2
```

Expected: `1 failed`, a `StepDefinitionNotFoundError` for `When "the client creates a decision that is missing its purpose and supersedes a decision the store does not hold, saying which role and why"`.

- [ ] **Step 2: The steps**

Append to `tests/test_create_an_artifact.py`:

```python


@when(
    "the client creates a decision that is missing its purpose and supersedes a decision the store does not hold, "
    "saying which role and why",
    target_fixture="attempt",
)
def _create_with_two_faults(client, tmp_path):
    before = _everything_under(tmp_path)
    response = request(client, "decision", "Price reviews happen weekly", {
        "supersedes": "decision/prices-are-reviewed-monthly",
        "sections": [SECTIONS[1]],
    }, message="Record it")
    return {"response": response, "before": before, "after": _everything_under(tmp_path)}


@then("the artifact is rejected with both faults, each naming the artifact, the place in it and the rule broken")
def _rejected_with_both_faults(attempt):
    refused = attempt["response"]
    assert (refused.id, refused.revision) == ("", 0)
    assert sorted((fault.artifact, fault.path, fault.rule) for fault in refused.faults) == [
        ("decision/price-reviews-happen-weekly", "sections", "sections"),
        ("decision/price-reviews-happen-weekly", "supersedes", "ref"),
    ]


@then("the store is unchanged")
def _store_unchanged(attempt):
    assert attempt["after"] == attempt["before"]
```

```bash
.venv/bin/python -m pytest -q -m slice-7 2>&1 | grep -E "^E |passed|failed" | head -4
```

Expected: `AssertionError`, `Right contains one more item: ('decision/price-reviews-happen-weekly', 'supersedes', 'ref')`, and `1 failed`. The sections fault is already there. Only one fault is reported for the missing purpose, because Task 4's rule looks for each required section where the last one left off.

- [ ] **Step 3: The link rule, and Read on the same links**

Replace the whole of `src/kb/validation.py` with:

```python
"""Schema validation: the type's JSON Schema composed with kb's own structural rules, checked in one pass, then
what the schema language cannot say, checked in code: required sections in their declared order, and links that
land on an artifact the corpus holds, of a kind the type allows.

kb's keywords are read through the type's composition, so a type built on a base carries the base's first.
"""
from jsonschema import Draft202012Validator
from referencing import Registry
from referencing.exceptions import NoSuchResource
from referencing.jsonschema import DRAFT202012

from kb import values
from kb.contract import kb_pb2
from kb.values import Kind

TYPE_URI = "kb:"

SECTION = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "body": {"type": "string"},
        "sections": {"type": "array", "items": {"$ref": "#/$defs/kb-section"}},
    },
    "required": ["title", "body"],
    "additionalProperties": False,
}

STRUCTURE = {"properties": {"sections": {"type": "array", "items": {"$ref": "#/$defs/kb-section"}}}}


def compose(schema: dict) -> dict:
    """One effective schema: the type's, with kb's structural rules beside it under allOf.

    The type stays the root, so its own `#` references still resolve; kb's shapes sit under `$defs/kb-*`.
    """
    return {
        **schema,
        "allOf": [*schema.get("allOf", []), STRUCTURE],
        "$defs": {**schema.get("$defs", {}), "kb-section": SECTION},
    }


def registry(corpus) -> Registry:
    """Every type the corpus holds, found by the URI kb:schema/<type> when a schema refers to it, and only then."""
    def retrieve(uri: str):
        return DRAFT202012.create_resource(_type_schema(uri, corpus))
    return Registry(retrieve=retrieve)


def _type_schema(uri: str, corpus) -> dict:
    """The JSON Schema of the type a kb: URI names, its name checked as any other name is. NoSuchResource if none."""
    try:
        schema_id = values.artifact_id(uri.removeprefix(TYPE_URI)) if uri.startswith(TYPE_URI) else None
    except values.Refused:
        schema_id = None
    if schema_id is None or schema_id.kind != Kind("schema") or not corpus.holds(schema_id):
        raise NoSuchResource(ref=uri)
    return corpus.load(schema_id)["schema"]


def validate(artifact_id: str, content: dict, schema: dict, corpus) -> list[kb_pb2.Fault]:
    """Every violation, as artifact, path, rule, message. A kb:schema/<type> reference resolves against the corpus.

    kb's own rules read content that fits the composed schema, so they run only when it does.
    """
    faults = [
        kb_pb2.Fault(
            artifact=artifact_id,
            path="/".join(str(step) for step in error.absolute_path),
            rule=error.validator,
            message=error.message,
        )
        for error in Draft202012Validator(compose(schema), registry=registry(corpus)).iter_errors(content)
    ]
    if faults:
        return faults
    required = [section for part in composition(schema, corpus) for section in part.get("sections", [])]
    faults = _sections(artifact_id, content.get("sections", []), required, "sections")
    allowed = references(schema, corpus)
    for field, place, target in links(content, schema, corpus):
        if not _lands(target, allowed[field]["targets"], corpus):
            faults.append(kb_pb2.Fault(
                artifact=artifact_id, path=place, rule="ref",
                message=f"a link must land on a node of a kind the type allows; {target!r} does not",
            ))
    return faults


def references(schema: dict, corpus) -> dict[str, dict]:
    """Every field that links to other artifacts, from every schema in the composition, base first, with its `ref`."""
    return {
        name: field["ref"]
        for part in composition(schema, corpus)
        for name, field in part.get("properties", {}).items()
        if "ref" in field
    }


def links(artifact: dict, schema: dict, corpus) -> list[tuple[str, str, str]]:
    """Every link an artifact carries, as the field, the place in the artifact, and the name it points at."""
    found = []
    for field in references(schema, corpus):
        value = artifact.get(field)
        if isinstance(value, list):
            found += [(field, f"{field}/{index}", target) for index, target in enumerate(value)]
        elif value is not None:
            found.append((field, field, value))
    return found


def _lands(target: str, allowed: list, corpus) -> bool:
    try:
        target_id = values.artifact_id(target)
    except values.Refused:
        return False
    return target_id.kind.name in allowed and corpus.holds(target_id)


def composition(schema: dict, corpus) -> list[dict]:
    """The schema and every schema it is built on, base first: its allOf members in order, a whole type it names by
    $ref followed to that type's schema, and last the schema itself. kb's keywords are read through this list."""
    built_on = []
    for member in schema.get("allOf", []):
        built_on += composition(member, corpus)
    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith(TYPE_URI) and "#" not in ref:
        built_on += composition(_type_schema(ref, corpus), corpus)
    return [*built_on, schema]


def _sections(artifact_id: str, sections: list, required: list, place: str) -> list[kb_pb2.Fault]:
    """The required sections first, in their declared order, at every level of the tree; any others may follow.

    Each required section is looked for where the one before it left off, so one missing section is one fault.
    """
    faults, at = [], 0
    titles = [section["title"] for section in sections]
    for wanted in required:
        if titles[at:at + 1] == [wanted["title"]]:
            faults += _sections(
                artifact_id, sections[at].get("sections", []), wanted.get("sections", []), f"{place}/{at}/sections",
            )
            at += 1
            continue
        where = "is out of its place" if wanted["title"] in titles else "is missing"
        faults.append(kb_pb2.Fault(
            artifact=artifact_id, path=place, rule="sections",
            message=f"the sections the type requires must all be present, in order; {wanted['title']!r} {where}",
        ))
    return faults
```

In `src/kb/servicer.py`, in `_summary`, replace

```python
        for field in _reference_fields(schema):
            for target_id in _as_list(artifact.get(field)):
                response.references.append(self._stub(field, values.artifact_id(target_id)))
```

with

```python
        for field, _, target in validation.links(artifact, schema, self._store):
            response.references.append(self._stub(field, values.artifact_id(target)))
```

In `_inbound`, replace

```python
            for field in _reference_fields(schema):
                if artifact_id in _as_list(other.get(field)):
                    key = (other["type"], field)
                    counts[key] = counts.get(key, 0) + 1
```

with

```python
            pointing = {field for field, _, target in validation.links(other, schema, self._store) if target == artifact_id}
            for field in pointing:
                counts[(other["type"], field)] = counts.get((other["type"], field), 0) + 1
```

and delete the functions `_reference_fields` and `_as_list` at the end of the file, so that it ends with `_summary_fields`. Read and the link rule now find links in one way, through the composition.

- [ ] **Step 4: Run it green, and the suite**

```bash
.venv/bin/python -m pytest -q -m slice-7 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `1 passed, 117 deselected`; `68 failed, 50 passed`. Slice 5 stays green because its work item points at the decision the draft already holds. The read-an-artifact scenarios of slice 1 stay green on the shared `links`.

- [ ] **Step 5: Commit**

```bash
git add src/kb/validation.py src/kb/servicer.py tests/test_create_an_artifact.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 7: a create reports every fault at once, a link that lands nowhere among them

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 6: Checkpoint**

Set slice 7's Status to `green`. Append at the very end of the Log:

```
- <date> slice 7 green. Someone can now: create a decision missing its purpose and superseding one the store lacks, and be told both, each with the artifact, the place, and the rule, with nothing written.
  Assumption "violations of JSON Schema and of kb's own rules are one list, placed by node path": <held or not>. Evidence: <the two faults as (artifact, path, rule, message)>. kb's rules join the list only when JSON Schema finds nothing (slice 6's question).
  Surprised by: <nothing, or what>.
  Open questions:
  - For slicing: slice 25's "An artifact missing a required section is refused" and "An artifact pointing at something that is not there is refused" use the rule and message built here and in slice 6, so they are expected to go green on their step definitions.
  - QUESTION FOR THE SPEC: a link to a part (`process/x#steps/draft`) never lands, even where the field's `ref` allows parts; no scenario writes one yet.
  Next: slice 8.
```

Commit the plan: `Slice 7 green`.

---

### Task 6: Slice 8, a refused change leaves the artifact as it was

**Slice plan entry:** Slice 8, capability. Unknown: after a refused write, does the store as the same client reads it (not only the files) still hold the old content at the old version? Scenario:

1. kb / change-an-artifact / A change that would break the type leaves the artifact as it was

**Files:**
- Modify: `src/kb/contract/kb.proto`, then regenerate (`make contract`)
- Modify: `src/kb/servicer.py` (new `Write`)
- Modify: `src/kb/client.py` (new `Write`)
- Modify: `tests/calls.py`, `tests/test_change_an_artifact.py`
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `_land`, `Replacement` and `_replace` (Task 3). The sections rule (Task 4). `DECISION_TYPE`, `create`, `define` and `read` from `tests/calls.py`.
- Produces: the rpc `Write(WriteRequest) returns (WriteResponse)`, `WriteRequest { locator, content, actor, message }` and `WriteResponse { revision, faults }`, `InProcessClient.Write`, `tests/calls.py:write(client, artifact_id, content, message=…)`, and the Background Given `a store holding a decision with a purpose and a rationale, at its first version`. Slices 13 and 23 build on all of these.

- [ ] **Step 1: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-8 2>&1 | grep -E "^E |passed|failed" | tail -2
```

Expected: `1 failed`, a `StepDefinitionNotFoundError` for `Given "a store holding a decision with a purpose and a rationale, at its first version"`.

- [ ] **Step 2: The steps**

Append to `tests/calls.py`:

```python


def write(client, artifact_id, content, message="Change an artifact"):
    """A Write of a whole artifact under the client's role. Returns the response, faults and all."""
    return client.Write(kb_pb2.WriteRequest(
        locator=kb_pb2.Locator(id=artifact_id), content=dumps(content), actor=CLIENT, message=message,
    ))
```

Replace the whole of `tests/test_change_an_artifact.py` with:

```python
from pytest_bdd import given, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, create, define, read, write
from kb import client as kb_client
from kb.contract import kb_pb2

scenarios("change-an-artifact.feature")

DECISION = "decision/price-reviews-happen-weekly"
SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]


@given("a store holding a decision with a purpose and a rationale, at its first version", target_fixture="client")
def _store_with_a_decision(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS})
    return client


@when("the client replaces the decision with content that has no purpose, saying which role and why", target_fixture="attempt")
def _replace_without_a_purpose(root, client):
    before = (root / "kb" / f"{DECISION}.yaml").read_bytes()
    response = write(client, DECISION, {"sections": SECTIONS[1:]}, message="Drop the purpose")
    return {"response": response, "before": before}


@then("the change is rejected because the sections the type requires must all be present, in order")
def _rejected_for_the_sections(attempt):
    refused = attempt["response"]
    assert refused.revision == 0
    assert [(fault.artifact, fault.path, fault.rule) for fault in refused.faults] == [(DECISION, "sections", "sections")]
    assert refused.faults[0].message.startswith("the sections the type requires must all be present, in order")


@then("reading the decision gives what it held before, at the version it held before")
def _as_it_was(root, client, attempt):
    assert read(client, DECISION).revision == 1
    assert (root / "kb" / f"{DECISION}.yaml").read_bytes() == attempt["before"]
```

The last Then compares the stored bytes, since a whole Read is slice 21's, and the version as Read gives it.

```bash
.venv/bin/python -m pytest -q -m slice-8 2>&1 | grep -E "^E .*Error|passed|failed"
```

Expected: `AttributeError: 'InProcessClient' object has no attribute 'Write'` and `1 failed`.

- [ ] **Step 3: The Write call**

In `src/kb/contract/kb.proto`, change

```proto
  rpc Apply(ApplyRequest) returns (ApplyResponse);
}
```

to

```proto
  rpc Write(WriteRequest) returns (WriteResponse);
  rpc Apply(ApplyRequest) returns (ApplyResponse);
}
```

and insert above the line `// One change in a set: a create or a replacement, with no role or message`:

```proto
// A new content for an artifact the store holds; its title is kept.
message WriteRequest {
  Locator locator = 1;
  string content = 2;  // canonical YAML: fields, sections, parts
  Actor actor = 3;
  string message = 4;
}

// With faults, a refusal, and the artifact is as it was.
message WriteResponse {
  int32 revision = 1;
  repeated Fault faults = 2;
}

```

Then run `make contract`.

In `src/kb/servicer.py`, insert above `    def Apply(self, request, context):`:

```python
    def Write(self, request, context):
        replacement = kb_pb2.Replacement(locator=request.locator, content=request.content)
        landed = self._land([kb_pb2.Operation(write=replacement)], request.actor, request.message)
        if landed.faults:
            return kb_pb2.WriteResponse(faults=landed.faults)
        return kb_pb2.WriteResponse(revision=landed.results[0].revision)

```

In `src/kb/client.py`, insert above `    def Apply(self, request, timeout=None):`:

```python
    def Write(self, request, timeout=None):
        return self._call("Write", request, kb_pb2.WriteResponse)

```

- [ ] **Step 4: Run it green, and the suite**

```bash
.venv/bin/python -m pytest -q -m slice-8 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
git diff --quiet HEAD -- features && echo "features untouched"
```

Expected: `1 passed, 117 deselected`; `67 failed, 51 passed`; `features untouched`.

- [ ] **Step 5: Commit**

```bash
git add src/kb/contract src/kb/servicer.py src/kb/client.py tests/calls.py tests/test_change_an_artifact.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 8: a change that breaks the type leaves the artifact as it was

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 6: Checkpoint**

Set slice 8's Status to `green`. Append at the very end of the Log:

```
- <date> slice 8 green. Someone can now: replace a decision, and when the new content lacks its purpose be refused, reading the decision back as it was at the version it was.
  Assumption "after a refused write the store as the client reads it still holds the old content at the old version": <held or not>. Evidence: <read(...).revision and the stored file's bytes before and after>.
  Surprised by: <nothing, or what>.
  Open questions:
  - QUESTION FOR THE SPEC: a Write whose locator names a node inside the artifact (path "sections/rationale") replaces the whole artifact with the content given; slice 13 builds node writes. Until then, should a path be refused? (Review Focus 1)
  - QUESTION FOR THE SPEC: a Write of a name the store lacks raises FileNotFoundError through the client; slice 23 pins the refusal. (Review Focus 2)
  - QUESTION FOR THE SPEC: a Write to an artifact whose stored file cannot be read raises store.Unreadable through the client, where Read answers with the fault. (Review Focus 5)
  Next: slice 9.
```

Commit the plan: `Slice 8 green`.

---

## After slice 8

Not a slice. Run the whole-batch review over the commits of Tasks 1 to 6: `superpowers:requesting-code-review`, with this plan and the spec as the brief. Every finding goes to `slicing-into-increments`. That skill places it by its unknown among the slices not yet begun, and it is never coded here. The next batch starts at slice 9, whose clock control is its unknown.
