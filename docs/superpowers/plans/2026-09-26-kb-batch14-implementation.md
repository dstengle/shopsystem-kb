# kb Batch 14 Implementation Plan: slice 89.2, the links out of one place

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Each task is one slice of `docs/superpowers/plans/2026-09-24-kb-slices.md`. The one task here is a capability slice, written red-green against its one scenario (shopsystem-bdd:bdd-red-green).

**Goal:** The last slice the plan holds:
- Follow the links out of one place (slice 89.2, capability): kb / follow-the-links / The client follows the links out of one place inside an artifact, re-formulated with the user's approval on 2026-09-26 (commit `841a506`) so that the place is a step of a process.

**Architecture:** kb is the Python package `kb` in `/home/vscode/shopsystem-kb`. A protobuf contract (`kb.contract`) sits in front of `KbServicer` (`servicer.py`), whose every rpc runs inside one boundary that turns `values.Refused` into that rpc's faults. `Refs` already takes a `Locator`, a name and a place (`path`), and `requests.walk` already converts both into `values.Locator(id, place)`; but `query.walk` reads only `locator.id`, so today a traversal from a step answers with every link the whole process carries. The place a traversal starts at is a step of a process, a part, and three modules already own how a place and its links are read. This plan asks each of them for its own part once, and adds no second reading:
- **places.py resolves a place (the module map).** A new `places.node(content, locator)` says what stands at the locator's place: the content itself for no place, otherwise the item, the section or the field's value there. It goes through `places.resolve`, so a place the artifact holds nothing at is refused with the fault `resolve` already gives (`not-found`, and `identity` for a place beginning at what only the store settles), exactly as a read of that place is.
- **links.py is the one reading of links (the module map).** A new `links.inside(artifact, schema, corpus, node)` gives the links an artifact carries in one node of it and in the items inside that node, found by the walk `links.carried` already makes, so each `Link` keeps the place, `ref` and `own` it has today. `links.carried` becomes `inside` at the artifact itself; its callers do not change.
- **query.py walks.** `query.walk` starts its frontier at the locator asked for instead of its name. `_outward` takes a `Locator` and reads `links.inside` at `places.node`; every later step starts at an artifact whole (`Locator(other_id, ())`). `_inward` takes a `Locator` and reads its name only.
- **Fail-closed boundary (rule 1).** No rpc gains a `try`; nothing here catches anything. A bad place reaches the boundary as the `Refused` `places.resolve` raises.
- **Parse, don't validate (rule 2).** The place arrives already converted in `Walk.locator`; nothing here reads the request's `path` text.

**Provenance:** Every code block here was assembled in a scratch clone of this repository (`/tmp/kb14`, cloned at `20d8bbf`, run with this checkout's `.venv` and `PYTHONPATH=/tmp/kb14/src`) on 2026-09-26, red then green, and the task applied in one commit. The red failure, the suite counts, the probe before and after, the greps and the line counts are what that run gave. This repository was not touched except to write this plan and the slice plan's entries. The plan was then replayed from its text alone, in the foreground of the same session, in a second clone (see the end of this file).

**Tech Stack:** Python 3.11, setuptools (src layout), protobuf + grpcio (generated code committed; no `.proto` change in this batch), python-jsonschema 4.26 with `referencing`, ruamel.yaml 0.19 (YAML 1.2), git via subprocess, pytest 9 + pytest-bdd 8.

**Spec:** `docs/superpowers/specs/2026-09-23-kb-design.md` (`Refs` takes a locator, direction, optional via-field, optional type and depth, and answers stubs with the path taken; a place is parts of the plain alphabet, or a collection name followed by an item id). The slice plan is `docs/superpowers/plans/2026-09-24-kb-slices.md` (slice 89.2 and the log entry of the approved re-formulation), and the scenario is in `features/follow-the-links.feature`, tagged `@slice-89.2`. `CLAUDE.md` at the repository root is binding.

## Global Constraints

- Feature files are read-only for the implementer. Any diff under `features/` is a stop condition; this batch touches none.
- Code is written red-green against the one scenario, and adds no behaviour it does not ask for. What this plan does for places other than a step (below, Review Focus) follows from asking `places.py` and `links.py` their own questions and is pinned by the probe, never by a new scenario or a new refusal.
- **CLAUDE.md's rules are implemented once.** No rpc in `servicer.py` gains a `try` (`grep -c "try:" src/kb/servicer.py` stays `1`). No module catches a broad exception (`grep -nE "except (Exception|BaseException)|except:" src/kb/*.py` prints nothing). No module but `places.py` walks a place; no module but `links.py` builds a `Link` (`grep -rn "Link(" src/kb/` shows `links.py` only).
- **Size.** No module over 250 lines; `servicer.py` under 150. After the task `query.py` is 141 lines, `links.py` 71 and `places.py` 75. `values.py` stays 241 and is not touched.
- Tests use the contract or a module's public functions, never private helpers. The step definitions call the contract through `tests/calls.py`.
- `make test` runs the suite in this checkout's virtualenv (`.venv/bin/python -m pytest -q`). While any scenario is red, make's own error line comes last, so the steps run pytest directly to see the summary. A worktree needs its own `.venv` first (`make dev`).
- The contract's version stays `0.1`; `pyproject.toml` stays `0.2.0` (tagged `v0.2.0` at `20d8bbf`).
- Work on `main` in `/home/vscode/shopsystem-kb`.
- Commits: `git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit`, the message ending with the Co-Authored-By line of the model that made the commit, e.g. `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- The suite prints pytest-bdd `PytestRemovedIn10Warning`s. That is the baseline, not a fault. The summary lines quoted as Expected leave out the `, N warnings in Xs` that pytest adds.
- Baseline before Task 1: `.venv/bin/python -m pytest -q` → `1 failed, 195 passed`, the one failure slice 89.2's (`tests/test_follow_the_links.py::test_the_client_follows_the_links_out_of_one_place_inside_an_artifact`, `StepDefinitionNotFoundError` on its Given). After Task 1: `196 passed`.
- A probe is a Python script run with `.venv/bin/python` from the repository root, given in full in the task, that drives the in-process client over a store in a temporary directory. Save it under `/tmp`, run it before the change and after, and compare with the lines given.

## Decisions this plan makes

1. **What the start's links are.** The links in the node at the place and in every item inside that node, at any depth, each as `links.carried` finds it. A step's own `uses` is the scenario's; a step's sub-items, should a type declare them, are inside the step and so are followed from it.
2. **How links.py knows the node.** By identity: `places.node` hands back the very dict the artifact holds at the place, and `links._links_in` starts reading a node's fields once it meets that dict, or a node it sits inside. No place is translated from names (`steps/unlock-the-door`) into the indexes a `Link`'s place is written with (`steps/0/uses`), so neither module learns the other's form. `places.node` and `links.inside` are given the same loaded artifact in `query._outward`.
3. **`links.inside` is a function of its own**, not an optional argument of `links.carried`. `places.node` can answer `None` (a field the item there does not hold), and no value of `node` may mean "the whole artifact" but the artifact itself.
4. **Only the first step starts at a place.** Every artifact reached is walked whole on the next step, as today; the route keeps the field and the name of each hop, as today.
5. **Going in, the place is not asked.** `_inward` reads `locator.id` only, so a traversal into a step answers what it answers into the whole artifact, as today, and a place the artifact lacks is not refused going in. No scenario asks otherwise; it is a question for the spec (Review Focus 3).
6. **The Given widens the process type in its own step.** It deep-copies `calls.PROCESS_TYPE` and lets a step's `uses` point at a tag or a decision; `calls.PROCESS_TYPE` stays as it is, since slice 72's scenario and others define it. The tag of the step's own is `tag/opening`, a tag nothing else in the Background points at; the other step points at the Background's decision.
7. **`calls.refs` gains `place=""`**, sent as the locator's `path`. Every existing call leaves it empty and sends what it sends today.

## Review Focus

Five inputs the scenario does not exercise, most likely to bite first. Each answer is what the scratch run gave, pinned by the probe in Task 1 (Steps 3 and 7); lines 1 to 3 are logged as QUESTIONS FOR THE SPEC in the slice plan's log, never code in this plan.

1. **A place naming a field of a step** (`steps/unlock-the-door/uses`): answers nothing, where a reasonable client would expect the tag in that field. A field's value is not a node (Decision 2). Question for the spec.
2. **A place naming a whole collection** (`steps`): answers nothing, where a client might expect what every step points at. Question for the spec.
3. **Going in from a place** (`steps/check-the-prices`, inward): answers every artifact pointing anywhere into the process, here the work item pointing at the other step; a place the process lacks is not refused going in. Question for the spec (Decision 5).
4. **A place the artifact holds nothing at, going out** (`steps/close-up`): refused, one fault, path `steps/close-up`, rule `not-found`; a place beginning at a settled key (`id`): rule `identity`. Today both answer every link the process carries.
5. **A place in a decision** (`sections/rationale`): answers nothing, since a section carries no link; and a traversal two steps out of a place walks each artifact it reaches whole (the probe runs at depth 2).

---

### Task 1: Slice 89.2, follow the links out of one place

**Slice plan entry:** Slice 89.2, capability. Scenario: kb / follow-the-links / The client follows the links out of one place inside an artifact. Observable: a client following the links out of one step of a process gets only the tag that step points at, not the decision another step points at. Needs: slice 65's resolution of a place.

**Files:**
- Modify: `tests/calls.py` (`refs` gains `place`)
- Modify: `tests/test_follow_the_links.py` (the scenario's three steps)
- Modify: `src/kb/places.py` (`node`)
- Modify: `src/kb/links.py` (`inside`; `carried` through it; `_links_in` split, `_fields` from it)
- Modify: `src/kb/query.py` (`walk` starts at the locator; `_outward` and `_inward` take a `Locator`)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint, status)

**Interfaces:**
- Consumes: `places.resolve(content: dict, locator: Locator) -> Spot` (raises `Refused`), `places.Spot(holder, key, collection)`; `links.carried(artifact, schema, corpus) -> list[Link]`; `requests.Walk.locator: values.Locator(id: ArtifactId, place: tuple[str, ...])`.
- Produces: `places.node(content: dict, locator: Locator)` → the content for no place, else `spot.holder[spot.key]` for an item or `spot.holder.get(spot.key)` for a field or section; raises `Refused` as `resolve` does. `links.inside(artifact: dict, schema: dict, corpus, node) -> list[Link]`. `links.carried` unchanged in signature and answer. In tests, `calls.refs(client, artifact_id, depth, inward=False, via="", type_name="", place="")`.

- [ ] **Step 1: Save the failing ids**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
cat /tmp/failing-before
```

Expected: the one line `FAILED tests/test_follow_the_links.py::test_the_client_follows_the_links_out_of_one_place_inside_an_artifact`.

- [ ] **Step 2: Write the scenario's steps**

In `tests/calls.py`, replace:

```python
def refs(client, artifact_id, depth, inward=False, via="", type_name=""):
    """The links out of an artifact, or into it when inward, followed as many steps as depth says, through the field
    via names and to artifacts of the kind type_name names when either is given."""
    direction = kb_pb2.RefsRequest.IN if inward else kb_pb2.RefsRequest.OUT
    return client.Refs(kb_pb2.RefsRequest(
        locator=kb_pb2.Locator(id=artifact_id), depth=depth, direction=direction, via=via, type=type_name,
    ))
```

with:

```python
def refs(client, artifact_id, depth, inward=False, via="", type_name="", place=""):
    """The links out of an artifact, or out of the place inside it place names, or into it when inward, followed as
    many steps as depth says, through the field via names and to artifacts of the kind type_name names when either is
    given."""
    direction = kb_pb2.RefsRequest.IN if inward else kb_pb2.RefsRequest.OUT
    return client.Refs(kb_pb2.RefsRequest(
        locator=kb_pb2.Locator(id=artifact_id, path=place), depth=depth, direction=direction, via=via, type=type_name,
    ))
```

Append to `tests/test_follow_the_links.py` (it already imports `copy`, `PROCESS_TYPE`, `create`, `define`, `refs`, and defines `DECISION` and `PROCESS`):

```python


OPENING = "tag/opening"


@given("a process one of whose steps points at a tag of its own, while another of its steps points at the decision")
def _a_process_whose_steps_point_out(client):
    process_type = copy.deepcopy(PROCESS_TYPE)
    process_type["schema"]["parts"]["steps"]["items"]["properties"]["uses"]["ref"]["targets"] = ["tag", "decision"]
    define(client, process_type)
    create(client, "tag", {"title": "opening"})
    create(client, "process", {"title": "Open the shop", "steps": [
        {"title": "Unlock the door", "uses": OPENING},
        {"title": "Check the prices", "uses": DECISION},
    ]})


@when("the client follows the links out of that step of the process", target_fixture="reached")
def _follow_out_of_a_step(client):
    response = refs(client, PROCESS, depth=1, place="steps/unlock-the-door")
    assert not response.faults, response.faults
    return list(response.reached)


@then("the client is given a stub of that tag and nothing else the process points at")
def _only_the_tag(reached):
    assert [(found.stub.field, found.stub.id, found.stub.type, found.stub.title) for found in reached] == [
        ("uses", OPENING, "tag", "opening"),
    ]
    assert [[(hop.field, hop.id) for hop in found.route] for found in reached] == [[("uses", OPENING)]]
```

(The file ends with the `_a_work_item_pointing_twice` step; the block starts with the two blank lines that separate it.)

- [ ] **Step 3: Run it red, and save the probe's answers**

```bash
.venv/bin/python -m pytest -q tests/test_follow_the_links.py 2>&1 | grep -E "^E |passed|failed"
```

Expected: `1 failed, 5 passed`, the failure the Then's first assertion, its `E` lines ending in

```
E         Left contains one more item: ('uses', 'decision/price-reviews-happen-weekly', 'decision', 'Price reviews happen weekly')
```

The walk answers every link the process carries: that is the red this slice turns green. A `StepDefinitionNotFoundError` instead means a step's text was mistyped.

Save this probe as `/tmp/probe-89-2.py`:

```python
"""Slice 89.2's probe: the links out of a process, whole and from places inside it, and into it from a place."""
import copy, pathlib, sys, tempfile

sys.path.insert(0, "tests")
from calls import CLIENT, DECISION_TYPE, PROCESS_TYPE, TAG_TYPE, WORK_ITEM_TYPE, create, define, refs
from kb import client as kb_client
from kb.contract import kb_pb2

root = pathlib.Path(tempfile.mkdtemp())
client = kb_client.connect(root)
client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
process_type = copy.deepcopy(PROCESS_TYPE)
process_type["schema"]["parts"]["steps"]["items"]["properties"]["uses"]["ref"]["targets"] = ["tag", "decision"]
work_item_type = copy.deepcopy(WORK_ITEM_TYPE)
work_item_type["schema"]["properties"]["decisions"]["ref"].update(targets=["decision", "process"], parts=True)
for type_content in (TAG_TYPE, DECISION_TYPE, process_type, work_item_type):
    define(client, type_content)
create(client, "tag", {"title": "opening"})
create(client, "decision", {"title": "D one", "sections": [{"title": "Purpose", "body": "a\n"}, {"title": "Rationale", "body": "b\n"}]})
create(client, "process", {"title": "Open the shop", "steps": [
    {"title": "Unlock the door", "uses": "tag/opening"}, {"title": "Check the prices", "uses": "decision/d-one"},
]})
create(client, "work-item", {"title": "W", "decisions": ["process/open-the-shop#steps/unlock-the-door"]})
for label, artifact_id, place, inward in [
    ("whole", "process/open-the-shop", "", False),
    ("one step", "process/open-the-shop", "steps/unlock-the-door", False),
    ("a step's field", "process/open-the-shop", "steps/unlock-the-door/uses", False),
    ("a field no step holds", "process/open-the-shop", "steps/unlock-the-door/branches", False),
    ("the collection", "process/open-the-shop", "steps", False),
    ("a step it lacks", "process/open-the-shop", "steps/close-up", False),
    ("a settled place", "process/open-the-shop", "id", False),
    ("a section", "decision/d-one", "sections/rationale", False),
    ("into a step", "process/open-the-shop", "steps/check-the-prices", True),
]:
    response = refs(client, artifact_id, depth=2, inward=inward, place=place)
    print(label, "->", [found.stub.id for found in response.reached], [(fault.path, fault.rule) for fault in response.faults])
```

```bash
.venv/bin/python /tmp/probe-89-2.py | tee /tmp/probe-89-2-before.txt
```

Expected (every place going out ignored today):

```
whole -> ['tag/opening', 'decision/d-one'] []
one step -> ['tag/opening', 'decision/d-one'] []
a step's field -> ['tag/opening', 'decision/d-one'] []
a field no step holds -> ['tag/opening', 'decision/d-one'] []
the collection -> ['tag/opening', 'decision/d-one'] []
a step it lacks -> ['tag/opening', 'decision/d-one'] []
a settled place -> ['tag/opening', 'decision/d-one'] []
a section -> [] []
into a step -> ['work-item/w'] []
```

- [ ] **Step 4: What stands at a place, in places.py**

In `src/kb/places.py`, insert between `resolve` and `holds_part`, that is, replace:

```python
def holds_part(content: dict, place: tuple) -> bool:
```

with:

```python
def node(content: dict, locator: Locator):
    """What stands at the locator's place in an artifact's content: the content itself for no place, otherwise the
    item, the section or the field's value there, None for a field the node there does not hold. Raises Refused as
    resolve does."""
    if not locator.place:
        return content
    spot = resolve(content, locator)
    return spot.holder[spot.key] if spot.collection else spot.holder.get(spot.key)


def holds_part(content: dict, place: tuple) -> bool:
```

An item's `Spot` names its collection and its index in that collection's list; any other `Spot` has an empty collection, its holder the artifact or an item (a dict) and its key the field or section name, which `resolve` does not require to be there.

- [ ] **Step 5: The links inside one node, in links.py**

In `src/kb/links.py`, replace:

```python
def carried(artifact: dict, schema: dict, corpus) -> list[Link]:
    """Every link an artifact carries, wherever it sits: in its own fields, and in the fields of each item of each of
    its collections, at every depth."""
    return _links_in(artifact, references(schema, corpus), declared(schema, corpus)["parts"], "", corpus)


def _links_in(node: dict, refs: dict[str, dict], parts: dict, at: str, corpus) -> list[Link]:
    """The links in one node, an artifact or an item, its place in the artifact before each of theirs."""
    found = []
    for field, ref in refs.items():
        value = node.get(field)
        if isinstance(value, list):
            found += [Link(field, f"{at}{field}/{index}", target, ref, not at) for index, target in enumerate(value)]
        elif value is not None:
            found.append(Link(field, f"{at}{field}", value, ref, not at))
    for collection, part in parts.items():
```

with:

```python
def carried(artifact: dict, schema: dict, corpus) -> list[Link]:
    """Every link an artifact carries, wherever it sits: in its own fields, and in the fields of each item of each of
    its collections, at every depth."""
    return inside(artifact, schema, corpus, artifact)


def inside(artifact: dict, schema: dict, corpus, node) -> list[Link]:
    """The links an artifact carries in one node of it, as `places.node` finds it, and in the items inside that node:
    all of them for the artifact itself, none for a field's value, which is not a node."""
    return _links_in(artifact, references(schema, corpus), declared(schema, corpus)["parts"], "", corpus, node, False)


def _links_in(node: dict, refs: dict[str, dict], parts: dict, at: str, corpus, within, entered: bool) -> list[Link]:
    """The links in one node, an artifact or an item, and in the items inside it, its place in the artifact before each
    of theirs; a node's own fields are read only once within, or a node it sits inside, has been entered."""
    entered = entered or node is within
    found = _fields(node, refs, at) if entered else []
    for collection, part in parts.items():
```

and, at the end of `_links_in`, replace:

```python
                found += _links_in(item, item_refs, declared(item_schema, corpus)["parts"], f"{at}{collection}/{index}/", corpus)
    return found
```

with:

```python
                found += _links_in(
                    item, item_refs, declared(item_schema, corpus)["parts"], f"{at}{collection}/{index}/", corpus,
                    within, entered,
                )
    return found


def _fields(node: dict, refs: dict[str, dict], at: str) -> list[Link]:
    """The links in a node's own fields, each alone or in a list."""
    found = []
    for field, ref in refs.items():
        value = node.get(field)
        if isinstance(value, list):
            found += [Link(field, f"{at}{field}/{index}", target, ref, not at) for index, target in enumerate(value)]
        elif value is not None:
            found.append(Link(field, f"{at}{field}", value, ref, not at))
    return found
```

`carried` gives exactly what it gave before: the artifact is `within`, so every node is entered from the start. `points_at` stays after `_fields`.

- [ ] **Step 6: The walk starts at the locator, in query.py**

In `src/kb/query.py`, replace the two imports:

```python
from kb import composition, journal, links, read, refusals, search, values
```

```python
from kb.values import ArtifactId, Refused
```

with:

```python
from kb import composition, journal, links, places, read, refusals, search, values
```

```python
from kb.values import ArtifactId, Locator, Refused
```

In `walk`, replace the docstring:

```python
    """What an artifact's links reach, out of it or into it, a step at a time out to the depth asked: each artifact
    once, by the shortest route, the one asked about never. A via or a type narrows every step. Raises Refused for
    a kind the store holds no type for, or a name the store lacks."""
```

with:

```python
    """What an artifact's links reach, out of it, or out of the place inside it the locator names, or into it, a step at
    a time out to the depth asked: each artifact once, by the shortest route, the one asked about never. A via or a
    type narrows every step. Raises Refused for a kind the store holds no type for, a name the store lacks, or, going
    out, a place it holds nothing at."""
```

then replace:

```python
    reached, seen, frontier = [], {str(start)}, [(start, [])]
```

with:

```python
    reached, seen, frontier = [], {str(start)}, [(asked.locator, [])]
```

replace:

```python
        for artifact_id, route in frontier:
            for field, other_id in step(store, artifact_id):
```

with:

```python
        for locator, route in frontier:
            for field, other_id in step(store, locator):
```

and replace:

```python
                following.append((other_id, taken))
```

with:

```python
                following.append((Locator(other_id, ()), taken))
```

Then replace:

```python
def _outward(store: Store, artifact_id: ArtifactId) -> list[tuple[str, ArtifactId]]:
    """Each link out of an artifact, as the field and the name it points at."""
    artifact = store.artifact(artifact_id)
    schema = composition.kind_schema(artifact_id.kind, store)["schema"]
    return [(link.field, values.artifact_id(link.target)) for link in links.carried(artifact, schema, store)]


def _inward(store: Store, artifact_id: ArtifactId) -> list[tuple[str, ArtifactId]]:
    """Each link into an artifact or a part inside it, as the field that points there and the artifact that holds
    that field, in path order."""
    pointing = []
```

with:

```python
def _outward(store: Store, locator: Locator) -> list[tuple[str, ArtifactId]]:
    """Each link out of an artifact, or out of the place inside it the locator names, as the field and the name it
    points at."""
    artifact = store.artifact(locator.id)
    schema = composition.kind_schema(locator.id.kind, store)["schema"]
    found = links.inside(artifact, schema, store, places.node(artifact, locator))
    return [(link.field, values.artifact_id(link.target)) for link in found]


def _inward(store: Store, locator: Locator) -> list[tuple[str, ArtifactId]]:
    """Each link into an artifact or a part inside it, as the field that points there and the artifact that holds
    that field, in path order. The place the locator names, if any, is not asked."""
    artifact_id = locator.id
    pointing = []
```

The rest of `_inward` is unchanged; it still uses `artifact_id`. `ArtifactId` is still imported for the return annotations.

- [ ] **Step 7: Check**

```bash
.venv/bin/python -m pytest -q tests/test_follow_the_links.py 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python /tmp/probe-89-2.py | tee /tmp/probe-89-2-after.txt
grep -c "try:" src/kb/servicer.py
grep -nE "except (Exception|BaseException)|except:" src/kb/*.py
grep -rn "Link(" src/kb/
git status --porcelain features/
wc -l src/kb/query.py src/kb/links.py src/kb/places.py
```

Expected: `6 passed`; `196 passed`; the probe prints

```
whole -> ['tag/opening', 'decision/d-one'] []
one step -> ['tag/opening'] []
a step's field -> [] []
a field no step holds -> [] []
the collection -> [] []
a step it lacks -> [] [('steps/close-up', 'not-found')]
a settled place -> [] [('id', 'identity')]
a section -> [] []
into a step -> ['work-item/w'] []
```

(against `/tmp/probe-89-2-before.txt`, the lines `whole`, `a section` and `into a step` unchanged, every other place going out now read); `1`; nothing; three lines, all in `src/kb/links.py` (the class and the two constructions in `_fields`); nothing; `141`, `71` and `75`.

- [ ] **Step 8: Checkpoint and commit**

In the slice plan, set slice 89.2's Status to `green`. Append the slice 89.2 checkpoint to its log, in the shape of slice 95.1's: slice 89.2 green (capability; kb / follow-the-links / The client follows the links out of one place inside an artifact); what a client can now rely on (Refs out of a place inside an artifact follows only the links in the node there and in the items inside it; a place the artifact holds nothing at is refused going out as a read of it is; the next step walks each artifact reached whole); what someone reading the code can rely on (`places.node` says what stands at a place, `links.inside` reads the links in one node, `links.carried` is `inside` at the artifact); surprised by; the check (red on the Then's first assertion, the decision too; `196 passed` after; the probe's lines before and after; the greps; the line counts); open questions: the three QUESTIONS FOR THE SPEC this plan logged (a field's place, a collection's place, a place going in). Then append the batch line: slice 89.2 green; suite 196 passed; every slice in the plan is green, leaving the questions for the spec.

```bash
git add tests/calls.py tests/test_follow_the_links.py src/kb docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 89.2: Follow the links out of one place

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Replay

Replayed from this file's text alone, in the foreground of the session that wrote it, in a second clone (`/tmp/kb14-replay`, from `20d8bbf`, `PYTHONPATH=/tmp/kb14-replay/src`, this checkout's `.venv`): the probe, the step definitions and every replacement taken verbatim from Task 1's code blocks by their place in it, each old text found exactly once, every command run as written. Every Expected held: the one failing id saved before; after Step 2, `1 failed, 5 passed` in the feature's tests, the Then's first assertion failing on the decision; the probe's nine lines before; after Steps 4 to 6, `6 passed` and `196 passed`, the probe's nine lines after, `1` `try:` in `servicer.py`, no broad `except`, the three `Link(` lines all in `links.py`, nothing under `features/`, and `141`, `71` and `75` lines. The replayed `src/` and `tests/` are identical to the scratch run's (`diff -r`, no output). The replay found no fault in this text; the one slip was the replaying script's own (it read Step 6's four import blocks as two pairs, where the text gives both olds and then both news, and it compared Step 3's probe against the wrong block), and the text needed no change.
