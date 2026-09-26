# kb Refactor Implementation Plan: slices 53 to 62

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Each task is one enabling slice of `docs/superpowers/plans/2026-09-24-kb-slices.md`. None adds or changes a scenario, and no file under `features/` or `tests/` changes. A slice's check is its red and its green. If a check cannot be met without changing what a client gets, stop, write a HAND-BACK entry in the slice plan's log, and hand the slice back to `shopsystem-bdd:slicing-into-increments`.

**Goal:** Bring `src/kb/` into the shape `CLAUDE.md` states, with no change in behaviour:
- the suite gives the same answer on every run;
- every request field is a value before the domain sees it;
- names are decided in one module;
- the write pipeline, reads and queries each have a module of their own;
- nothing is read from disk once a set starts writing;
- the servicer is a 101-line adapter with one boundary.

**Architecture:** kb is the Python package `kb` in `/home/vscode/shopsystem-kb`. A protobuf contract (`kb.contract`) sits in front of `KbServicer` (`src/kb/servicer.py`, 597 lines today), which holds the whole domain over a `Store` (`src/kb/store.py`): one canonical YAML file per artifact under `<root>/kb/`, itself a git repository. This plan moves the domain out, one slice at a time, into:
- `requests.py`: each rpc's request as values;
- `names.py`: names;
- `write.py`: the pipeline, starting a store, recording a snapshot;
- `edits.py`: what each operation does to the draft;
- `refusals.py`: the domain's faults;
- `read.py`: reads and stubs;
- `query.py`: list, refs, search, journal, and what a snapshot read;
- `validation.check`: the whole-store check.

Discovery joins `store.py`. Each task's code is given as the exact patch, since a refactor is mostly moved lines and a patch is the least ambiguous way to say which. Apply it with `git apply`, or by hand from the hunks.

**Tech Stack:** Python 3.11, setuptools (src layout), protobuf + grpcio (generated code committed), python-jsonschema 4.26 with `referencing`, ruamel.yaml 0.19 (YAML 1.2), git via subprocess, pytest 9 + pytest-bdd 8.

**Spec:** `CLAUDE.md` (the module map, the six rules, the size limits) and the slice plan `docs/superpowers/plans/2026-09-24-kb-slices.md`: slices 53 to 62, and the log entries of 2026-09-26, which hold architecture review 1. The behaviour every task must keep is the kb design spec's, `docs/superpowers/specs/2026-09-23-kb-design.md`, as the 118 scenarios in `features/` pin it.

**Provenance:** Every patch here was made in a scratch clone of this repository (`/tmp/refactor/kb`, cloned at `f3c469d`) on 2026-09-26, with its own `.venv` from `make dev`, and the tasks were applied in order. Each task's patch is `git diff` of that task's scratch commit, byte for byte. Every red and green result below is what those runs gave, including ten consecutive green runs after the last task, and each slice's probe output was compared with the baseline's. The plan was then replayed from its own text on a fresh clone (`/tmp/replay/kb`, at `f3c469d`, its own `.venv`), with each probe, patch and command extracted from this file. Every patch applied, every green matched, the probe gave the diffs stated, and the replay's `src/` was identical to the scratch run's. Four red expectations and one apply warning were corrected from that run. This repository was not touched except to log the review and to write this plan.

## Global Constraints

- No module under `src/kb/` over 250 lines; `servicer.py` under 150 (`CLAUDE.md`, Size and shape). Generated code under `src/kb/contract/` is exempt.
- No file under `features/` changes, and no scenario is added (the user's instruction for these slices).
- No file under `tests/` changes: tests use the contract or a module's public functions (`CLAUDE.md`), and those stay as they are.
- `make test` runs the suite in this checkout's virtualenv; every task ends `118 passed`.
- No module but `servicer.py` catches broad exceptions (`CLAUDE.md` rule 1). The domain's `except Refused` and `except Unreadable` are specific and stay.
- All YAML is 1.2 through `kb.canonical` (`CLAUDE.md` rule 5); no task touches `canonical.py`.
- Commit with `git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit`, the message ending with the line `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

The suite cannot see these, since no scenario covers them and none may be added. Each is pinned instead by the probe in "Before task 1", which every task runs and compares:
1. **A set removing an unreadable artifact.** `Apply [write tag/a, delete tag/b]` with `tag/b`'s file broken raises `Unreadable` through the client before and after. Before task 5 (slice 57) it also rewrote `tag/a` and left a journal entry uncommitted; from task 5 on it writes nothing first (batch 5's Critical, half fixed: the raise itself awaits a scenario). This is the one line where the probe's output may change, and only in task 5: `tag/a unchanged on disk False` becomes `True`, and the file count goes from 14 to 13.
2. **The order and number of a mixed set's faults** (task 2): a kind with no type, a name that is not plain, a title that leaves no name with content that cannot be read, a name clash with identity keys, and a kind that is not plain, all in one Apply, answer the same faults in the same order.
3. **A taken title with content that does not fit** (task 2): the content's fault names the numbered name (`decision/close-early-2`), which only the draft can know.
4. **A root named relatively** (task 7): each refusal quotes the root exactly as named (`'./nope'`, `'./s/inner'`).
5. **A fingerprint of prose that is not ASCII** (task 5): the journal's fingerprint, now taken from the text before it is written, equals sha256 of the file's bytes. This holds where Python's default encoding is UTF-8, as in this checkout's container, because `Store.save` writes with `write_text` and the fingerprint encodes UTF-8.

---

## Before task 1: the probe

- [ ] **Step 1: Save the probe**

Save this as `/tmp/kb-probe.py`. It is not part of the repository.

```python
"""Edge cases no scenario covers, run through the in-process client; prints each answer, or the exception it raised,
and what the store holds after. Run from a checkout's root with its .venv: output must not change across a refactor."""
import hashlib, os, re, sys, tempfile
from pathlib import Path

sys.path.insert(0, "tests")
from calls import DECISION_TYPE, TAG_TYPE, tagged_decision_type  # noqa: E402
from kb import client as kb_client  # noqa: E402
from kb.content import dumps  # noqa: E402
from kb.contract import kb_pb2  # noqa: E402

ME = kb_pb2.Actor(role="probe", execution="run-1")


def say(*parts):
    line = " ".join(str(part) for part in parts)
    print(re.sub(r"\d{8}T\d{12}Z-\d+", "STAMP", line.replace(str(work), "WORK")))


def show(label, call):
    try:
        answer = call()
        faults = [(f.artifact, f.path, f.rule, f.message) for f in getattr(answer, "faults", [])]
        say(label, "faults" if faults else "ok", faults or str(answer).replace("\n", " "))
    except Exception as error:
        say(label, "raised", type(error).__name__)


def files(root):
    return sorted(str(p.relative_to(root)) for p in (root / "kb").rglob("*") if p.is_file() and ".git" not in p.parts)


def op_create(kind, title, content):
    return kb_pb2.Operation(create=kb_pb2.Creation(type=kind, title=title, content=content))


def op_write(name, content, path=""):
    return kb_pb2.Operation(write=kb_pb2.Replacement(locator=kb_pb2.Locator(id=name, path=path), content=content))


def op_delete(name):
    return kb_pb2.Operation(delete=kb_pb2.Removal(locator=kb_pb2.Locator(id=name)))


work = Path(tempfile.mkdtemp()).resolve()
os.chdir(work)
(work / "a-file").write_text("x")
(work / "has-kb" / "kb").mkdir(parents=True)
init = kb_client.connect().Init
show("init no role", lambda: init(kb_pb2.InitRequest(root="s", actor=kb_pb2.Actor())))
show("init no root", lambda: init(kb_pb2.InitRequest(root="", actor=ME)))
show("init missing", lambda: init(kb_pb2.InitRequest(root="./nope", actor=ME)))
show("init a file", lambda: init(kb_pb2.InitRequest(root="./a-file", actor=ME)))
show("init over kb", lambda: init(kb_pb2.InitRequest(root="./has-kb", actor=ME)))
(work / "s").mkdir()
show("init ok", lambda: init(kb_pb2.InitRequest(root="./s", actor=ME)))
(work / "s" / "inner").mkdir()
show("init nested", lambda: init(kb_pb2.InitRequest(root="./s/inner", actor=ME)))

root = work / "s"
client = kb_client.connect(root)
apply = lambda ops, message="probe": client.Apply(kb_pb2.ApplyRequest(operations=ops, actor=ME, message=message))
for kind, type_content in [("decision", tagged_decision_type()), ("tag", TAG_TYPE)]:
    show(f"define {kind}", lambda: apply([op_create("schema", kind, dumps({k: v for k, v in type_content.items() if k != "title"}))]))
sections = [{"title": "Purpose", "body": "Ünïcødé — prose"}, {"title": "Rationale", "body": "why"}]
show("create decision", lambda: apply([op_create("decision", "Close early", dumps({"sections": sections}))]))
show("create tags", lambda: apply([op_create("tag", "A", dumps({})), op_create("tag", "B", dumps({}))]))
show("mixed set", lambda: apply([
    op_create("nothing", "X", dumps({})),
    op_write("Not/Plain", dumps({})),
    op_create("decision", "!!!", "a: [unclosed"),
    op_create("decision", "Close early", "id: x\n"),
    op_create("Bad Kind", "Y", "{}"),
]))
show("taken title, bad content", lambda: apply([op_create("decision", "Close early", "revision: 3\n")]))
show("write missing and bad", lambda: apply([op_write("decision/none", "a: [x"), op_write("decision/close-early", "x: 1", "sections/nowhere")]))
show("append bad item", lambda: client.Append(kb_pb2.AppendRequest(locator=kb_pb2.Locator(id="decision/close-early", path="options"), content="id: mine\n", actor=ME, message="m")))
show("append no collection", lambda: client.Append(kb_pb2.AppendRequest(locator=kb_pb2.Locator(id="decision/close-early", path="steps"), content="title: t\n", actor=ME, message="m")))
show("delete place", lambda: client.Delete(kb_pb2.DeleteRequest(locator=kb_pb2.Locator(id="tag/a", path="x/y"), actor=ME, message="m")))
show("snapshot mixed", lambda: client.Snapshot(kb_pb2.SnapshotRequest(artifacts=["tag/a", "Bad", "tag/none", "tag/b"], actor=ME, message="m")))
show("read section missing", lambda: client.Read(kb_pb2.ReadRequest(locator=kb_pb2.Locator(id="decision/close-early"), level=kb_pb2.ReadRequest.SECTION, section="Nope")))
show("refs bad both", lambda: client.Refs(kb_pb2.RefsRequest(locator=kb_pb2.Locator(id="Bad"), type="Bad Type", depth=1)))
show("journal bad both", lambda: client.Journal(kb_pb2.JournalRequest(artifact="Bad", since="yesterday")))
show("list bad kind", lambda: client.List(kb_pb2.ListRequest(type="Bad Kind")))
show("search bad kind", lambda: client.Search(kb_pb2.SearchRequest(type="Bad Kind", text="x")))
show("create no-type kind", lambda: client.Create(kb_pb2.CreateRequest(type="process", title="P", content="{}", actor=ME, message="m")))
entry_digests = []
for path in sorted((root / "kb" / "journal").rglob("*.yaml")):
    text = path.read_text()
    if "decision/close-early" in text and "digest:" in text:
        digest = next(line.split(": ")[1] for line in text.splitlines() if line.startswith("digest:"))
        entry_digests.append(digest == hashlib.sha256((root / "kb" / "decision" / "close-early.yaml").read_bytes()).hexdigest())
say("fingerprint of non-ascii matches file", entry_digests)
(root / "kb" / "tag" / "b.yaml").write_text("title: [broken\n")
before = (root / "kb" / "tag" / "a.yaml").read_bytes()
show("write a, delete unreadable b", lambda: apply([op_write("tag/a", dumps({})), op_delete("tag/b")]))
say("tag/a unchanged on disk", (root / "kb" / "tag" / "a.yaml").read_bytes() == before)
say("files", [name for name in files(root) if "journal" not in name], len(files(root)))
```

- [ ] **Step 2: Record the baseline**

Run (from the checkout's root, at the commit this plan was written on): `.venv/bin/python /tmp/kb-probe.py > /tmp/kb-probe-baseline.txt 2>&1; cat /tmp/kb-probe-baseline.txt`
Expected, exactly:

```
init no role faults [('', '', 'actor', 'a store can only be started under a role')]
init no root faults [('', '', 'root', 'a store is started in a directory that was named and that exists; no directory was named')]
init missing faults [('', '', 'root', "a store is started in a directory that exists; './nope' does not")]
init a file faults [('', '', 'root', "a store is started in a directory, and './a-file' is not one")]
init over kb faults [('', '', 'root', "a store is never started over another; './has-kb' already has a store inside it")]
init ok ok 
init nested faults [('', '', 'root', "stores do not nest; './s/inner' is inside the store at 'WORK/s'")]
define decision ok batch: "STAMP" results {   id: "schema/decision"   revision: 1 } 
define tag ok batch: "STAMP" results {   id: "schema/tag"   revision: 1 } 
create decision ok batch: "STAMP" results {   id: "decision/close-early"   revision: 1 } 
create tags ok batch: "STAMP" results {   id: "tag/a"   revision: 1 } results {   id: "tag/b"   revision: 1 } 
mixed set faults [('', '', 'kind', "a kind must name a type the store holds; the store holds no type called 'nothing'"), ('Not/Plain', '', 'locator', "a name is a kind and a plain name of lower-case letters, digits and single hyphens, never a path; 'Not/Plain' is not"), ('decision/', 'title', 'title', "a title must leave something to make a name from; '!!!' leaves nothing"), ('decision/', '', 'content', "it is not YAML that can be read: expected ',' or ']', but got '<stream end>' at line 1"), ('decision/close-early-2', 'id', 'identity', "content holds only what the type declares; id is settled by the store, and the content carried id: 'x'"), ('', '', 'kind', "a kind is a plain name of lower-case letters, digits and single hyphens, never a path; 'Bad Kind' is not")]
taken title, bad content faults [('decision/close-early-2', 'revision', 'identity', 'content holds only what the type declares; revision is settled by the store, and the content carried revision: 3')]
write missing and bad faults [('decision/none', '', 'not-found', "the store holds nothing by the name 'decision/none'"), ('decision/close-early', 'sections/nowhere', 'not-found', "'decision/close-early' holds nothing at 'sections/nowhere'")]
append bad item faults [('decision/close-early', 'id', 'identity', "content holds only what the type declares; an item's id is settled by the store, and the content carried id: 'mine'")]
append no collection faults [('decision/close-early', 'steps', 'not-found', "'decision/close-early' holds no collection called 'steps'")]
delete place faults [('tag/a', 'x/y', 'locator', "a removal takes out a whole artifact; 'x/y' is a place inside 'tag/a'")]
snapshot mixed faults [('Bad', '', 'locator', "a name is a kind and a plain name of lower-case letters, digits and single hyphens, never a path; 'Bad' is not"), ('tag/none', '', 'not-found', "the store holds nothing by the name 'tag/none'")]
read section missing faults [('decision/close-early', 'sections', 'not-found', "'decision/close-early' holds no section titled 'Nope'")]
refs bad both faults [('Bad', '', 'locator', "a name is a kind and a plain name of lower-case letters, digits and single hyphens, never a path; 'Bad' is not"), ('', '', 'kind', "a kind is a plain name of lower-case letters, digits and single hyphens, never a path; 'Bad Type' is not")]
journal bad both faults [('Bad', '', 'locator', "a name is a kind and a plain name of lower-case letters, digits and single hyphens, never a path; 'Bad' is not"), ('', '', 'since', "a time is written in ISO 8601, as 2026-09-22 or 2026-09-22T09:00:00Z; 'yesterday' is not")]
list bad kind faults [('', '', 'kind', "a kind is a plain name of lower-case letters, digits and single hyphens, never a path; 'Bad Kind' is not")]
search bad kind faults [('', '', 'kind', "a kind is a plain name of lower-case letters, digits and single hyphens, never a path; 'Bad Kind' is not")]
create no-type kind faults [('', '', 'kind', "a kind must name a type the store holds; the store holds no type called 'process'")]
fingerprint of non-ascii matches file [True]
write a, delete unreadable b raised Unreadable
tag/a unchanged on disk False
files ['kb/decision/close-early.yaml', 'kb/schema/decision.yaml', 'kb/schema/schema.yaml', 'kb/schema/tag.yaml', 'kb/store.yaml', 'kb/tag/a.yaml', 'kb/tag/b.yaml'] 14
```

Each task's probe step runs `.venv/bin/python /tmp/kb-probe.py > /tmp/kb-probe-now.txt 2>&1` and compares `/tmp/kb-probe-now.txt` with the file named there, using `diff`.

---

### Task 1: Slice 53, The suite gives the same answer every time

**Files:**
- Modify: `src/kb/store.py` (the git helper at the end of the file)

**Interfaces:**
- Consumes: nothing
- Produces:
  `store.QUIET`, the `-c` options every git call the store makes now carries. No signature changes.

- [ ] **Step 1: See the check fail**

Run: `for i in $(seq 10); do .venv/bin/python -m pytest -q 2>&1 | tail -1; done`
Expected: most lines `118 passed, 508 warnings in …`; in the scratch run one line in ten was `1 failed, 117 passed …`. The failure is intermittent: if all ten pass, run the loop once more. It is not a gate, since the fix is known (batch 6 review: git's detached `git maintenance run --auto` touches `kb/.git` after a commit returns, while a "nothing was written" step snapshots the whole tree).

- [ ] **Step 2: Apply the change**

Save the patch as `/tmp/kb-slice-53.patch`, then run: `git apply --check /tmp/kb-slice-53.patch && git apply /tmp/kb-slice-53.patch`
Expected: no output

```diff
diff --git a/src/kb/store.py b/src/kb/store.py
index 3fd34b2..b945459 100644
--- a/src/kb/store.py
+++ b/src/kb/store.py
@@ -119,5 +119,9 @@ class Draft:
         return self.load(ArtifactId(Kind("schema"), kind.name))
 
 
+QUIET = ("-c", "maintenance.auto=false", "-c", "gc.auto=0")
+
+
 def _git(*args, env=None):
-    subprocess.run(["git", *args], check=True, capture_output=True, text=True, env=env)
+    """git, with its automatic maintenance off, so nothing runs on in the store after a call returns."""
+    subprocess.run(["git", *QUIET, *args], check=True, capture_output=True, text=True, env=env)
```

- [ ] **Step 3: See the check pass**

Run: `for i in $(seq 10); do .venv/bin/python -m pytest -q 2>&1 | tail -1; done`
Expected: ten lines, each `118 passed, 508 warnings in …`, none with `failed`.

- [ ] **Step 4: Run the probe**

Run: `.venv/bin/python /tmp/kb-probe.py > /tmp/kb-probe-now.txt 2>&1; diff /tmp/kb-probe-baseline.txt /tmp/kb-probe-now.txt`
Expected: no output (the probe's output is identical to the baseline)

- [ ] **Step 5: Mark the slice green and commit**

In `docs/superpowers/plans/2026-09-24-kb-slices.md`, set slice 53's `Status:` to `green` and append a log line: `- <date> slice 53 green. <what its check showed>. Surprised by: <anything, or nothing>.`

```bash
git add -A src/kb docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 53: The suite gives the same answer every time

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 2: Slice 54, Every request field is a value before anything else sees it

**Files:**
- Create: `src/kb/requests.py`: each rpc's request as the values its domain call takes
- Modify: `src/kb/values.py`: `content` and `item` return a `Content` value carrying problems instead of raising; new `Actor`, `Signed`, `actor`, `signed`, `starter`
- Modify: `src/kb/journal.py`: `write` and `snapshot` take `signed: Signed` instead of `actor` and `message`
- Modify: `src/kb/store.py`: `Store.commit(paths, signed)`
- Modify: `src/kb/servicer.py`: every rpc converts its whole request first; the domain code works on the values

**Interfaces:**
- Consumes: `store.QUIET` (task 1), used only inside the store
- Produces:
- `values.Content(tree, problems)`, a frozen dataclass; `problems` is a tuple of `(path, rule, message)`; `Content.refusal(artifact: str) -> list[kb_pb2.Fault]`
- `values.content(text: str, at_root: bool = True) -> Content`, `values.item(text: str) -> Content`
- `values.Actor(role, execution)`, `values.Signed(actor, message)`, `values.actor(proto) -> Actor`, `values.signed(proto_actor, message) -> Signed`, `values.starter(proto_actor) -> Actor` (raises `Refused` with rule `actor` when there is no role)
- `requests.Refusal(faults)`, `requests.Create(kind, title, name, at, title_faults, content)`, `requests.Replace(locator, content)`, `requests.Add(locator, item)`, `requests.Remove(locator)`, `requests.Reading(locator, level, depth, section)` with `level` one of `"whole"`, `"section"`, `"summary"`, `requests.JournalFilter(artifact, role, execution, since, batch)`, `requests.Searching(kind, text, sections, fields)`, `requests.Walk(locator, kind, depth, via, inward)`, `requests.Listing(kind, fields, ids)`
- `requests.starting(InitRequest) -> (Actor, root)`, `requests.operations(iterable of kb_pb2.Operation) -> list` (each a value or a `Refusal`), `requests.reading`, `requests.journal`, `requests.searching`, `requests.walk`, `requests.listing`, `requests.names(names) -> list` (each an `ArtifactId` or a `Refusal`), renamed `snapshotted` in task 3
- `journal.write(store_dir, *, signed, op, artifact, path, revision, schema_version, written, seq=1, batch="")`, `journal.snapshot(store_dir, *, signed, read)`, `Store.commit(paths, signed)`

- [ ] **Step 1: See the check fail**

Run: `grep -n "request\.[a-z_]" src/kb/servicer.py | grep -vE "requests\.[a-z]+\(|values\.signed\(|kb_pb2\.(Creation|Replacement|Addition|Removal)\(" | wc -l`
Expected: `33`

Run: `grep -nE "message: str|role: str" src/kb/journal.py src/kb/store.py`
Expected: three lines (journal.py's `write` and `snapshot`, store.py's `commit`)

- [ ] **Step 2: Apply the change**

Save the patch as `/tmp/kb-slice-54.patch`, then run: `git apply --check /tmp/kb-slice-54.patch && git apply /tmp/kb-slice-54.patch`
Expected: no output

```diff
diff --git a/src/kb/journal.py b/src/kb/journal.py
index ddb4ab0..d7ffa26 100644
--- a/src/kb/journal.py
+++ b/src/kb/journal.py
@@ -4,6 +4,7 @@ from datetime import datetime, timezone
 from pathlib import Path
 
 from kb import canonical
+from kb.values import Signed
 
 
 def now() -> datetime:
@@ -16,8 +17,8 @@ def digest(path: Path) -> str:
     return hashlib.sha256(path.read_bytes()).hexdigest()
 
 
-def write(store_dir: Path, *, actor, op: str, artifact: str, path: str, revision: int,
-          schema_version: int, written: Path | None, message: str, seq: int = 1, batch: str = "") -> Path:
+def write(store_dir: Path, *, signed: Signed, op: str, artifact: str, path: str, revision: int,
+          schema_version: int, written: Path | None, seq: int = 1, batch: str = "") -> Path:
     """Write one entry and return its file; its stem is the entry's id. A change made alone names itself as its batch.
     A removal wrote nothing, so its entry's fingerprint is empty."""
     at = now()
@@ -25,20 +26,20 @@ def write(store_dir: Path, *, actor, op: str, artifact: str, path: str, revision
     entry = {
         "id": entry_id,
         "at": at.isoformat(),
-        "actor": {"role": actor.role, "execution": actor.execution},
+        "actor": {"role": signed.actor.role, "execution": signed.actor.execution},
         "op": op,
         "artifact": artifact,
         "path": path,
         "revision": revision,
         "schema_version": schema_version,
         "digest": digest(written) if written is not None else "",
-        "message": message,
+        "message": signed.message,
         "batch": batch or entry_id,
     }
     return _save(store_dir, at, entry)
 
 
-def snapshot(store_dir: Path, *, actor, read: list[dict], message: str) -> Path:
+def snapshot(store_dir: Path, *, signed: Signed, read: list[dict]) -> Path:
     """Write the entry recording what a piece of work read, each artifact as { artifact, revision, digest }, and
     return its file. It names no artifact of its own and is a set of its own."""
     at = now()
@@ -46,10 +47,10 @@ def snapshot(store_dir: Path, *, actor, read: list[dict], message: str) -> Path:
     entry = {
         "id": entry_id,
         "at": at.isoformat(),
-        "actor": {"role": actor.role, "execution": actor.execution},
+        "actor": {"role": signed.actor.role, "execution": signed.actor.execution},
         "op": "snapshot",
         "read": read,
-        "message": message,
+        "message": signed.message,
         "batch": entry_id,
     }
     return _save(store_dir, at, entry)
diff --git a/src/kb/requests.py b/src/kb/requests.py
new file mode 100644
index 0000000..8979f43
--- /dev/null
+++ b/src/kb/requests.py
@@ -0,0 +1,182 @@
+"""Each rpc's request as the values its one domain call takes, built from the conversions in kb.values. A request that
+does not convert is refused here, before anything else sees it. In a set, or among the names a snapshot is given, an
+entry that does not convert stands in its place as a Refusal, so the faults come back in the order of the entries."""
+from dataclasses import dataclass
+from datetime import datetime
+from pathlib import Path
+
+from kb import values
+from kb.contract import kb_pb2
+from kb.values import Actor, ArtifactId, Content, Kind, Locator, Refused
+
+
+@dataclass(frozen=True)
+class Refusal:
+    """An entry that did not convert, and its faults."""
+    faults: tuple
+
+
+@dataclass(frozen=True)
+class Create:
+    """A new artifact: its kind, its title, the name the title gives (None when it gives none, the title's faults
+    saying why), the name its faults are said of until it has one, and its content."""
+    kind: Kind
+    title: str
+    name: ArtifactId | None
+    at: str
+    title_faults: tuple
+    content: Content
+
+
+@dataclass(frozen=True)
+class Replace:
+    locator: Locator
+    content: Content
+
+
+@dataclass(frozen=True)
+class Add:
+    locator: Locator
+    item: Content
+
+
+@dataclass(frozen=True)
+class Remove:
+    locator: Locator
+
+
+@dataclass(frozen=True)
+class Reading:
+    locator: Locator
+    level: str
+    depth: int
+    section: str
+
+
+@dataclass(frozen=True)
+class JournalFilter:
+    artifact: ArtifactId | None
+    role: str
+    execution: str
+    since: datetime | None
+    batch: str
+
+
+@dataclass(frozen=True)
+class Searching:
+    kind: Kind | None
+    text: str
+    sections: bool
+    fields: bool
+
+
+@dataclass(frozen=True)
+class Walk:
+    locator: Locator
+    kind: Kind | None
+    depth: int
+    via: str
+    inward: bool
+
+
+@dataclass(frozen=True)
+class Listing:
+    kind: Kind
+    fields: dict
+    ids: bool
+
+
+def starting(request: kb_pb2.InitRequest) -> tuple[Actor, Path]:
+    """Who starts a store, then where; the first refusal only."""
+    return values.starter(request.actor), values.root(request.root)
+
+
+def operations(requested) -> list:
+    """Every operation of a set, each converted or standing as its refusal."""
+    converted = []
+    for operation in requested:
+        try:
+            converted.append(_operation(operation))
+        except Refused as refused:
+            converted.append(Refusal(tuple(refused.faults)))
+    return converted
+
+
+def _operation(operation: kb_pb2.Operation):
+    which = operation.WhichOneof("operation")
+    if which == "create":
+        return _create(operation.create)
+    if which == "append":
+        return Add(values.locator(operation.append.locator), values.item(operation.append.content))
+    if which == "delete":
+        return Remove(values.locator(operation.delete.locator))
+    locator = values.locator(operation.write.locator)
+    return Replace(locator, values.content(operation.write.content, at_root=not locator.place))
+
+
+def _create(creation: kb_pb2.Creation) -> Create:
+    kind = values.kind(creation.type)
+    try:
+        name, title_faults = values.named(kind, creation.title), ()
+    except Refused as refused:
+        name, title_faults = None, tuple(refused.faults)
+    at = f"{kind.name}/{values.slug(creation.title)}"
+    return Create(kind, creation.title, name, at, title_faults, values.content(creation.content))
+
+
+def reading(request: kb_pb2.ReadRequest) -> Reading:
+    level = {kb_pb2.ReadRequest.WHOLE: "whole", kb_pb2.ReadRequest.SECTION: "section"}.get(request.level, "summary")
+    return Reading(values.locator(request.locator), level, request.depth, request.section)
+
+
+def journal(request: kb_pb2.JournalRequest) -> JournalFilter:
+    """The journal's filters; both faults when the artifact and the time both fail."""
+    artifact, since, faults = None, None, []
+    try:
+        artifact = values.artifact_id(request.artifact) if request.artifact else None
+    except Refused as refused:
+        faults += refused.faults
+    try:
+        since = values.since(request.since) if request.since else None
+    except Refused as refused:
+        faults += refused.faults
+    if faults:
+        raise Refused(faults)
+    return JournalFilter(artifact, request.role, request.execution, since, request.batch)
+
+
+def searching(request: kb_pb2.SearchRequest) -> Searching:
+    kind = values.kind(request.type) if request.type else None
+    scope = request.scope
+    return Searching(kind, request.text, scope != kb_pb2.SearchRequest.FIELDS, scope != kb_pb2.SearchRequest.SECTIONS)
+
+
+def walk(request: kb_pb2.RefsRequest) -> Walk:
+    """The walk's start and its narrowing by type; both faults when both fail."""
+    locator, kind, faults = None, None, []
+    try:
+        locator = values.locator(request.locator)
+    except Refused as refused:
+        faults += refused.faults
+    try:
+        kind = values.kind(request.type) if request.type else None
+    except Refused as refused:
+        faults += refused.faults
+    if faults:
+        raise Refused(faults)
+    return Walk(locator, kind, request.depth, request.via, request.direction == kb_pb2.RefsRequest.IN)
+
+
+def listing(request: kb_pb2.ListRequest) -> Listing:
+    return Listing(values.kind(request.type), dict(request.fields), request.form == kb_pb2.ListRequest.IDS)
+
+
+def names(requested) -> list:
+    """Each name a snapshot is given, converted or standing as its refusal."""
+    converted = []
+    for name in requested:
+        try:
+            converted.append(values.artifact_id(name))
+        except Refused as refused:
+            converted.append(Refusal(tuple(refused.faults)))
+    return converted
diff --git a/src/kb/servicer.py b/src/kb/servicer.py
index 13ffaf4..44e90f3 100644
--- a/src/kb/servicer.py
+++ b/src/kb/servicer.py
@@ -7,12 +7,12 @@ import copy
 from datetime import datetime
 from typing import NamedTuple
 
-from kb import canonical, journal, search, validation, values
+from kb import canonical, journal, requests, search, validation, values
 from kb.content import dumps, text
 from kb.contract import kb_pb2, kb_pb2_grpc
 from kb.metaschema import METASCHEMA
 from kb.store import Draft, Store, Unreadable
-from kb.values import ArtifactId, Kind
+from kb.values import ArtifactId, Kind, Signed
 
 METASCHEMA_ID = ArtifactId(Kind("schema"), "schema")
 
@@ -31,56 +31,53 @@ class KbServicer(kb_pb2_grpc.KbServicer):
         self._store = Store(root) if root is not None else None
 
     def Init(self, request, context):
-        if not request.actor.role:
-            return kb_pb2.InitResponse(faults=[kb_pb2.Fault(
-                rule="actor", message="a store can only be started under a role",
-            )])
         try:
-            store = Store(values.root(request.root))
+            actor, root = requests.starting(request)
         except values.Refused as refused:
             return kb_pb2.InitResponse(faults=refused.faults)
+        store, signed = Store(root), Signed(actor, "initialise store")
         store.start()
         metaschema = {"id": str(METASCHEMA_ID), "type": "schema", "schema_version": 1, "revision": 1, **METASCHEMA}
         path = store.save(METASCHEMA_ID, canonical.dump(canonical.order(metaschema, METASCHEMA["schema"])))
         entry = journal.write(
-            store.dir, actor=request.actor, op="create", artifact=str(METASCHEMA_ID), path="",
-            revision=1, schema_version=1, written=path, message="initialise store",
+            store.dir, signed=signed, op="create", artifact=str(METASCHEMA_ID), path="",
+            revision=1, schema_version=1, written=path,
         )
-        store.commit([store.dir / "store.yaml", path, entry], request.actor.role, "initialise store")
+        store.commit([store.dir / "store.yaml", path, entry], signed)
         return kb_pb2.InitResponse()
 
     def Create(self, request, context):
         creation = kb_pb2.Creation(type=request.type, title=request.title, content=request.content)
-        landed = self._land([kb_pb2.Operation(create=creation)], request.actor, request.message)
+        landed = self._land(requests.operations([kb_pb2.Operation(create=creation)]), values.signed(request.actor, request.message))
         if landed.faults:
             return kb_pb2.CreateResponse(faults=landed.faults)
         return kb_pb2.CreateResponse(id=landed.results[0].id, revision=landed.results[0].revision)
 
     def Write(self, request, context):
         replacement = kb_pb2.Replacement(locator=request.locator, content=request.content)
-        landed = self._land([kb_pb2.Operation(write=replacement)], request.actor, request.message)
+        landed = self._land(requests.operations([kb_pb2.Operation(write=replacement)]), values.signed(request.actor, request.message))
         if landed.faults:
             return kb_pb2.WriteResponse(faults=landed.faults)
         return kb_pb2.WriteResponse(revision=landed.results[0].revision)
 
     def Append(self, request, context):
         addition = kb_pb2.Addition(locator=request.locator, content=request.content)
-        landed = self._land([kb_pb2.Operation(append=addition)], request.actor, request.message)
+        landed = self._land(requests.operations([kb_pb2.Operation(append=addition)]), values.signed(request.actor, request.message))
         if landed.faults:
             return kb_pb2.AppendResponse(faults=landed.faults)
         return kb_pb2.AppendResponse(id=landed.results[0].item, revision=landed.results[0].revision)
 
     def Delete(self, request, context):
         removal = kb_pb2.Removal(locator=request.locator)
-        landed = self._land([kb_pb2.Operation(delete=removal)], request.actor, request.message)
+        landed = self._land(requests.operations([kb_pb2.Operation(delete=removal)]), values.signed(request.actor, request.message))
         if landed.faults:
             return kb_pb2.DeleteResponse(faults=landed.faults)
         return kb_pb2.DeleteResponse(revision=landed.results[0].revision)
 
     def Apply(self, request, context):
-        return self._land(request.operations, request.actor, request.message)
+        return self._land(requests.operations(request.operations), values.signed(request.actor, request.message))
 
-    def _land(self, operations, actor, message) -> kb_pb2.ApplyResponse:
+    def _land(self, operations: list, signed: Signed) -> kb_pb2.ApplyResponse:
         """The write path. Each operation is applied in order to a draft of the store and checked there, against the
         store as the operations before it left it; only when every one passes is anything written, each artifact
         saved, one journal entry per operation naming the set, and one commit.
@@ -90,6 +87,9 @@ class KbServicer(kb_pb2_grpc.KbServicer):
         draft = Draft(self._store)
         touched, faults = [], []
         for operation in operations:
+            if isinstance(operation, requests.Refusal):
+                faults += operation.faults
+                continue
             try:
                 touched.append(self._apply(draft, operation))
             except values.Refused as refused:
@@ -118,46 +118,39 @@ class KbServicer(kb_pb2_grpc.KbServicer):
                 revision, schema_version = artifact["revision"], artifact["schema_version"]
                 path = saved = self._store.save(change.artifact_id, text)
             entry = journal.write(
-                self._store.dir, actor=actor, op=change.op, artifact=str(change.artifact_id), path=change.path,
-                revision=revision, schema_version=schema_version,
-                written=saved, message=message, seq=seq, batch=batch,
+                self._store.dir, signed=signed, op=change.op, artifact=str(change.artifact_id), path=change.path,
+                revision=revision, schema_version=schema_version, written=saved, seq=seq, batch=batch,
             )
             batch = batch or entry.stem
             written += [path, entry]
             results.append(kb_pb2.Result(id=str(change.artifact_id), revision=revision, item=change.item))
-        self._store.commit(written, actor.role, message)
+        self._store.commit(written, signed)
         return kb_pb2.ApplyResponse(batch=batch, results=results)
 
-    def _apply(self, draft: Draft, operation: kb_pb2.Operation) -> Change:
+    def _apply(self, draft: Draft, operation) -> Change:
         """One operation applied to the draft. Returns what it did; raises values.Refused."""
-        which = operation.WhichOneof("operation")
-        if which == "create":
-            return Change("create", self._create(draft, operation.create))
-        if which == "append":
-            return self._append(draft, operation.append)
-        if which == "delete":
-            return self._delete(draft, operation.delete)
-        return Change("write", self._replace(draft, operation.write))
-
-    def _create(self, draft: Draft, creation: kb_pb2.Creation) -> ArtifactId:
-        kind = values.kind(creation.type)
+        if isinstance(operation, requests.Create):
+            return Change("create", self._create(draft, operation))
+        if isinstance(operation, requests.Add):
+            return self._append(draft, operation)
+        if isinstance(operation, requests.Remove):
+            return self._delete(draft, operation)
+        return Change("write", self._replace(draft, operation))
+
+    def _create(self, draft: Draft, creation: requests.Create) -> ArtifactId:
+        kind = creation.kind
         if not draft.holds(ArtifactId(Kind("schema"), kind.name)):
             raise values.Refused([kb_pb2.Fault(
                 rule="kind", message=f"a kind must name a type the store holds; the store holds no type called {kind.name!r}",
             )])
-        at = f"{kind.name}/{values.slug(creation.title)}"
-        faults = []
-        try:
-            artifact_id = _unclaimed(draft, values.named(kind, creation.title))
+        at, faults = creation.at, list(creation.title_faults)
+        if creation.name is not None:
+            artifact_id = _unclaimed(draft, creation.name)
             at = str(artifact_id)
-        except values.Refused as refused:
-            faults += refused.faults
-        try:
-            content = values.content(at, creation.content)
-        except values.Refused as refused:
-            faults += refused.faults
+        faults += creation.content.refusal(at)
         if faults:
             raise values.Refused(faults)
+        content = creation.content.tree
         schema = draft.schema(kind)
         faults = validation.validate(at, {"title": creation.title, **content}, schema["schema"], draft)
         if faults:
@@ -171,23 +164,27 @@ class KbServicer(kb_pb2_grpc.KbServicer):
         draft.put(artifact_id, canonical.order(artifact, schema["schema"]))
         return artifact_id
 
-    def _replace(self, draft: Draft, replacement: kb_pb2.Replacement) -> ArtifactId:
-        locator = values.locator(replacement.locator)
+    def _replace(self, draft: Draft, replacement: requests.Replace) -> ArtifactId:
+        locator = replacement.locator
         if not draft.holds(locator.id):
             raise values.Refused([_not_found(locator.id)])
-        content = values.content(str(locator.id), replacement.content, at_root=not locator.place)
+        if replacement.content.problems:
+            raise values.Refused(replacement.content.refusal(str(locator.id)))
+        content = replacement.content.tree
         current = draft.load(locator.id)
         if locator.place:
             content = _placed(current, locator, content)
         _revise(draft, locator.id, current, content)
         return locator.id
 
-    def _append(self, draft: Draft, addition: kb_pb2.Addition) -> Change:
+    def _append(self, draft: Draft, addition: requests.Add) -> Change:
         """One item put at the end of a collection the artifact's type declares, and named there."""
-        locator = values.locator(addition.locator)
+        locator = addition.locator
         if not draft.holds(locator.id):
             raise values.Refused([_not_found(locator.id)])
-        item = values.item(str(locator.id), addition.content)
+        if addition.item.problems:
+            raise values.Refused(addition.item.refusal(str(locator.id)))
+        item = addition.item.tree
         collection = "/".join(locator.place)
         if collection not in draft.schema(locator.id.kind)["schema"].get("parts", {}):
             raise values.Refused([kb_pb2.Fault(
@@ -200,9 +197,9 @@ class KbServicer(kb_pb2_grpc.KbServicer):
         _revise(draft, locator.id, current, content)
         return Change("append", locator.id, f"{collection}/{item['id']}", item["id"])
 
-    def _delete(self, draft: Draft, removal: kb_pb2.Removal) -> Change:
+    def _delete(self, draft: Draft, removal: requests.Remove) -> Change:
         """A whole artifact taken out of the draft, refused with one fault for each link that still points at it."""
-        locator = values.locator(removal.locator)
+        locator = removal.locator
         if not draft.holds(locator.id):
             raise values.Refused([_not_found(locator.id)])
         if locator.place:
@@ -228,16 +225,17 @@ class KbServicer(kb_pb2_grpc.KbServicer):
 
     def Read(self, request, context):
         try:
-            locator = values.locator(request.locator)
+            reading = requests.reading(request)
         except values.Refused as refused:
             return kb_pb2.ReadResponse(faults=refused.faults)
+        locator = reading.locator
         if not self._store.holds(locator.id):
             return kb_pb2.ReadResponse(faults=[_not_found(locator.id)])
         try:
-            if request.level == kb_pb2.ReadRequest.WHOLE:
-                return self._whole(locator, request.depth)
-            if request.level == kb_pb2.ReadRequest.SECTION:
-                return self._section(locator, request.section)
+            if reading.level == "whole":
+                return self._whole(locator, reading.depth)
+            if reading.level == "section":
+                return self._section(locator, reading.section)
             return self._summary(locator)
         except Unreadable as unreadable:
             return kb_pb2.ReadResponse(faults=[unreadable.fault])
@@ -324,39 +322,29 @@ class KbServicer(kb_pb2_grpc.KbServicer):
 
     def Journal(self, request, context):
         """The journal's entries, oldest first, narrowed by each of artifact, role, piece of work, time and set given."""
-        faults = []
-        try:
-            artifact = str(values.artifact_id(request.artifact)) if request.artifact else ""
-        except values.Refused as refused:
-            faults += refused.faults
         try:
-            since = values.since(request.since) if request.since else None
+            wanted = requests.journal(request)
         except values.Refused as refused:
-            faults += refused.faults
-        if faults:
-            return kb_pb2.JournalResponse(faults=faults)
+            return kb_pb2.JournalResponse(faults=refused.faults)
         return kb_pb2.JournalResponse(entries=[
             _entry(entry) for entry in journal.entries(self._store.dir)
-            if (not artifact or entry.get("artifact") == artifact)
-            and (not request.role or entry["actor"]["role"] == request.role)
-            and (not request.execution or entry["actor"]["execution"] == request.execution)
-            and (since is None or datetime.fromisoformat(entry["at"]) >= since)
-            and (not request.batch or entry["batch"] == request.batch)
+            if (wanted.artifact is None or entry.get("artifact") == str(wanted.artifact))
+            and (not wanted.role or entry["actor"]["role"] == wanted.role)
+            and (not wanted.execution or entry["actor"]["execution"] == wanted.execution)
+            and (wanted.since is None or datetime.fromisoformat(entry["at"]) >= wanted.since)
+            and (not wanted.batch or entry["batch"] == wanted.batch)
         ])
 
     def Search(self, request, context):
         """Every section whose prose, or field whose value, holds a word searched for, as the scope asks, among the
         artifacts of one kind when a type is given, with a stub of its artifact, most often first."""
         try:
-            kind = values.kind(request.type) if request.type else None
+            searching = requests.searching(request)
         except values.Refused as refused:
             return kb_pb2.SearchResponse(faults=refused.faults)
+        kind = searching.kind
         artifacts = (artifact for artifact in self._store.artifacts() if kind is None or artifact["type"] == kind.name)
-        scope = request.scope
-        hits = search.rank(
-            artifacts, request.text,
-            sections=scope != kb_pb2.SearchRequest.FIELDS, fields=scope != kb_pb2.SearchRequest.SECTIONS,
-        )
+        hits = search.rank(artifacts, searching.text, sections=searching.sections, fields=searching.fields)
         return kb_pb2.SearchResponse(matches=[
             kb_pb2.Match(
                 stub=self._stub("", values.artifact_id(hit.artifact)), section=hit.section, field=hit.field,
@@ -368,26 +356,20 @@ class KbServicer(kb_pb2_grpc.KbServicer):
     def Refs(self, request, context):
         """What an artifact's links reach, out of it or into it, a step at a time out to the depth asked: each artifact
         once, by the shortest route, the one asked about never. A via or a type narrows every step."""
-        faults = []
-        try:
-            locator = values.locator(request.locator)
-        except values.Refused as refused:
-            faults += refused.faults
         try:
-            kind = values.kind(request.type) if request.type else None
+            walk = requests.walk(request)
         except values.Refused as refused:
-            faults += refused.faults
-        if faults:
-            return kb_pb2.RefsResponse(faults=faults)
+            return kb_pb2.RefsResponse(faults=refused.faults)
+        locator, kind = walk.locator, walk.kind
         if not self._store.holds(locator.id):
             return kb_pb2.RefsResponse(faults=[_not_found(locator.id)])
-        step = self._inward if request.direction == kb_pb2.RefsRequest.IN else self._outward
+        step = self._inward if walk.inward else self._outward
         reached, seen, frontier = [], {str(locator.id)}, [(locator.id, [])]
-        for _ in range(request.depth):
+        for _ in range(walk.depth):
             following = []
             for artifact_id, route in frontier:
                 for field, other_id in step(artifact_id):
-                    if str(other_id) in seen or (request.via and field != request.via):
+                    if str(other_id) in seen or (walk.via and field != walk.via):
                         continue
                     if kind is not None and other_id.kind != kind:
                         continue
@@ -419,14 +401,14 @@ class KbServicer(kb_pb2_grpc.KbServicer):
     def List(self, request, context):
         """Every artifact of a kind whose fields hold the values asked for, in path order, as stubs or names."""
         try:
-            kind = values.kind(request.type)
+            listing = requests.listing(request)
         except values.Refused as refused:
             return kb_pb2.ListResponse(faults=refused.faults)
         matched = [
             artifact_id for artifact_id in self._store.ids()
-            if artifact_id.kind == kind and _holds(self._store.load(artifact_id), request.fields)
+            if artifact_id.kind == listing.kind and _holds(self._store.load(artifact_id), listing.fields)
         ]
-        if request.form == kb_pb2.ListRequest.IDS:
+        if listing.ids:
             return kb_pb2.ListResponse(ids=[str(artifact_id) for artifact_id in matched])
         return kb_pb2.ListResponse(stubs=[self._stub("", artifact_id) for artifact_id in matched])
 
@@ -434,11 +416,9 @@ class KbServicer(kb_pb2_grpc.KbServicer):
         """One journal entry listing each artifact named with its version now and the fingerprint of its file, under
         the actor and the message given, in a commit of its own."""
         named, faults = [], []
-        for name in request.artifacts:
-            try:
-                artifact_id = values.artifact_id(name)
-            except values.Refused as refused:
-                faults += refused.faults
+        for artifact_id in requests.names(request.artifacts):
+            if isinstance(artifact_id, requests.Refusal):
+                faults += artifact_id.faults
                 continue
             if not self._store.holds(artifact_id):
                 faults.append(_not_found(artifact_id))
@@ -453,8 +433,9 @@ class KbServicer(kb_pb2_grpc.KbServicer):
             }
             for artifact_id in named
         ]
-        entry = journal.snapshot(self._store.dir, actor=request.actor, read=read, message=request.message)
-        self._store.commit([entry], request.actor.role, request.message)
+        signed = values.signed(request.actor, request.message)
+        entry = journal.snapshot(self._store.dir, signed=signed, read=read)
+        self._store.commit([entry], signed)
         return kb_pb2.SnapshotResponse(entry=entry.stem)
 
     def _stub(self, field, target_id: ArtifactId):
diff --git a/src/kb/store.py b/src/kb/store.py
index b945459..05767a9 100644
--- a/src/kb/store.py
+++ b/src/kb/store.py
@@ -5,7 +5,7 @@ from pathlib import Path
 
 from kb import canonical, values
 from kb.contract import CONTRACT_VERSION, kb_pb2
-from kb.values import ArtifactId, Kind
+from kb.values import ArtifactId, Kind, Signed
 
 
 class Unreadable(Exception):
@@ -63,8 +63,9 @@ class Store:
         """The schema artifact of a kind; its JSON Schema is under `schema`."""
         return self.load(ArtifactId(Kind("schema"), kind.name))
 
-    def commit(self, paths: list, role: str, message: str) -> None:
-        """One commit of the given files, message from the request, author from the actor."""
+    def commit(self, paths: list, signed: Signed) -> None:
+        """One commit of the given files, under the message and the actor's role."""
+        role = signed.actor.role
         relative = [str(Path(path).relative_to(self.dir)) for path in paths]
         _git("-C", str(self.dir), "add", "--", *relative)
         env = {
@@ -72,7 +73,7 @@ class Store:
             "GIT_AUTHOR_NAME": role, "GIT_AUTHOR_EMAIL": f"{role}@kb",
             "GIT_COMMITTER_NAME": role, "GIT_COMMITTER_EMAIL": f"{role}@kb",
         }
-        _git("-C", str(self.dir), "-c", "commit.gpgsign=false", "commit", "-q", "-m", message, "--", *relative, env=env)
+        _git("-C", str(self.dir), "-c", "commit.gpgsign=false", "commit", "-q", "-m", signed.message, "--", *relative, env=env)
 
     def ids(self) -> list[ArtifactId]:
         """The name of every artifact in the store, schemas included, in path order."""
diff --git a/src/kb/values.py b/src/kb/values.py
index 288b21f..203cba3 100644
--- a/src/kb/values.py
+++ b/src/kb/values.py
@@ -107,17 +107,28 @@ def named(kind: Kind, title: str) -> ArtifactId:
     return ArtifactId(kind, slug(title))
 
 
-def content(artifact: str, text: str, at_root: bool = True) -> dict:
-    """Content as a request carries it: read plainly, and, for a whole artifact, holding only what a type declares.
-    The identity keys belong to an artifact's root, so a node inside it, a section with its title, is not held to
-    them. Refused with every fault."""
+@dataclass(frozen=True)
+class Content:
+    """Content as a request carries it: the tree read from it, and, when it cannot be taken, what is wrong with it,
+    each as a place, a rule and a message, to be said of whichever artifact the content turns out to be for."""
+    tree: object
+    problems: tuple[tuple[str, str, str], ...] = ()
+
+    def refusal(self, artifact: str) -> list[kb_pb2.Fault]:
+        return [kb_pb2.Fault(artifact=artifact, path=path, rule=rule, message=message)
+                for path, rule, message in self.problems]
+
+
+def content(text: str, at_root: bool = True) -> Content:
+    """Content read plainly, and, for a whole artifact, holding only what a type declares. The identity keys belong
+    to an artifact's root, so a node inside it, a section with its title, is not held to them. Every problem found."""
     try:
         tree = loads(text)
     except canonical.NotCanonical as fault:
-        raise Refused([kb_pb2.Fault(artifact=artifact, path=fault.path, rule="content", message=str(fault))]) from None
+        return Content(None, ((fault.path, "content", str(fault)),))
     if not at_root:
-        return tree
-    faults = []
+        return Content(tree)
+    problems = []
     for key in canonical.IDENTITY:
         if key not in tree:
             continue
@@ -125,22 +136,45 @@ def content(artifact: str, text: str, at_root: bool = True) -> dict:
             message = f"a title is given alongside the content, never inside it; the content carried the title {tree[key]!r}"
         else:
             message = f"content holds only what the type declares; {key} is settled by the store, and the content carried {key}: {tree[key]!r}"
-        faults.append(kb_pb2.Fault(artifact=artifact, path=key, rule="identity", message=message))
-    if faults:
-        raise Refused(faults)
-    return tree
+        problems.append((key, "identity", message))
+    return Content(tree, tuple(problems))
 
 
-def item(artifact: str, text: str) -> dict:
-    """An item as a request carries it: read plainly, and never carrying its own name, which kb gives. Refused with
-    the fault that names what it carried."""
-    tree = content(artifact, text, at_root=False)
-    if "id" in tree:
-        raise Refused([kb_pb2.Fault(
-            artifact=artifact, path="id", rule="identity",
-            message=f"content holds only what the type declares; an item's id is settled by the store, and the content carried id: {tree['id']!r}",
-        )])
-    return tree
+def item(text: str) -> Content:
+    """An item read plainly, never carrying its own name, which kb gives."""
+    read = content(text, at_root=False)
+    if read.problems or "id" not in read.tree:
+        return read
+    return Content(read.tree, (("id", "identity",
+        f"content holds only what the type declares; an item's id is settled by the store, and the content carried id: {read.tree['id']!r}"),))
+
+
+@dataclass(frozen=True)
+class Actor:
+    role: str
+    execution: str
+
+
+@dataclass(frozen=True)
+class Signed:
+    """Who made a change, and the message they gave for it."""
+    actor: Actor
+    message: str
+
+
+def actor(request: kb_pb2.Actor) -> Actor:
+    return Actor(request.role, request.execution)
+
+
+def signed(request: kb_pb2.Actor, message: str) -> Signed:
+    return Signed(actor(request), message)
+
+
+def starter(request: kb_pb2.Actor) -> Actor:
+    """The actor who starts a store, who must name a role."""
+    if not request.role:
+        raise Refused([kb_pb2.Fault(rule="actor", message="a store can only be started under a role")])
+    return actor(request)
 
 
 def root(text: str) -> Path:
```

- [ ] **Step 3: See the check pass**

Run: `make test`
Expected: last line `118 passed, 508 warnings in …`

Run: `grep -n "request\.[a-z_]" src/kb/servicer.py | grep -vE "requests\.[a-z]+\(|values\.signed\(|kb_pb2\.(Creation|Replacement|Addition|Removal)\("`
Expected: no output

Run: `ls src/kb/*.py | grep -vE "/(servicer|values|requests|client|cli)\.py" | xargs grep -nE "request\.|\.WhichOneof\(|kb_pb2\.[A-Za-z]+(Request|Operation|Creation|Replacement|Addition|Removal)\b"`
Expected: no output

Run: `grep -nE "message: str|role: str" src/kb/journal.py src/kb/store.py`
Expected: no output

Run: `wc -l src/kb/values.py src/kb/requests.py`
Expected: 224 and 182, both under 250

- [ ] **Step 4: Run the probe**

Run: `.venv/bin/python /tmp/kb-probe.py > /tmp/kb-probe-now.txt 2>&1; diff /tmp/kb-probe-baseline.txt /tmp/kb-probe-now.txt`
Expected: no output (the probe's output is identical to the baseline)

- [ ] **Step 5: Mark the slice green and commit**

In `docs/superpowers/plans/2026-09-24-kb-slices.md`, set slice 54's `Status:` to `green` and append a log line: `- <date> slice 54 green. <what its check showed>. Surprised by: <anything, or nothing>.`

```bash
git add -A src/kb docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 54: Every request field is a value before anything else sees it

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 3: Slice 55, Names live in one place

**Files:**
- Create: `src/kb/names.py`: the plain-name grammar, `slug`, `numbered`, `items`
- Modify: `src/kb/values.py`: uses `names.plain` and `names.slug`; its own `PLAIN` and `slug` go
- Modify: `src/kb/requests.py`: uses `names.slug`
- Modify: `src/kb/servicer.py`: `_name_items` and `_numbered` go; it calls `names.items` and `names.numbered`

**Interfaces:**
- Consumes: `requests.*` (task 2)
- Produces:
- `names.PLAIN`, `names.plain(text) -> bool`, `names.slug(title) -> str`, `names.numbered(name, taken: Callable[[str], bool]) -> str`, `names.items(schema, content, keep_named) -> None` (names every item of every part collection in place)
- `values.slug` no longer exists; every caller uses `names.slug`
- `requests.names` is renamed `requests.snapshotted`, since `requests.py` now imports the `names` module and a function of that name would shadow it (the scratch run's first try gave `107 failed` for exactly that)

- [ ] **Step 1: See the check fail**

Run: `grep -nE "\[a-z0-9\]|re\.sub|-\{number\}" src/kb/*.py`
Expected: lines in `values.py` (the grammar and `slug`) and `servicer.py` (`_numbered`), and no `names.py`

- [ ] **Step 2: Apply the change**

Save the patch as `/tmp/kb-slice-55.patch`, then run: `git apply --check /tmp/kb-slice-55.patch && git apply /tmp/kb-slice-55.patch`
Expected: no output

```diff
diff --git a/src/kb/names.py b/src/kb/names.py
new file mode 100644
index 0000000..071d878
--- /dev/null
+++ b/src/kb/names.py
@@ -0,0 +1,39 @@
+"""Names: the grammar of an artifact's and an item's name, the name a title gives, and the numbering that keeps a name
+free. Nothing here reads or writes; whether a name is taken is asked of the caller."""
+import re
+
+PLAIN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
+
+
+def plain(text: str) -> bool:
+    """Whether text is a plain name: lower-case letters and digits in runs joined by single hyphens."""
+    return PLAIN.fullmatch(text) is not None
+
+
+def slug(title: str) -> str:
+    """The name a title gives: lower-cased, every run of anything else a hyphen, none at either end."""
+    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
+
+
+def numbered(name: str, taken) -> str:
+    """The name, or, when taken says it is taken, that name with -2, -3 and so on added: the first it does not."""
+    candidate, number = name, 1
+    while taken(candidate):
+        number += 1
+        candidate = f"{name}-{number}"
+    return candidate
+
+
+def items(schema: dict, content: dict, keep_named: bool) -> None:
+    """Every item of every part collection given its name: from its title when it carries one, otherwise from its
+    place in the collection, counted from 1, with a number added as an artifact's name has when an item beside it
+    already has that name. On a write an item already carrying a name is the item of that name, moved or changed
+    where it stands, and keeps it; a name is minted once and never worked out again."""
+    for collection in schema.get("parts", {}):
+        found = content.get(collection, [])
+        taken = {item["id"] for item in found if keep_named and "id" in item}
+        for place, item in enumerate(found, start=1):
+            if keep_named and "id" in item:
+                continue
+            item["id"] = numbered(slug(item["title"]) if "title" in item else str(place), taken.__contains__)
+            taken.add(item["id"])
diff --git a/src/kb/requests.py b/src/kb/requests.py
index 8979f43..1dfc65d 100644
--- a/src/kb/requests.py
+++ b/src/kb/requests.py
@@ -5,7 +5,7 @@ from dataclasses import dataclass
 from datetime import datetime
 from pathlib import Path
 
-from kb import values
+from kb import names, values
 from kb.contract import kb_pb2
 from kb.values import Actor, ArtifactId, Content, Kind, Locator, Refused
 
@@ -120,7 +120,7 @@ def _create(creation: kb_pb2.Creation) -> Create:
         name, title_faults = values.named(kind, creation.title), ()
     except Refused as refused:
         name, title_faults = None, tuple(refused.faults)
-    at = f"{kind.name}/{values.slug(creation.title)}"
+    at = f"{kind.name}/{names.slug(creation.title)}"
     return Create(kind, creation.title, name, at, title_faults, values.content(creation.content))
 
 
@@ -171,7 +171,7 @@ def listing(request: kb_pb2.ListRequest) -> Listing:
     return Listing(values.kind(request.type), dict(request.fields), request.form == kb_pb2.ListRequest.IDS)
 
 
-def names(requested) -> list:
+def snapshotted(requested) -> list:
     """Each name a snapshot is given, converted or standing as its refusal."""
     converted = []
     for name in requested:
diff --git a/src/kb/servicer.py b/src/kb/servicer.py
index 44e90f3..eaf1905 100644
--- a/src/kb/servicer.py
+++ b/src/kb/servicer.py
@@ -7,7 +7,7 @@ import copy
 from datetime import datetime
 from typing import NamedTuple
 
-from kb import canonical, journal, requests, search, validation, values
+from kb import canonical, journal, names, requests, search, validation, values
 from kb.content import dumps, text
 from kb.contract import kb_pb2, kb_pb2_grpc
 from kb.metaschema import METASCHEMA
@@ -155,7 +155,7 @@ class KbServicer(kb_pb2_grpc.KbServicer):
         faults = validation.validate(at, {"title": creation.title, **content}, schema["schema"], draft)
         if faults:
             raise values.Refused(faults)
-        _name_items(schema["schema"], content, keep_named=False)
+        names.items(schema["schema"], content, keep_named=False)
         artifact = {
             **content,
             "id": str(artifact_id), "type": kind.name,
@@ -416,7 +416,7 @@ class KbServicer(kb_pb2_grpc.KbServicer):
         """One journal entry listing each artifact named with its version now and the fingerprint of its file, under
         the actor and the message given, in a commit of its own."""
         named, faults = [], []
-        for artifact_id in requests.names(request.artifacts):
+        for artifact_id in requests.snapshotted(request.artifacts):
             if isinstance(artifact_id, requests.Refusal):
                 faults += artifact_id.faults
                 continue
@@ -485,7 +485,7 @@ def _revise(draft: Draft, artifact_id: ArtifactId, current: dict, content: dict)
     faults = validation.validate(str(artifact_id), {"title": current["title"], **content}, schema["schema"], draft)
     if faults:
         raise values.Refused(faults)
-    _name_items(schema["schema"], content, keep_named=True)
+    names.items(schema["schema"], content, keep_named=True)
     artifact = {
         **content,
         "id": current["id"], "type": current["type"],
@@ -534,22 +534,7 @@ def _find_section(sections: list, title: str) -> dict | None:
 
 def _node_name(collection: str, item: dict) -> str:
     """How a place names an item: a section by its title's name, a part by its id."""
-    return values.slug(item["title"]) if collection == "sections" else item.get("id")
-
-
-def _name_items(schema: dict, content: dict, keep_named: bool) -> None:
-    """Every item of every part collection given its name: from its title when it carries one, otherwise from its
-    place in the collection, counted from 1, with a number added as an artifact's name has when an item beside it
-    already has that name. On a write an item already carrying a name is the item of that name, moved or changed
-    where it stands, and keeps it; a name is minted once and never worked out again."""
-    for collection in schema.get("parts", {}):
-        items = content.get(collection, [])
-        taken = {item["id"] for item in items if keep_named and "id" in item}
-        for place, item in enumerate(items, start=1):
-            if keep_named and "id" in item:
-                continue
-            item["id"] = _numbered(values.slug(item["title"]) if "title" in item else str(place), taken.__contains__)
-            taken.add(item["id"])
+    return names.slug(item["title"]) if collection == "sections" else item.get("id")
 
 
 def _not_found(artifact_id: ArtifactId) -> kb_pb2.Fault:
@@ -561,16 +546,7 @@ def _not_found(artifact_id: ArtifactId) -> kb_pb2.Fault:
 def _unclaimed(draft: Draft, named: ArtifactId) -> ArtifactId:
     """The name a title gives, or, when the store or an earlier change in the set already holds it, that name with
     -2, -3 and so on added: the first that nothing holds. What already holds a name keeps it."""
-    return ArtifactId(named.kind, _numbered(named.slug, lambda slug: draft.holds(ArtifactId(named.kind, slug))))
-
-
-def _numbered(name: str, taken) -> str:
-    """The name, or, when taken says it is taken, that name with -2, -3 and so on added: the first it does not."""
-    candidate, number = name, 1
-    while taken(candidate):
-        number += 1
-        candidate = f"{name}-{number}"
-    return candidate
+    return ArtifactId(named.kind, names.numbered(named.slug, lambda slug: draft.holds(ArtifactId(named.kind, slug))))
 
 
 def _summary_fields(artifact, schema):
diff --git a/src/kb/values.py b/src/kb/values.py
index 203cba3..1b405d2 100644
--- a/src/kb/values.py
+++ b/src/kb/values.py
@@ -3,18 +3,14 @@
 Storage takes only these values, never a string that came from a request, and `path` is the one place a file
 path is made from a name.
 """
-import re
 from dataclasses import dataclass
 from datetime import datetime, timezone
 from pathlib import Path
 
-from kb import canonical, discovery
+from kb import canonical, discovery, names
 from kb.content import loads
 from kb.contract import kb_pb2
 
-PLAIN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
-
-
 class Refused(ValueError):
     """A request value that does not convert. Carries every fault found."""
 
@@ -44,7 +40,7 @@ class Locator:
 
 
 def kind(text: str) -> Kind:
-    if not PLAIN.fullmatch(text):
+    if not names.plain(text):
         raise Refused([kb_pb2.Fault(
             rule="kind",
             message=f"a kind is a plain name of lower-case letters, digits and single hyphens, never a path; {text!r} is not",
@@ -54,7 +50,7 @@ def kind(text: str) -> Kind:
 
 def artifact_id(text: str) -> ArtifactId:
     kind_name, _, slug = text.partition("/")
-    if not (PLAIN.fullmatch(kind_name) and PLAIN.fullmatch(slug)):
+    if not (names.plain(kind_name) and names.plain(slug)):
         raise Refused([_not_a_plain_name(text)])
     return ArtifactId(Kind(kind_name), slug)
 
@@ -67,7 +63,7 @@ def locator(request: kb_pb2.Locator) -> Locator:
     except Refused as refused:
         faults += refused.faults
     place = tuple(request.path.split("/")) if request.path else ()
-    if not all(PLAIN.fullmatch(part) for part in place):
+    if not all(names.plain(part) for part in place):
         faults.append(kb_pb2.Fault(
             artifact=request.id, path=request.path, rule="locator",
             message=f"a place inside an artifact is named by parts of the same plain alphabet, or a collection and an item in it; {request.path!r} is not",
@@ -97,14 +93,14 @@ def since(text: str) -> datetime:
 
 def named(kind: Kind, title: str) -> ArtifactId:
     """The name kb gives an artifact of this kind from its title. A title is required and must leave a name."""
-    at = f"{kind.name}/{slug(title)}"
+    at = f"{kind.name}/{names.slug(title)}"
     if not title:
         raise Refused([kb_pb2.Fault(artifact=at, path="title", rule="title",
                                     message="an artifact cannot be created without a title")])
-    if not slug(title):
+    if not names.slug(title):
         raise Refused([kb_pb2.Fault(artifact=at, path="title", rule="title",
                                     message=f"a title must leave something to make a name from; {title!r} leaves nothing")])
-    return ArtifactId(kind, slug(title))
+    return ArtifactId(kind, names.slug(title))
 
 
 @dataclass(frozen=True)
@@ -206,10 +202,6 @@ def root(text: str) -> Path:
     return named
 
 
-def slug(title: str) -> str:
-    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
-
-
 def path(store_dir: Path, artifact_id: ArtifactId) -> Path:
     """The one function that makes a file path from a name."""
     if not isinstance(artifact_id, ArtifactId):
```

- [ ] **Step 3: See the check pass**

Run: `make test`
Expected: `118 passed, 508 warnings in …`

Run: `grep -nE "\[a-z0-9\]|re\.sub|-\{number\}" src/kb/*.py`
Expected: three lines, all in `src/kb/names.py`

Run: `grep -n "^import\|^from" src/kb/names.py`
Expected: `import re` only

- [ ] **Step 4: Run the probe**

Run: `.venv/bin/python /tmp/kb-probe.py > /tmp/kb-probe-now.txt 2>&1; diff /tmp/kb-probe-baseline.txt /tmp/kb-probe-now.txt`
Expected: no output (the probe's output is identical to the baseline)

- [ ] **Step 5: Mark the slice green and commit**

In `docs/superpowers/plans/2026-09-24-kb-slices.md`, set slice 55's `Status:` to `green` and append a log line: `- <date> slice 55 green. <what its check showed>. Surprised by: <anything, or nothing>.`

```bash
git add -A src/kb docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 55: Names live in one place

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 4: Slice 56, The write pipeline is its own module

**Files:**
- Create: `src/kb/write.py`: `start`, `land`, `record`, and the draft, serialise and write phases
- Create: `src/kb/edits.py`: what each operation does to the draft (`apply`, `Change`, `not_found`)
- Modify: `src/kb/validation.py`: gains `points_at(target, artifact_id)`, which was `servicer._points_at`
- Modify: `src/kb/servicer.py`: Init, Create, Write, Append, Delete, Apply and Snapshot's recording call `write`; the draft code goes

**Interfaces:**
- Consumes: `requests.*` operation values, `values.Signed` (task 2), `names.*` (task 3)
- Produces:
- `write.METASCHEMA_ID`, `write.start(root: Path, actor: Actor) -> None`, `write.land(store, operations: list, signed) -> kb_pb2.ApplyResponse` (this task; task 6 changes it), `write.record(store, read: list[dict], signed) -> str`
- `edits.Change(op, artifact_id, path="", item="")`, `edits.apply(draft, operation) -> Change`, `edits.not_found(artifact_id) -> kb_pb2.Fault`
- `validation.points_at(target: str, artifact_id) -> bool`

The write pipeline alone came to 268 lines in the scratch run, over the 250 limit, so what each operation does to the draft is split into `edits.py`. Both land under 250 (100 and 177).

- [ ] **Step 1: See the check fail**

Run: `grep -nE "Draft|journal\.(write|snapshot)|\.commit\(|\.save\(|\.remove\(" src/kb/servicer.py | wc -l`
Expected: a non-zero count (the draft, journal writes, saves and commits are all in the servicer)

- [ ] **Step 2: Apply the change**

Save the patch as `/tmp/kb-slice-56.patch`, then run: `git apply --check /tmp/kb-slice-56.patch && git apply /tmp/kb-slice-56.patch`
Expected: no output

```diff
diff --git a/src/kb/edits.py b/src/kb/edits.py
new file mode 100644
index 0000000..bd0a0ac
--- /dev/null
+++ b/src/kb/edits.py
@@ -0,0 +1,177 @@
+"""What each operation of a set does to the draft: a new artifact, a whole or placed replacement, an item added to a
+collection, an artifact removed. Each is checked against the draft as the operations before it left it, and refused
+with every fault it finds."""
+import copy
+from typing import NamedTuple
+
+from kb import canonical, names, requests, validation, values
+from kb.contract import kb_pb2
+from kb.store import Draft
+from kb.values import ArtifactId, Kind, Refused
+
+
+class Change(NamedTuple):
+    """What one operation did, to which artifact, at which place in it, and, for an item added, the item's name."""
+    op: str
+    artifact_id: ArtifactId
+    path: str = ""
+    item: str = ""
+
+
+def apply(draft: Draft, operation) -> Change:
+    """One operation applied to the draft. Returns what it did; raises Refused."""
+    if isinstance(operation, requests.Create):
+        return Change("create", _create(draft, operation))
+    if isinstance(operation, requests.Add):
+        return _append(draft, operation)
+    if isinstance(operation, requests.Remove):
+        return _delete(draft, operation)
+    return Change("write", _replace(draft, operation))
+
+
+def _create(draft: Draft, creation: requests.Create) -> ArtifactId:
+    kind = creation.kind
+    if not draft.holds(ArtifactId(Kind("schema"), kind.name)):
+        raise Refused([kb_pb2.Fault(
+            rule="kind", message=f"a kind must name a type the store holds; the store holds no type called {kind.name!r}",
+        )])
+    at, faults = creation.at, list(creation.title_faults)
+    if creation.name is not None:
+        artifact_id = _unclaimed(draft, creation.name)
+        at = str(artifact_id)
+    faults += creation.content.refusal(at)
+    if faults:
+        raise Refused(faults)
+    content = creation.content.tree
+    schema = draft.schema(kind)
+    faults = validation.validate(at, {"title": creation.title, **content}, schema["schema"], draft)
+    if faults:
+        raise Refused(faults)
+    names.items(schema["schema"], content, keep_named=False)
+    artifact = {
+        **content,
+        "id": str(artifact_id), "type": kind.name,
+        "schema_version": schema["version"], "revision": 1, "title": creation.title,
+    }
+    draft.put(artifact_id, canonical.order(artifact, schema["schema"]))
+    return artifact_id
+
+
+def _replace(draft: Draft, replacement: requests.Replace) -> ArtifactId:
+    locator = replacement.locator
+    if not draft.holds(locator.id):
+        raise Refused([not_found(locator.id)])
+    if replacement.content.problems:
+        raise Refused(replacement.content.refusal(str(locator.id)))
+    content, current = replacement.content.tree, draft.load(locator.id)
+    if locator.place:
+        content = _placed(current, locator, content)
+    _revise(draft, locator.id, current, content)
+    return locator.id
+
+
+def _append(draft: Draft, addition: requests.Add) -> Change:
+    """One item put at the end of a collection the artifact's type declares, and named there."""
+    locator = addition.locator
+    if not draft.holds(locator.id):
+        raise Refused([not_found(locator.id)])
+    if addition.item.problems:
+        raise Refused(addition.item.refusal(str(locator.id)))
+    item, collection = addition.item.tree, "/".join(locator.place)
+    if collection not in draft.schema(locator.id.kind)["schema"].get("parts", {}):
+        raise Refused([kb_pb2.Fault(
+            artifact=str(locator.id), path=collection, rule="not-found",
+            message=f"{str(locator.id)!r} holds no collection called {collection!r}",
+        )])
+    current = draft.load(locator.id)
+    content = _content_of(current)
+    content.setdefault(collection, []).append(item)
+    _revise(draft, locator.id, current, content)
+    return Change("append", locator.id, f"{collection}/{item['id']}", item["id"])
+
+
+def _delete(draft: Draft, removal: requests.Remove) -> Change:
+    """A whole artifact taken out of the draft, refused with one fault for each link that still points at it."""
+    locator = removal.locator
+    if not draft.holds(locator.id):
+        raise Refused([not_found(locator.id)])
+    if locator.place:
+        raise Refused([kb_pb2.Fault(
+            artifact=str(locator.id), path="/".join(locator.place), rule="locator",
+            message=f"a removal takes out a whole artifact; {'/'.join(locator.place)!r} is a place inside {str(locator.id)!r}",
+        )])
+    blocking = []
+    for other_id in draft.ids():
+        if other_id == locator.id:
+            continue
+        schema = draft.schema(other_id.kind)["schema"]
+        for field, place, target in validation.links(draft.load(other_id), schema, draft):
+            if validation.points_at(target, locator.id):
+                blocking.append(kb_pb2.Fault(
+                    artifact=str(other_id), path=place, rule="on_delete",
+                    message=f"{str(locator.id)!r} cannot be removed while {str(other_id)!r} points at it at {place!r}",
+                ))
+    if blocking:
+        raise Refused(blocking)
+    draft.remove(locator.id)
+    return Change("delete", locator.id)
+
+
+def _revise(draft: Draft, artifact_id: ArtifactId, current: dict, content: dict) -> None:
+    """The artifact's next version put in the draft: the content checked against the current version of its type,
+    its items named, its version up by one, its title kept. Raises Refused with every fault."""
+    schema = draft.schema(artifact_id.kind)
+    faults = validation.validate(str(artifact_id), {"title": current["title"], **content}, schema["schema"], draft)
+    if faults:
+        raise Refused(faults)
+    names.items(schema["schema"], content, keep_named=True)
+    artifact = {
+        **content,
+        "id": current["id"], "type": current["type"],
+        "schema_version": schema["version"], "revision": current["revision"] + 1, "title": current["title"],
+    }
+    draft.put(artifact_id, canonical.order(artifact, schema["schema"]))
+
+
+def _content_of(artifact: dict) -> dict:
+    """A copy of what an artifact holds but its identity keys, to be changed without changing it."""
+    return copy.deepcopy({key: value for key, value in artifact.items() if key not in canonical.IDENTITY})
+
+
+def _placed(artifact: dict, locator: values.Locator, node: dict) -> dict:
+    """The artifact's content with the node at the locator's place replaced by the one given. A place is pairs of a
+    list and an item in it, a section named by its title's name and a part by its id, and may end in a field."""
+    content = _content_of(artifact)
+    holder, steps = content, list(locator.place)
+    while len(steps) > 1:
+        collection, name = steps.pop(0), steps.pop(0)
+        found = holder.get(collection, [])
+        index = next((index for index, item in enumerate(found) if _node_name(collection, item) == name), None)
+        if index is None:
+            raise Refused([kb_pb2.Fault(
+                artifact=str(locator.id), path="/".join(locator.place), rule="not-found",
+                message=f"{str(locator.id)!r} holds nothing at {'/'.join(locator.place)!r}",
+            )])
+        if not steps:
+            found[index] = node if collection == "sections" else {"id": name, **node}
+            return content
+        holder = found[index]
+    holder[steps[0]] = node
+    return content
+
+
+def _node_name(collection: str, item: dict) -> str:
+    """How a place names an item: a section by its title's name, a part by its id."""
+    return names.slug(item["title"]) if collection == "sections" else item.get("id")
+
+
+def _unclaimed(draft: Draft, named: ArtifactId) -> ArtifactId:
+    """The name a title gives, or, when the store or an earlier change in the set already holds it, that name with
+    -2, -3 and so on added: the first that nothing holds. What already holds a name keeps it."""
+    return ArtifactId(named.kind, names.numbered(named.slug, lambda slug: draft.holds(ArtifactId(named.kind, slug))))
+
+
+def not_found(artifact_id: ArtifactId) -> kb_pb2.Fault:
+    return kb_pb2.Fault(
+        artifact=str(artifact_id), rule="not-found", message=f"the store holds nothing by the name {str(artifact_id)!r}",
+    )
diff --git a/src/kb/servicer.py b/src/kb/servicer.py
index eaf1905..7a1d257 100644
--- a/src/kb/servicer.py
+++ b/src/kb/servicer.py
@@ -3,26 +3,14 @@
 Each rpc first turns what the request carries into checked values (kb.values); nothing past that point sees a
 string that came from the request.
 """
-import copy
 from datetime import datetime
-from typing import NamedTuple
 
-from kb import canonical, journal, names, requests, search, validation, values
+from kb import canonical, journal, requests, search, validation, values, write
 from kb.content import dumps, text
 from kb.contract import kb_pb2, kb_pb2_grpc
-from kb.metaschema import METASCHEMA
-from kb.store import Draft, Store, Unreadable
-from kb.values import ArtifactId, Kind, Signed
-
-METASCHEMA_ID = ArtifactId(Kind("schema"), "schema")
-
-
-class Change(NamedTuple):
-    """What one operation did, to which artifact, at which place in it, and, for an item added, the item's name."""
-    op: str
-    artifact_id: ArtifactId
-    path: str = ""
-    item: str = ""
+from kb.store import Store, Unreadable
+from kb.values import ArtifactId
+from kb.edits import not_found as _not_found
 
 
 class KbServicer(kb_pb2_grpc.KbServicer):
@@ -35,193 +23,39 @@ class KbServicer(kb_pb2_grpc.KbServicer):
             actor, root = requests.starting(request)
         except values.Refused as refused:
             return kb_pb2.InitResponse(faults=refused.faults)
-        store, signed = Store(root), Signed(actor, "initialise store")
-        store.start()
-        metaschema = {"id": str(METASCHEMA_ID), "type": "schema", "schema_version": 1, "revision": 1, **METASCHEMA}
-        path = store.save(METASCHEMA_ID, canonical.dump(canonical.order(metaschema, METASCHEMA["schema"])))
-        entry = journal.write(
-            store.dir, signed=signed, op="create", artifact=str(METASCHEMA_ID), path="",
-            revision=1, schema_version=1, written=path,
-        )
-        store.commit([store.dir / "store.yaml", path, entry], signed)
+        write.start(root, actor)
         return kb_pb2.InitResponse()
 
     def Create(self, request, context):
         creation = kb_pb2.Creation(type=request.type, title=request.title, content=request.content)
-        landed = self._land(requests.operations([kb_pb2.Operation(create=creation)]), values.signed(request.actor, request.message))
+        landed = write.land(self._store, requests.operations([kb_pb2.Operation(create=creation)]), values.signed(request.actor, request.message))
         if landed.faults:
             return kb_pb2.CreateResponse(faults=landed.faults)
         return kb_pb2.CreateResponse(id=landed.results[0].id, revision=landed.results[0].revision)
 
     def Write(self, request, context):
         replacement = kb_pb2.Replacement(locator=request.locator, content=request.content)
-        landed = self._land(requests.operations([kb_pb2.Operation(write=replacement)]), values.signed(request.actor, request.message))
+        landed = write.land(self._store, requests.operations([kb_pb2.Operation(write=replacement)]), values.signed(request.actor, request.message))
         if landed.faults:
             return kb_pb2.WriteResponse(faults=landed.faults)
         return kb_pb2.WriteResponse(revision=landed.results[0].revision)
 
     def Append(self, request, context):
         addition = kb_pb2.Addition(locator=request.locator, content=request.content)
-        landed = self._land(requests.operations([kb_pb2.Operation(append=addition)]), values.signed(request.actor, request.message))
+        landed = write.land(self._store, requests.operations([kb_pb2.Operation(append=addition)]), values.signed(request.actor, request.message))
         if landed.faults:
             return kb_pb2.AppendResponse(faults=landed.faults)
         return kb_pb2.AppendResponse(id=landed.results[0].item, revision=landed.results[0].revision)
 
     def Delete(self, request, context):
         removal = kb_pb2.Removal(locator=request.locator)
-        landed = self._land(requests.operations([kb_pb2.Operation(delete=removal)]), values.signed(request.actor, request.message))
+        landed = write.land(self._store, requests.operations([kb_pb2.Operation(delete=removal)]), values.signed(request.actor, request.message))
         if landed.faults:
             return kb_pb2.DeleteResponse(faults=landed.faults)
         return kb_pb2.DeleteResponse(revision=landed.results[0].revision)
 
     def Apply(self, request, context):
-        return self._land(requests.operations(request.operations), values.signed(request.actor, request.message))
-
-    def _land(self, operations: list, signed: Signed) -> kb_pb2.ApplyResponse:
-        """The write path. Each operation is applied in order to a draft of the store and checked there, against the
-        store as the operations before it left it; only when every one passes is anything written, each artifact
-        saved, one journal entry per operation naming the set, and one commit.
-
-        A fault anywhere refuses the whole set with every fault found, and nothing is written.
-        """
-        draft = Draft(self._store)
-        touched, faults = [], []
-        for operation in operations:
-            if isinstance(operation, requests.Refusal):
-                faults += operation.faults
-                continue
-            try:
-                touched.append(self._apply(draft, operation))
-            except values.Refused as refused:
-                faults += refused.faults
-        if faults:
-            return kb_pb2.ApplyResponse(faults=faults)
-        texts = []
-        for change in touched:
-            if change.op == "delete":
-                texts.append((change, None))
-                continue
-            try:
-                texts.append((change, canonical.dump(draft.load(change.artifact_id))))
-            except canonical.NotCanonical as fault:
-                faults.append(kb_pb2.Fault(artifact=str(change.artifact_id), rule="content", message=str(fault)))
-        if faults:
-            return kb_pb2.ApplyResponse(faults=faults)
-        written, results, batch = [], [], ""
-        for seq, (change, text) in enumerate(texts, start=1):
-            if text is None:
-                removed = self._store.load(change.artifact_id)
-                revision, schema_version = removed["revision"] + 1, removed["schema_version"]
-                path, saved = self._store.remove(change.artifact_id), None
-            else:
-                artifact = draft.load(change.artifact_id)
-                revision, schema_version = artifact["revision"], artifact["schema_version"]
-                path = saved = self._store.save(change.artifact_id, text)
-            entry = journal.write(
-                self._store.dir, signed=signed, op=change.op, artifact=str(change.artifact_id), path=change.path,
-                revision=revision, schema_version=schema_version, written=saved, seq=seq, batch=batch,
-            )
-            batch = batch or entry.stem
-            written += [path, entry]
-            results.append(kb_pb2.Result(id=str(change.artifact_id), revision=revision, item=change.item))
-        self._store.commit(written, signed)
-        return kb_pb2.ApplyResponse(batch=batch, results=results)
-
-    def _apply(self, draft: Draft, operation) -> Change:
-        """One operation applied to the draft. Returns what it did; raises values.Refused."""
-        if isinstance(operation, requests.Create):
-            return Change("create", self._create(draft, operation))
-        if isinstance(operation, requests.Add):
-            return self._append(draft, operation)
-        if isinstance(operation, requests.Remove):
-            return self._delete(draft, operation)
-        return Change("write", self._replace(draft, operation))
-
-    def _create(self, draft: Draft, creation: requests.Create) -> ArtifactId:
-        kind = creation.kind
-        if not draft.holds(ArtifactId(Kind("schema"), kind.name)):
-            raise values.Refused([kb_pb2.Fault(
-                rule="kind", message=f"a kind must name a type the store holds; the store holds no type called {kind.name!r}",
-            )])
-        at, faults = creation.at, list(creation.title_faults)
-        if creation.name is not None:
-            artifact_id = _unclaimed(draft, creation.name)
-            at = str(artifact_id)
-        faults += creation.content.refusal(at)
-        if faults:
-            raise values.Refused(faults)
-        content = creation.content.tree
-        schema = draft.schema(kind)
-        faults = validation.validate(at, {"title": creation.title, **content}, schema["schema"], draft)
-        if faults:
-            raise values.Refused(faults)
-        names.items(schema["schema"], content, keep_named=False)
-        artifact = {
-            **content,
-            "id": str(artifact_id), "type": kind.name,
-            "schema_version": schema["version"], "revision": 1, "title": creation.title,
-        }
-        draft.put(artifact_id, canonical.order(artifact, schema["schema"]))
-        return artifact_id
-
-    def _replace(self, draft: Draft, replacement: requests.Replace) -> ArtifactId:
-        locator = replacement.locator
-        if not draft.holds(locator.id):
-            raise values.Refused([_not_found(locator.id)])
-        if replacement.content.problems:
-            raise values.Refused(replacement.content.refusal(str(locator.id)))
-        content = replacement.content.tree
-        current = draft.load(locator.id)
-        if locator.place:
-            content = _placed(current, locator, content)
-        _revise(draft, locator.id, current, content)
-        return locator.id
-
-    def _append(self, draft: Draft, addition: requests.Add) -> Change:
-        """One item put at the end of a collection the artifact's type declares, and named there."""
-        locator = addition.locator
-        if not draft.holds(locator.id):
-            raise values.Refused([_not_found(locator.id)])
-        if addition.item.problems:
-            raise values.Refused(addition.item.refusal(str(locator.id)))
-        item = addition.item.tree
-        collection = "/".join(locator.place)
-        if collection not in draft.schema(locator.id.kind)["schema"].get("parts", {}):
-            raise values.Refused([kb_pb2.Fault(
-                artifact=str(locator.id), path=collection, rule="not-found",
-                message=f"{str(locator.id)!r} holds no collection called {collection!r}",
-            )])
-        current = draft.load(locator.id)
-        content = _content_of(current)
-        content.setdefault(collection, []).append(item)
-        _revise(draft, locator.id, current, content)
-        return Change("append", locator.id, f"{collection}/{item['id']}", item["id"])
-
-    def _delete(self, draft: Draft, removal: requests.Remove) -> Change:
-        """A whole artifact taken out of the draft, refused with one fault for each link that still points at it."""
-        locator = removal.locator
-        if not draft.holds(locator.id):
-            raise values.Refused([_not_found(locator.id)])
-        if locator.place:
-            raise values.Refused([kb_pb2.Fault(
-                artifact=str(locator.id), path="/".join(locator.place), rule="locator",
-                message=f"a removal takes out a whole artifact; {'/'.join(locator.place)!r} is a place inside {str(locator.id)!r}",
-            )])
-        blocking = []
-        for other_id in draft.ids():
-            if other_id == locator.id:
-                continue
-            schema = draft.schema(other_id.kind)["schema"]
-            for field, place, target in validation.links(draft.load(other_id), schema, draft):
-                if _points_at(target, locator.id):
-                    blocking.append(kb_pb2.Fault(
-                        artifact=str(other_id), path=place, rule="on_delete",
-                        message=f"{str(locator.id)!r} cannot be removed while {str(other_id)!r} points at it at {place!r}",
-                    ))
-        if blocking:
-            raise values.Refused(blocking)
-        draft.remove(locator.id)
-        return Change("delete", locator.id)
+        return write.land(self._store, requests.operations(request.operations), values.signed(request.actor, request.message))
 
     def Read(self, request, context):
         try:
@@ -394,7 +228,7 @@ class KbServicer(kb_pb2_grpc.KbServicer):
             other = self._store.load(other_id)
             schema = self._store.schema(other_id.kind)["schema"]
             for field, _, target in validation.links(other, schema, self._store):
-                if _points_at(target, artifact_id):
+                if validation.points_at(target, artifact_id):
                     found.append((field, other_id))
         return found
 
@@ -434,9 +268,7 @@ class KbServicer(kb_pb2_grpc.KbServicer):
             for artifact_id in named
         ]
         signed = values.signed(request.actor, request.message)
-        entry = journal.snapshot(self._store.dir, signed=signed, read=read)
-        self._store.commit([entry], signed)
-        return kb_pb2.SnapshotResponse(entry=entry.stem)
+        return kb_pb2.SnapshotResponse(entry=write.record(self._store, read, signed))
 
     def _stub(self, field, target_id: ArtifactId):
         target = self._store.load(target_id)
@@ -457,11 +289,6 @@ class KbServicer(kb_pb2_grpc.KbServicer):
         return counts
 
 
-def _points_at(target: str, artifact_id: ArtifactId) -> bool:
-    """Whether a link lands on the artifact or on a part inside it."""
-    return target.partition("#")[0] == str(artifact_id)
-
-
 def _holds(artifact: dict, fields) -> bool:
     """Whether each field named holds the value given, compared as the text the value is written as."""
     return all(field in artifact and text(artifact[field]) == value for field, value in fields.items())
@@ -478,49 +305,6 @@ def _entry(entry: dict) -> kb_pb2.Entry:
     )
 
 
-def _revise(draft: Draft, artifact_id: ArtifactId, current: dict, content: dict) -> None:
-    """The artifact's next version put in the draft: the content checked against the current version of its type,
-    its items named, its version up by one, its title kept. Raises values.Refused with every fault."""
-    schema = draft.schema(artifact_id.kind)
-    faults = validation.validate(str(artifact_id), {"title": current["title"], **content}, schema["schema"], draft)
-    if faults:
-        raise values.Refused(faults)
-    names.items(schema["schema"], content, keep_named=True)
-    artifact = {
-        **content,
-        "id": current["id"], "type": current["type"],
-        "schema_version": schema["version"], "revision": current["revision"] + 1, "title": current["title"],
-    }
-    draft.put(artifact_id, canonical.order(artifact, schema["schema"]))
-
-
-def _content_of(artifact: dict) -> dict:
-    """A copy of what an artifact holds but its identity keys, to be changed without changing it."""
-    return copy.deepcopy({key: value for key, value in artifact.items() if key not in canonical.IDENTITY})
-
-
-def _placed(artifact: dict, locator: values.Locator, node: dict) -> dict:
-    """The artifact's content with the node at the locator's place replaced by the one given. A place is pairs of a
-    list and an item in it, a section named by its title's name and a part by its id, and may end in a field."""
-    content = _content_of(artifact)
-    holder, steps = content, list(locator.place)
-    while len(steps) > 1:
-        collection, name = steps.pop(0), steps.pop(0)
-        items = holder.get(collection, [])
-        index = next((index for index, item in enumerate(items) if _node_name(collection, item) == name), None)
-        if index is None:
-            raise values.Refused([kb_pb2.Fault(
-                artifact=str(locator.id), path="/".join(locator.place), rule="not-found",
-                message=f"{str(locator.id)!r} holds nothing at {'/'.join(locator.place)!r}",
-            )])
-        if not steps:
-            items[index] = node if collection == "sections" else {"id": name, **node}
-            return content
-        holder = items[index]
-    holder[steps[0]] = node
-    return content
-
-
 def _find_section(sections: list, title: str) -> dict | None:
     """The first section titled so, looking at each section before the sections inside it."""
     for section in sections:
@@ -532,23 +316,6 @@ def _find_section(sections: list, title: str) -> dict | None:
     return None
 
 
-def _node_name(collection: str, item: dict) -> str:
-    """How a place names an item: a section by its title's name, a part by its id."""
-    return names.slug(item["title"]) if collection == "sections" else item.get("id")
-
-
-def _not_found(artifact_id: ArtifactId) -> kb_pb2.Fault:
-    return kb_pb2.Fault(
-        artifact=str(artifact_id), rule="not-found", message=f"the store holds nothing by the name {str(artifact_id)!r}",
-    )
-
-
-def _unclaimed(draft: Draft, named: ArtifactId) -> ArtifactId:
-    """The name a title gives, or, when the store or an earlier change in the set already holds it, that name with
-    -2, -3 and so on added: the first that nothing holds. What already holds a name keeps it."""
-    return ArtifactId(named.kind, names.numbered(named.slug, lambda slug: draft.holds(ArtifactId(named.kind, slug))))
-
-
 def _summary_fields(artifact, schema):
     return {name: artifact[name] for name in schema.get("summary", []) if name in artifact}
 
diff --git a/src/kb/validation.py b/src/kb/validation.py
index 951a38e..2ee2942 100644
--- a/src/kb/validation.py
+++ b/src/kb/validation.py
@@ -109,6 +109,11 @@ def links(artifact: dict, schema: dict, corpus) -> list[tuple[str, str, str]]:
     return found
 
 
+def points_at(target: str, artifact_id) -> bool:
+    """Whether a link lands on the artifact or on a part inside it."""
+    return target.partition("#")[0] == str(artifact_id)
+
+
 def _lands(target: str, ref: dict, corpus) -> bool:
     """Whether a link lands: on an artifact of a kind the field allows that the corpus holds, and, when it names a
     place after `#` and the field allows parts, on a part that artifact holds."""
diff --git a/src/kb/write.py b/src/kb/write.py
new file mode 100644
index 0000000..f2c8265
--- /dev/null
+++ b/src/kb/write.py
@@ -0,0 +1,100 @@
+"""The write path: a set of operations applied in order to a draft of the store and checked there, against the store
+as the operations before it left it; only when every one passes is anything written, each artifact saved, one journal
+entry per operation naming the set, and one commit. A fault anywhere refuses the whole set with every fault found,
+and nothing is written. Starting a store and recording a snapshot write and commit here too."""
+from pathlib import Path
+
+from kb import canonical, edits, journal, requests
+from kb.contract import kb_pb2
+from kb.metaschema import METASCHEMA
+from kb.edits import Change
+from kb.store import Draft, Store
+from kb.values import Actor, ArtifactId, Kind, Refused, Signed
+
+METASCHEMA_ID = ArtifactId(Kind("schema"), "schema")
+
+
+def start(root: Path, actor: Actor) -> None:
+    """A new store at root, holding the type of types, its start in the journal and in one commit."""
+    store, signed = Store(root), Signed(actor, "initialise store")
+    store.start()
+    metaschema = {"id": str(METASCHEMA_ID), "type": "schema", "schema_version": 1, "revision": 1, **METASCHEMA}
+    path = store.save(METASCHEMA_ID, canonical.dump(canonical.order(metaschema, METASCHEMA["schema"])))
+    entry = journal.write(
+        store.dir, signed=signed, op="create", artifact=str(METASCHEMA_ID), path="",
+        revision=1, schema_version=1, written=path,
+    )
+    store.commit([store.dir / "store.yaml", path, entry], signed)
+
+
+def land(store: Store, operations: list, signed: Signed) -> kb_pb2.ApplyResponse:
+    """The set drafted, serialised, then written and committed; refused with every fault before anything is written."""
+    try:
+        draft, changes = _drafted(store, operations)
+        texts = _serialised(draft, changes)
+    except Refused as refused:
+        return kb_pb2.ApplyResponse(faults=refused.faults)
+    return _written(store, draft, texts, signed)
+
+
+def record(store: Store, read: list[dict], signed: Signed) -> str:
+    """One journal entry listing what a piece of work read, in a commit of its own. Returns the entry's id."""
+    entry = journal.snapshot(store.dir, signed=signed, read=read)
+    store.commit([entry], signed)
+    return entry.stem
+
+
+def _drafted(store: Store, operations: list) -> tuple[Draft, list[Change]]:
+    """Every operation applied in order to a draft; refused with the faults of every operation that fails."""
+    draft = Draft(store)
+    changes, faults = [], []
+    for operation in operations:
+        if isinstance(operation, requests.Refusal):
+            faults += operation.faults
+            continue
+        try:
+            changes.append(edits.apply(draft, operation))
+        except Refused as refused:
+            faults += refused.faults
+    if faults:
+        raise Refused(faults)
+    return draft, changes
+
+
+def _serialised(draft: Draft, changes: list[Change]) -> list[tuple[Change, str | None]]:
+    """Each change with the canonical text of what it leaves, None for a removal; refused if any cannot be written."""
+    texts, faults = [], []
+    for change in changes:
+        if change.op == "delete":
+            texts.append((change, None))
+            continue
+        try:
+            texts.append((change, canonical.dump(draft.load(change.artifact_id))))
+        except canonical.NotCanonical as fault:
+            faults.append(kb_pb2.Fault(artifact=str(change.artifact_id), rule="content", message=str(fault)))
+    if faults:
+        raise Refused(faults)
+    return texts
+
+
+def _written(store: Store, draft: Draft, texts: list, signed: Signed) -> kb_pb2.ApplyResponse:
+    """Each file saved or removed, its journal entry written naming the set, and all of it in one commit."""
+    written, results, batch = [], [], ""
+    for seq, (change, text) in enumerate(texts, start=1):
+        if text is None:
+            removed = store.load(change.artifact_id)
+            revision, schema_version = removed["revision"] + 1, removed["schema_version"]
+            path, saved = store.remove(change.artifact_id), None
+        else:
+            artifact = draft.load(change.artifact_id)
+            revision, schema_version = artifact["revision"], artifact["schema_version"]
+            path = saved = store.save(change.artifact_id, text)
+        entry = journal.write(
+            store.dir, signed=signed, op=change.op, artifact=str(change.artifact_id), path=change.path,
+            revision=revision, schema_version=schema_version, written=saved, seq=seq, batch=batch,
+        )
+        batch = batch or entry.stem
+        written += [path, entry]
+        results.append(kb_pb2.Result(id=str(change.artifact_id), revision=revision, item=change.item))
+    store.commit(written, signed)
+    return kb_pb2.ApplyResponse(batch=batch, results=results)
```

- [ ] **Step 3: See the check pass**

Run: `make test`
Expected: `118 passed, 508 warnings in …`

Run: `grep -nE "Draft|journal\.(write|snapshot)|\.commit\(|\.save\(|\.remove\(" src/kb/servicer.py`
Expected: no output

Run: `wc -l src/kb/write.py src/kb/edits.py src/kb/servicer.py`
Expected: 100, 177, 321

- [ ] **Step 4: Run the probe**

Run: `.venv/bin/python /tmp/kb-probe.py > /tmp/kb-probe-now.txt 2>&1; diff /tmp/kb-probe-baseline.txt /tmp/kb-probe-now.txt`
Expected: no output (the probe's output is identical to the baseline)

- [ ] **Step 5: Mark the slice green and commit**

In `docs/superpowers/plans/2026-09-24-kb-slices.md`, set slice 56's `Status:` to `green` and append a log line: `- <date> slice 56 green. <what its check showed>. Surprised by: <anything, or nothing>.`

```bash
git add -A src/kb docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 56: The write pipeline is its own module

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 5: Slice 57, Nothing is read from disk once a set starts writing

**Files:**
- Modify: `src/kb/journal.py`: `write` takes `text: str | None` and fingerprints it with a new `fingerprint(text)`; `digest(path)` stays for snapshots
- Modify: `src/kb/edits.py`: `Change` gains `revision` and `schema_version`, set by a removal from the draft before it removes
- Modify: `src/kb/write.py`: a `Landing` per change settles the text and versions in the serialise phase; the write phase reads nothing

**Interfaces:**
- Consumes: `write._written`, `edits.Change` (task 4)
- Produces:
- `journal.fingerprint(text: str) -> str`, `journal.write(..., text: str | None, ...)` (replaces `written: Path | None`)
- `edits.Change(op, artifact_id, path="", item="", revision=0, schema_version=0)`
- `write.Landing(change, text, revision, schema_version)`; `write._written(store, landings, signed)`

- [ ] **Step 1: See the check fail**

Save the phase scan (below) as `/tmp/kb-phase-reads.py`, then run: `.venv/bin/python /tmp/kb-phase-reads.py`
Expected: `['load', 'load']`

```python
import ast
tree = ast.parse(open("src/kb/write.py").read())
phase = next(f for f in tree.body if isinstance(f, ast.FunctionDef) and f.name == "_written")
reads = {"load", "holds", "ids", "artifacts", "schema", "read_text", "read_bytes"}
found = [n.func.attr for n in ast.walk(phase)
         if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in reads]
print(found or "no reads")
```

- [ ] **Step 2: Apply the change**

Save the patch as `/tmp/kb-slice-57.patch`, then run: `git apply --check /tmp/kb-slice-57.patch && git apply /tmp/kb-slice-57.patch`
Expected: no output

```diff
diff --git a/src/kb/edits.py b/src/kb/edits.py
index bd0a0ac..40d2750 100644
--- a/src/kb/edits.py
+++ b/src/kb/edits.py
@@ -11,11 +11,14 @@ from kb.values import ArtifactId, Kind, Refused
 
 
 class Change(NamedTuple):
-    """What one operation did, to which artifact, at which place in it, and, for an item added, the item's name."""
+    """What one operation did, to which artifact, at which place in it, and, for an item added, the item's name. A
+    removal carries the version its entry records and the version of the type it was last checked against."""
     op: str
     artifact_id: ArtifactId
     path: str = ""
     item: str = ""
+    revision: int = 0
+    schema_version: int = 0
 
 
 def apply(draft: Draft, operation) -> Change:
@@ -113,8 +116,9 @@ def _delete(draft: Draft, removal: requests.Remove) -> Change:
                 ))
     if blocking:
         raise Refused(blocking)
+    removed = draft.load(locator.id)
     draft.remove(locator.id)
-    return Change("delete", locator.id)
+    return Change("delete", locator.id, revision=removed["revision"] + 1, schema_version=removed["schema_version"])
 
 
 def _revise(draft: Draft, artifact_id: ArtifactId, current: dict, content: dict) -> None:
diff --git a/src/kb/journal.py b/src/kb/journal.py
index d7ffa26..4538745 100644
--- a/src/kb/journal.py
+++ b/src/kb/journal.py
@@ -13,14 +13,19 @@ def now() -> datetime:
 
 
 def digest(path: Path) -> str:
-    """The fingerprint of what was written: sha256 of the file's bytes after the write."""
+    """The fingerprint of a stored file: sha256 of its bytes."""
     return hashlib.sha256(path.read_bytes()).hexdigest()
 
 
+def fingerprint(text: str) -> str:
+    """The fingerprint of text about to be written: sha256 of the bytes it is written as."""
+    return hashlib.sha256(text.encode()).hexdigest()
+
+
 def write(store_dir: Path, *, signed: Signed, op: str, artifact: str, path: str, revision: int,
-          schema_version: int, written: Path | None, seq: int = 1, batch: str = "") -> Path:
+          schema_version: int, text: str | None, seq: int = 1, batch: str = "") -> Path:
     """Write one entry and return its file; its stem is the entry's id. A change made alone names itself as its batch.
-    A removal wrote nothing, so its entry's fingerprint is empty."""
+    The fingerprint is of the text the change writes; a removal writes none, so its entry's fingerprint is empty."""
     at = now()
     entry_id = f"{at.strftime('%Y%m%dT%H%M%S%fZ')}-{seq}"
     entry = {
@@ -32,7 +37,7 @@ def write(store_dir: Path, *, signed: Signed, op: str, artifact: str, path: str,
         "path": path,
         "revision": revision,
         "schema_version": schema_version,
-        "digest": digest(written) if written is not None else "",
+        "digest": fingerprint(text) if text is not None else "",
         "message": signed.message,
         "batch": batch or entry_id,
     }
diff --git a/src/kb/write.py b/src/kb/write.py
index f2c8265..f0b0312 100644
--- a/src/kb/write.py
+++ b/src/kb/write.py
@@ -3,6 +3,7 @@ as the operations before it left it; only when every one passes is anything writ
 entry per operation naming the set, and one commit. A fault anywhere refuses the whole set with every fault found,
 and nothing is written. Starting a store and recording a snapshot write and commit here too."""
 from pathlib import Path
+from typing import NamedTuple
 
 from kb import canonical, edits, journal, requests
 from kb.contract import kb_pb2
@@ -14,15 +15,24 @@ from kb.values import Actor, ArtifactId, Kind, Refused, Signed
 METASCHEMA_ID = ArtifactId(Kind("schema"), "schema")
 
 
+class Landing(NamedTuple):
+    """A change as it will be written: its canonical text, None for a removal, and the versions its entry records."""
+    change: Change
+    text: str | None
+    revision: int
+    schema_version: int
+
+
 def start(root: Path, actor: Actor) -> None:
     """A new store at root, holding the type of types, its start in the journal and in one commit."""
     store, signed = Store(root), Signed(actor, "initialise store")
     store.start()
     metaschema = {"id": str(METASCHEMA_ID), "type": "schema", "schema_version": 1, "revision": 1, **METASCHEMA}
-    path = store.save(METASCHEMA_ID, canonical.dump(canonical.order(metaschema, METASCHEMA["schema"])))
+    text = canonical.dump(canonical.order(metaschema, METASCHEMA["schema"]))
+    path = store.save(METASCHEMA_ID, text)
     entry = journal.write(
         store.dir, signed=signed, op="create", artifact=str(METASCHEMA_ID), path="",
-        revision=1, schema_version=1, written=path,
+        revision=1, schema_version=1, text=text,
     )
     store.commit([store.dir / "store.yaml", path, entry], signed)
 
@@ -31,10 +41,10 @@ def land(store: Store, operations: list, signed: Signed) -> kb_pb2.ApplyResponse
     """The set drafted, serialised, then written and committed; refused with every fault before anything is written."""
     try:
         draft, changes = _drafted(store, operations)
-        texts = _serialised(draft, changes)
+        landings = _serialised(draft, changes)
     except Refused as refused:
         return kb_pb2.ApplyResponse(faults=refused.faults)
-    return _written(store, draft, texts, signed)
+    return _written(store, landings, signed)
 
 
 def record(store: Store, read: list[dict], signed: Signed) -> str:
@@ -61,37 +71,35 @@ def _drafted(store: Store, operations: list) -> tuple[Draft, list[Change]]:
     return draft, changes
 
 
-def _serialised(draft: Draft, changes: list[Change]) -> list[tuple[Change, str | None]]:
-    """Each change with the canonical text of what it leaves, None for a removal; refused if any cannot be written."""
-    texts, faults = [], []
+def _serialised(draft: Draft, changes: list[Change]) -> list[Landing]:
+    """Each change as it will be written, settled from the draft; refused if any cannot be written."""
+    landings, faults = [], []
     for change in changes:
         if change.op == "delete":
-            texts.append((change, None))
+            landings.append(Landing(change, None, change.revision, change.schema_version))
             continue
+        artifact = draft.load(change.artifact_id)
         try:
-            texts.append((change, canonical.dump(draft.load(change.artifact_id))))
+            landings.append(Landing(change, canonical.dump(artifact), artifact["revision"], artifact["schema_version"]))
         except canonical.NotCanonical as fault:
             faults.append(kb_pb2.Fault(artifact=str(change.artifact_id), rule="content", message=str(fault)))
     if faults:
         raise Refused(faults)
-    return texts
+    return landings
 
 
-def _written(store: Store, draft: Draft, texts: list, signed: Signed) -> kb_pb2.ApplyResponse:
-    """Each file saved or removed, its journal entry written naming the set, and all of it in one commit."""
+def _written(store: Store, landings: list[Landing], signed: Signed) -> kb_pb2.ApplyResponse:
+    """Each file saved or removed, its journal entry written naming the set, and all of it in one commit. Reads
+    nothing: everything written was settled before."""
     written, results, batch = [], [], ""
-    for seq, (change, text) in enumerate(texts, start=1):
+    for seq, (change, text, revision, schema_version) in enumerate(landings, start=1):
         if text is None:
-            removed = store.load(change.artifact_id)
-            revision, schema_version = removed["revision"] + 1, removed["schema_version"]
-            path, saved = store.remove(change.artifact_id), None
+            path = store.remove(change.artifact_id)
         else:
-            artifact = draft.load(change.artifact_id)
-            revision, schema_version = artifact["revision"], artifact["schema_version"]
-            path = saved = store.save(change.artifact_id, text)
+            path = store.save(change.artifact_id, text)
         entry = journal.write(
             store.dir, signed=signed, op=change.op, artifact=str(change.artifact_id), path=change.path,
-            revision=revision, schema_version=schema_version, written=saved, seq=seq, batch=batch,
+            revision=revision, schema_version=schema_version, text=text, seq=seq, batch=batch,
         )
         batch = batch or entry.stem
         written += [path, entry]
```

- [ ] **Step 3: See the check pass**

Run: `make test`
Expected: `118 passed, 508 warnings in …`

Run: `.venv/bin/python /tmp/kb-phase-reads.py`
Expected: `no reads`

Run: `grep -n "read_bytes" src/kb/journal.py`
Expected: one line, inside `digest`, which only a snapshot uses

- [ ] **Step 4: Run the probe**

Run: `.venv/bin/python /tmp/kb-probe.py > /tmp/kb-probe-now.txt 2>&1; diff /tmp/kb-probe-baseline.txt /tmp/kb-probe-now.txt`
Expected: the diff below, and nothing else; then run `cp /tmp/kb-probe-now.txt /tmp/kb-probe-after-57.txt`

```
27,28c27,28
< tag/a unchanged on disk False
< files ['kb/decision/close-early.yaml', 'kb/schema/decision.yaml', 'kb/schema/schema.yaml', 'kb/schema/tag.yaml', 'kb/store.yaml', 'kb/tag/a.yaml', 'kb/tag/b.yaml'] 14
---
> tag/a unchanged on disk True
> files ['kb/decision/close-early.yaml', 'kb/schema/decision.yaml', 'kb/schema/schema.yaml', 'kb/schema/tag.yaml', 'kb/store.yaml', 'kb/tag/a.yaml', 'kb/tag/b.yaml'] 13
```

- [ ] **Step 5: Mark the slice green and commit**

In `docs/superpowers/plans/2026-09-24-kb-slices.md`, set slice 57's `Status:` to `green` and append a log line: `- <date> slice 57 green. <what its check showed>. Surprised by: <anything, or nothing>.`

```bash
git add -A src/kb docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 57: Nothing is read from disk once a set starts writing

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 6: Slice 58, The write pipeline holds no rpc types

**Files:**
- Create: `src/kb/refusals.py`: `not_found`, `no_type`, `no_collection`, `nothing_at`, `whole_only`, `still_linked`, `unwritable`
- Modify: `src/kb/edits.py`: refuses through `refusals`; its `not_found` goes
- Modify: `src/kb/write.py`: `land` returns `Landed(batch, results)` and raises `Refused`; `Result(artifact_id, revision, item)`
- Modify: `src/kb/servicer.py`: the five write rpcs catch `Refused` and build their responses from `Landed`

**Interfaces:**
- Consumes: `write.land`, `edits.*` (tasks 4 and 5)
- Produces:
- `refusals.not_found(artifact_id)`, `refusals.no_type(kind_name)`, `refusals.no_collection(artifact_id, collection)`, `refusals.nothing_at(locator)`, `refusals.whole_only(locator)`, `refusals.still_linked(removed, other, place)`, `refusals.unwritable(artifact_id, problem)`, each `-> kb_pb2.Fault`
- `write.Result(artifact_id, revision, item)`, `write.Landed(batch, results)`, `write.land(store, operations, signed) -> Landed` (raises `values.Refused`)

- [ ] **Step 1: See the check fail**

Run: `grep -c kb_pb2 src/kb/write.py src/kb/edits.py`
Expected: `src/kb/write.py:7` and `src/kb/edits.py:8`

- [ ] **Step 2: Apply the change**

Save the patch as `/tmp/kb-slice-58.patch`, then run: `git apply --check /tmp/kb-slice-58.patch && git apply /tmp/kb-slice-58.patch`
Expected: no output (task 6's patch also prints `warning: 1 line adds whitespace errors.`, for the blank line that ends `refusals.py`; harmless)

```diff
diff --git a/src/kb/edits.py b/src/kb/edits.py
index 40d2750..3cf003d 100644
--- a/src/kb/edits.py
+++ b/src/kb/edits.py
@@ -4,8 +4,7 @@ with every fault it finds."""
 import copy
 from typing import NamedTuple
 
-from kb import canonical, names, requests, validation, values
-from kb.contract import kb_pb2
+from kb import canonical, names, refusals, requests, validation, values
 from kb.store import Draft
 from kb.values import ArtifactId, Kind, Refused
 
@@ -35,9 +34,7 @@ def apply(draft: Draft, operation) -> Change:
 def _create(draft: Draft, creation: requests.Create) -> ArtifactId:
     kind = creation.kind
     if not draft.holds(ArtifactId(Kind("schema"), kind.name)):
-        raise Refused([kb_pb2.Fault(
-            rule="kind", message=f"a kind must name a type the store holds; the store holds no type called {kind.name!r}",
-        )])
+        raise Refused([refusals.no_type(kind.name)])
     at, faults = creation.at, list(creation.title_faults)
     if creation.name is not None:
         artifact_id = _unclaimed(draft, creation.name)
@@ -63,7 +60,7 @@ def _create(draft: Draft, creation: requests.Create) -> ArtifactId:
 def _replace(draft: Draft, replacement: requests.Replace) -> ArtifactId:
     locator = replacement.locator
     if not draft.holds(locator.id):
-        raise Refused([not_found(locator.id)])
+        raise Refused([refusals.not_found(locator.id)])
     if replacement.content.problems:
         raise Refused(replacement.content.refusal(str(locator.id)))
     content, current = replacement.content.tree, draft.load(locator.id)
@@ -77,15 +74,12 @@ def _append(draft: Draft, addition: requests.Add) -> Change:
     """One item put at the end of a collection the artifact's type declares, and named there."""
     locator = addition.locator
     if not draft.holds(locator.id):
-        raise Refused([not_found(locator.id)])
+        raise Refused([refusals.not_found(locator.id)])
     if addition.item.problems:
         raise Refused(addition.item.refusal(str(locator.id)))
     item, collection = addition.item.tree, "/".join(locator.place)
     if collection not in draft.schema(locator.id.kind)["schema"].get("parts", {}):
-        raise Refused([kb_pb2.Fault(
-            artifact=str(locator.id), path=collection, rule="not-found",
-            message=f"{str(locator.id)!r} holds no collection called {collection!r}",
-        )])
+        raise Refused([refusals.no_collection(locator.id, collection)])
     current = draft.load(locator.id)
     content = _content_of(current)
     content.setdefault(collection, []).append(item)
@@ -97,12 +91,9 @@ def _delete(draft: Draft, removal: requests.Remove) -> Change:
     """A whole artifact taken out of the draft, refused with one fault for each link that still points at it."""
     locator = removal.locator
     if not draft.holds(locator.id):
-        raise Refused([not_found(locator.id)])
+        raise Refused([refusals.not_found(locator.id)])
     if locator.place:
-        raise Refused([kb_pb2.Fault(
-            artifact=str(locator.id), path="/".join(locator.place), rule="locator",
-            message=f"a removal takes out a whole artifact; {'/'.join(locator.place)!r} is a place inside {str(locator.id)!r}",
-        )])
+        raise Refused([refusals.whole_only(locator)])
     blocking = []
     for other_id in draft.ids():
         if other_id == locator.id:
@@ -110,10 +101,7 @@ def _delete(draft: Draft, removal: requests.Remove) -> Change:
         schema = draft.schema(other_id.kind)["schema"]
         for field, place, target in validation.links(draft.load(other_id), schema, draft):
             if validation.points_at(target, locator.id):
-                blocking.append(kb_pb2.Fault(
-                    artifact=str(other_id), path=place, rule="on_delete",
-                    message=f"{str(locator.id)!r} cannot be removed while {str(other_id)!r} points at it at {place!r}",
-                ))
+                blocking.append(refusals.still_linked(locator.id, other_id, place))
     if blocking:
         raise Refused(blocking)
     removed = draft.load(locator.id)
@@ -152,10 +140,7 @@ def _placed(artifact: dict, locator: values.Locator, node: dict) -> dict:
         found = holder.get(collection, [])
         index = next((index for index, item in enumerate(found) if _node_name(collection, item) == name), None)
         if index is None:
-            raise Refused([kb_pb2.Fault(
-                artifact=str(locator.id), path="/".join(locator.place), rule="not-found",
-                message=f"{str(locator.id)!r} holds nothing at {'/'.join(locator.place)!r}",
-            )])
+            raise Refused([refusals.nothing_at(locator)])
         if not steps:
             found[index] = node if collection == "sections" else {"id": name, **node}
             return content
@@ -173,9 +158,3 @@ def _unclaimed(draft: Draft, named: ArtifactId) -> ArtifactId:
     """The name a title gives, or, when the store or an earlier change in the set already holds it, that name with
     -2, -3 and so on added: the first that nothing holds. What already holds a name keeps it."""
     return ArtifactId(named.kind, names.numbered(named.slug, lambda slug: draft.holds(ArtifactId(named.kind, slug))))
-
-
-def not_found(artifact_id: ArtifactId) -> kb_pb2.Fault:
-    return kb_pb2.Fault(
-        artifact=str(artifact_id), rule="not-found", message=f"the store holds nothing by the name {str(artifact_id)!r}",
-    )
diff --git a/src/kb/refusals.py b/src/kb/refusals.py
new file mode 100644
index 0000000..8698caf
--- /dev/null
+++ b/src/kb/refusals.py
@@ -0,0 +1,51 @@
+"""The refusals the domain makes of what a store holds, each with its rule and its message. Conversions refuse in
+kb.values and type checks in kb.validation; what neither owns is made here, so no domain module names a contract type."""
+from kb.contract import kb_pb2
+from kb.values import ArtifactId, Locator
+
+
+def not_found(artifact_id: ArtifactId) -> kb_pb2.Fault:
+    return kb_pb2.Fault(
+        artifact=str(artifact_id), rule="not-found", message=f"the store holds nothing by the name {str(artifact_id)!r}",
+    )
+
+
+def no_type(kind_name: str) -> kb_pb2.Fault:
+    return kb_pb2.Fault(
+        rule="kind", message=f"a kind must name a type the store holds; the store holds no type called {kind_name!r}",
+    )
+
+
+def no_collection(artifact_id: ArtifactId, collection: str) -> kb_pb2.Fault:
+    return kb_pb2.Fault(
+        artifact=str(artifact_id), path=collection, rule="not-found",
+        message=f"{str(artifact_id)!r} holds no collection called {collection!r}",
+    )
+
+
+def nothing_at(locator: Locator) -> kb_pb2.Fault:
+    place = "/".join(locator.place)
+    return kb_pb2.Fault(
+        artifact=str(locator.id), path=place, rule="not-found",
+        message=f"{str(locator.id)!r} holds nothing at {place!r}",
+    )
+
+
+def whole_only(locator: Locator) -> kb_pb2.Fault:
+    place = "/".join(locator.place)
+    return kb_pb2.Fault(
+        artifact=str(locator.id), path=place, rule="locator",
+        message=f"a removal takes out a whole artifact; {place!r} is a place inside {str(locator.id)!r}",
+    )
+
+
+def still_linked(removed: ArtifactId, other: ArtifactId, place: str) -> kb_pb2.Fault:
+    return kb_pb2.Fault(
+        artifact=str(other), path=place, rule="on_delete",
+        message=f"{str(removed)!r} cannot be removed while {str(other)!r} points at it at {place!r}",
+    )
+
+
+def unwritable(artifact_id: ArtifactId, problem: str) -> kb_pb2.Fault:
+    return kb_pb2.Fault(artifact=str(artifact_id), rule="content", message=problem)
+
diff --git a/src/kb/servicer.py b/src/kb/servicer.py
index 7a1d257..f7aaea8 100644
--- a/src/kb/servicer.py
+++ b/src/kb/servicer.py
@@ -10,7 +10,7 @@ from kb.content import dumps, text
 from kb.contract import kb_pb2, kb_pb2_grpc
 from kb.store import Store, Unreadable
 from kb.values import ArtifactId
-from kb.edits import not_found as _not_found
+from kb.refusals import not_found as _not_found
 
 
 class KbServicer(kb_pb2_grpc.KbServicer):
@@ -28,34 +28,49 @@ class KbServicer(kb_pb2_grpc.KbServicer):
 
     def Create(self, request, context):
         creation = kb_pb2.Creation(type=request.type, title=request.title, content=request.content)
-        landed = write.land(self._store, requests.operations([kb_pb2.Operation(create=creation)]), values.signed(request.actor, request.message))
-        if landed.faults:
-            return kb_pb2.CreateResponse(faults=landed.faults)
-        return kb_pb2.CreateResponse(id=landed.results[0].id, revision=landed.results[0].revision)
+        try:
+            landed = self._land([kb_pb2.Operation(create=creation)], request)
+        except values.Refused as refused:
+            return kb_pb2.CreateResponse(faults=refused.faults)
+        return kb_pb2.CreateResponse(id=str(landed.results[0].artifact_id), revision=landed.results[0].revision)
 
     def Write(self, request, context):
         replacement = kb_pb2.Replacement(locator=request.locator, content=request.content)
-        landed = write.land(self._store, requests.operations([kb_pb2.Operation(write=replacement)]), values.signed(request.actor, request.message))
-        if landed.faults:
-            return kb_pb2.WriteResponse(faults=landed.faults)
+        try:
+            landed = self._land([kb_pb2.Operation(write=replacement)], request)
+        except values.Refused as refused:
+            return kb_pb2.WriteResponse(faults=refused.faults)
         return kb_pb2.WriteResponse(revision=landed.results[0].revision)
 
     def Append(self, request, context):
         addition = kb_pb2.Addition(locator=request.locator, content=request.content)
-        landed = write.land(self._store, requests.operations([kb_pb2.Operation(append=addition)]), values.signed(request.actor, request.message))
-        if landed.faults:
-            return kb_pb2.AppendResponse(faults=landed.faults)
+        try:
+            landed = self._land([kb_pb2.Operation(append=addition)], request)
+        except values.Refused as refused:
+            return kb_pb2.AppendResponse(faults=refused.faults)
         return kb_pb2.AppendResponse(id=landed.results[0].item, revision=landed.results[0].revision)
 
     def Delete(self, request, context):
         removal = kb_pb2.Removal(locator=request.locator)
-        landed = write.land(self._store, requests.operations([kb_pb2.Operation(delete=removal)]), values.signed(request.actor, request.message))
-        if landed.faults:
-            return kb_pb2.DeleteResponse(faults=landed.faults)
+        try:
+            landed = self._land([kb_pb2.Operation(delete=removal)], request)
+        except values.Refused as refused:
+            return kb_pb2.DeleteResponse(faults=refused.faults)
         return kb_pb2.DeleteResponse(revision=landed.results[0].revision)
 
     def Apply(self, request, context):
-        return write.land(self._store, requests.operations(request.operations), values.signed(request.actor, request.message))
+        try:
+            landed = self._land(request.operations, request)
+        except values.Refused as refused:
+            return kb_pb2.ApplyResponse(faults=refused.faults)
+        return kb_pb2.ApplyResponse(batch=landed.batch, results=[
+            kb_pb2.Result(id=str(result.artifact_id), revision=result.revision, item=result.item)
+            for result in landed.results
+        ])
+
+    def _land(self, operations, request) -> write.Landed:
+        """A set of operations landed under the request's actor and message."""
+        return write.land(self._store, requests.operations(operations), values.signed(request.actor, request.message))
 
     def Read(self, request, context):
         try:
diff --git a/src/kb/write.py b/src/kb/write.py
index f0b0312..7f8cd0b 100644
--- a/src/kb/write.py
+++ b/src/kb/write.py
@@ -5,8 +5,7 @@ and nothing is written. Starting a store and recording a snapshot write and comm
 from pathlib import Path
 from typing import NamedTuple
 
-from kb import canonical, edits, journal, requests
-from kb.contract import kb_pb2
+from kb import canonical, edits, journal, refusals, requests
 from kb.metaschema import METASCHEMA
 from kb.edits import Change
 from kb.store import Draft, Store
@@ -15,6 +14,19 @@ from kb.values import Actor, ArtifactId, Kind, Refused, Signed
 METASCHEMA_ID = ArtifactId(Kind("schema"), "schema")
 
 
+class Result(NamedTuple):
+    """What a set did to one artifact: its version now, and, for an item added, the item's name."""
+    artifact_id: ArtifactId
+    revision: int
+    item: str
+
+
+class Landed(NamedTuple):
+    """A set written: the name of the set, and what it did to each artifact, in the order of its operations."""
+    batch: str
+    results: list[Result]
+
+
 class Landing(NamedTuple):
     """A change as it will be written: its canonical text, None for a removal, and the versions its entry records."""
     change: Change
@@ -37,14 +49,11 @@ def start(root: Path, actor: Actor) -> None:
     store.commit([store.dir / "store.yaml", path, entry], signed)
 
 
-def land(store: Store, operations: list, signed: Signed) -> kb_pb2.ApplyResponse:
-    """The set drafted, serialised, then written and committed; refused with every fault before anything is written."""
-    try:
-        draft, changes = _drafted(store, operations)
-        landings = _serialised(draft, changes)
-    except Refused as refused:
-        return kb_pb2.ApplyResponse(faults=refused.faults)
-    return _written(store, landings, signed)
+def land(store: Store, operations: list, signed: Signed) -> Landed:
+    """The set drafted, serialised, then written and committed. Raises Refused with every fault, having written
+    nothing."""
+    draft, changes = _drafted(store, operations)
+    return _written(store, _serialised(draft, changes), signed)
 
 
 def record(store: Store, read: list[dict], signed: Signed) -> str:
@@ -73,7 +82,7 @@ def _drafted(store: Store, operations: list) -> tuple[Draft, list[Change]]:
 
 def _serialised(draft: Draft, changes: list[Change]) -> list[Landing]:
     """Each change as it will be written, settled from the draft; refused if any cannot be written."""
-    landings, faults = [], []
+    landings, found = [], []
     for change in changes:
         if change.op == "delete":
             landings.append(Landing(change, None, change.revision, change.schema_version))
@@ -82,13 +91,13 @@ def _serialised(draft: Draft, changes: list[Change]) -> list[Landing]:
         try:
             landings.append(Landing(change, canonical.dump(artifact), artifact["revision"], artifact["schema_version"]))
         except canonical.NotCanonical as fault:
-            faults.append(kb_pb2.Fault(artifact=str(change.artifact_id), rule="content", message=str(fault)))
-    if faults:
-        raise Refused(faults)
+            found.append(refusals.unwritable(change.artifact_id, str(fault)))
+    if found:
+        raise Refused(found)
     return landings
 
 
-def _written(store: Store, landings: list[Landing], signed: Signed) -> kb_pb2.ApplyResponse:
+def _written(store: Store, landings: list[Landing], signed: Signed) -> Landed:
     """Each file saved or removed, its journal entry written naming the set, and all of it in one commit. Reads
     nothing: everything written was settled before."""
     written, results, batch = [], [], ""
@@ -103,6 +112,6 @@ def _written(store: Store, landings: list[Landing], signed: Signed) -> kb_pb2.Ap
         )
         batch = batch or entry.stem
         written += [path, entry]
-        results.append(kb_pb2.Result(id=str(change.artifact_id), revision=revision, item=change.item))
+        results.append(Result(change.artifact_id, revision, change.item))
     store.commit(written, signed)
-    return kb_pb2.ApplyResponse(batch=batch, results=results)
+    return Landed(batch, results)
```

- [ ] **Step 3: See the check pass**

Run: `make test`
Expected: `118 passed, 508 warnings in …`

Run: `grep -c kb_pb2 src/kb/write.py src/kb/edits.py`
Expected: `src/kb/write.py:0` and `src/kb/edits.py:0`

- [ ] **Step 4: Run the probe**

Run: `.venv/bin/python /tmp/kb-probe.py > /tmp/kb-probe-now.txt 2>&1; diff /tmp/kb-probe-after-57.txt /tmp/kb-probe-now.txt`
Expected: no output (the probe's output is identical to `/tmp/kb-probe-after-57.txt`)

- [ ] **Step 5: Mark the slice green and commit**

In `docs/superpowers/plans/2026-09-24-kb-slices.md`, set slice 58's `Status:` to `green` and append a log line: `- <date> slice 58 green. <what its check showed>. Surprised by: <anything, or nothing>.`

```bash
git add -A src/kb docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 58: The write pipeline holds no rpc types

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 7: Slice 59, Converting a request touches no file

**Files:**
- Modify: `src/kb/values.py`: `root(text) -> Root(path, named)` checks only that a directory was named; the `discovery` import goes
- Modify: `src/kb/store.py`: gains `MARKER`, `vacant(root)` (the four refusals of what stands at a root), `find_above` and `locate` (from `discovery.py`)
- Delete: `src/kb/discovery.py`
- Modify: `src/kb/write.py`: `start(root: Root, actor)` calls `vacant(root)` first
- Modify: `src/kb/requests.py`, `src/kb/servicer.py`, `src/kb/client.py`: follow the moves

**Interfaces:**
- Consumes: `write.start`, `requests.starting` (tasks 2 and 4)
- Produces:
- `values.Root(path: Path, named: str)`, `values.root(text) -> Root`
- `store.MARKER`, `store.vacant(root: Root) -> None` (raises `Refused`), `store.find_above(start) -> Path | None`, `store.locate(cwd, env) -> (Path | None, Fault | None)`
- `write.start(root: Root, actor: Actor)`; `requests.starting(request) -> (Actor, Root)`

A refusal quotes the root as the request named it (`'./nope'`), which a `Path` would normalise away. That is why the value carries the name.

- [ ] **Step 1: See the check fail**

Run: `grep -nE "exists\(|is_dir\(|is_file\(|glob\(|read_text\(|discovery" src/kb/values.py`
Expected: five lines (the `discovery` import, `exists` twice, `is_dir`, and `discovery.find_above`)

- [ ] **Step 2: Apply the change**

Save the patch as `/tmp/kb-slice-59.patch`, then run: `git apply --check /tmp/kb-slice-59.patch && git apply /tmp/kb-slice-59.patch`
Expected: no output

```diff
diff --git a/src/kb/client.py b/src/kb/client.py
index f95c2ea..a5bcef3 100644
--- a/src/kb/client.py
+++ b/src/kb/client.py
@@ -2,7 +2,7 @@
 import os
 from pathlib import Path
 
-from kb import discovery
+from kb import store
 from kb.contract import kb_pb2
 from kb.servicer import KbServicer
 
@@ -21,7 +21,7 @@ class InProcessClient:
     def _servicer(self) -> tuple[KbServicer | None, kb_pb2.Fault | None]:
         if self._root is not None:
             return KbServicer(self._root), None
-        root, refusal = discovery.locate(Path.cwd(), os.environ)
+        root, refusal = store.locate(Path.cwd(), os.environ)
         if refusal is not None:
             return None, refusal
         return KbServicer(root), None
diff --git a/src/kb/discovery.py b/src/kb/discovery.py
deleted file mode 100644
index 8b6989c..0000000
--- a/src/kb/discovery.py
+++ /dev/null
@@ -1,38 +0,0 @@
-"""Finding the store the way git finds a repository: upward from the working directory, or named by KB_ROOT."""
-from pathlib import Path
-from typing import Mapping
-
-from kb.contract import kb_pb2
-
-MARKER = Path("kb") / "store.yaml"
-
-
-def find_above(start: Path) -> Path | None:
-    """The nearest directory at or above `start` with a store inside it, or None."""
-    for directory in (start, *start.parents):
-        if (directory / MARKER).is_file():
-            return directory
-    return None
-
-
-def locate(cwd: Path, env: Mapping[str, str]) -> tuple[Path | None, kb_pb2.Fault | None]:
-    """The store a call goes to, or the fault that refuses it. Nothing is guessed at."""
-    above = find_above(cwd)
-    if "KB_ROOT" not in env:
-        if above is None:
-            return None, kb_pb2.Fault(
-                rule="store", message=f"no store was found, neither above {cwd} nor named outright",
-            )
-        return above, None
-    named = Path(env["KB_ROOT"])
-    if not (named / MARKER).is_file():
-        return None, kb_pb2.Fault(
-            rule="store", message=f"KB_ROOT names a directory that holds no store: {named}",
-        )
-    if above is not None and above.resolve() != named.resolve():
-        return None, kb_pb2.Fault(
-            rule="store",
-            message=f"KB_ROOT names a store other than the one {cwd} is working in: KB_ROOT is {named}, "
-                    f"the working directory is inside {above}; neither is guessed at",
-        )
-    return named, None
diff --git a/src/kb/requests.py b/src/kb/requests.py
index 1dfc65d..eb6d51b 100644
--- a/src/kb/requests.py
+++ b/src/kb/requests.py
@@ -3,11 +3,10 @@ does not convert is refused here, before anything else sees it. In a set, or amo
 entry that does not convert stands in its place as a Refusal, so the faults come back in the order of the entries."""
 from dataclasses import dataclass
 from datetime import datetime
-from pathlib import Path
 
 from kb import names, values
 from kb.contract import kb_pb2
-from kb.values import Actor, ArtifactId, Content, Kind, Locator, Refused
+from kb.values import Actor, ArtifactId, Content, Kind, Locator, Refused, Root
 
 
 @dataclass(frozen=True)
@@ -86,7 +85,7 @@ class Listing:
     ids: bool
 
 
-def starting(request: kb_pb2.InitRequest) -> tuple[Actor, Path]:
+def starting(request: kb_pb2.InitRequest) -> tuple[Actor, Root]:
     """Who starts a store, then where; the first refusal only."""
     return values.starter(request.actor), values.root(request.root)
 
diff --git a/src/kb/servicer.py b/src/kb/servicer.py
index f7aaea8..a58be15 100644
--- a/src/kb/servicer.py
+++ b/src/kb/servicer.py
@@ -21,9 +21,9 @@ class KbServicer(kb_pb2_grpc.KbServicer):
     def Init(self, request, context):
         try:
             actor, root = requests.starting(request)
+            write.start(root, actor)
         except values.Refused as refused:
             return kb_pb2.InitResponse(faults=refused.faults)
-        write.start(root, actor)
         return kb_pb2.InitResponse()
 
     def Create(self, request, context):
diff --git a/src/kb/store.py b/src/kb/store.py
index 05767a9..ec54fc2 100644
--- a/src/kb/store.py
+++ b/src/kb/store.py
@@ -1,11 +1,15 @@
-"""The store on disk: <root>/kb/, one canonical YAML file per artifact, itself a git repository."""
+"""The store on disk: <root>/kb/, one canonical YAML file per artifact, itself a git repository; and finding it, the
+way git finds a repository: upward from the working directory, or named by KB_ROOT."""
 import os
 import subprocess
 from pathlib import Path
+from typing import Mapping
 
 from kb import canonical, values
 from kb.contract import CONTRACT_VERSION, kb_pb2
-from kb.values import ArtifactId, Kind, Signed
+from kb.values import ArtifactId, Kind, Refused, Root, Signed
+
+MARKER = Path("kb") / "store.yaml"
 
 
 class Unreadable(Exception):
@@ -120,6 +124,59 @@ class Draft:
         return self.load(ArtifactId(Kind("schema"), kind.name))
 
 
+def vacant(root: Root) -> None:
+    """Refuse a root a store cannot be started in: one that is not there, is not a directory, has anything called kb
+    inside it, or is inside a store."""
+    if not root.path.exists():
+        raise Refused([kb_pb2.Fault(
+            rule="root", message=f"a store is started in a directory that exists; {root.named!r} does not",
+        )])
+    if not root.path.is_dir():
+        raise Refused([kb_pb2.Fault(
+            rule="root", message=f"a store is started in a directory, and {root.named!r} is not one",
+        )])
+    if (root.path / "kb").exists():
+        raise Refused([kb_pb2.Fault(
+            rule="root", message=f"a store is never started over another; {root.named!r} already has a store inside it",
+        )])
+    above = find_above(root.path.resolve().parent)
+    if above is not None:
+        raise Refused([kb_pb2.Fault(
+            rule="root", message=f"stores do not nest; {root.named!r} is inside the store at {str(above)!r}",
+        )])
+
+
+def find_above(start: Path) -> Path | None:
+    """The nearest directory at or above `start` with a store inside it, or None."""
+    for directory in (start, *start.parents):
+        if (directory / MARKER).is_file():
+            return directory
+    return None
+
+
+def locate(cwd: Path, env: Mapping[str, str]) -> tuple[Path | None, kb_pb2.Fault | None]:
+    """The store a call goes to, or the fault that refuses it. Nothing is guessed at."""
+    above = find_above(cwd)
+    if "KB_ROOT" not in env:
+        if above is None:
+            return None, kb_pb2.Fault(
+                rule="store", message=f"no store was found, neither above {cwd} nor named outright",
+            )
+        return above, None
+    named = Path(env["KB_ROOT"])
+    if not (named / MARKER).is_file():
+        return None, kb_pb2.Fault(
+            rule="store", message=f"KB_ROOT names a directory that holds no store: {named}",
+        )
+    if above is not None and above.resolve() != named.resolve():
+        return None, kb_pb2.Fault(
+            rule="store",
+            message=f"KB_ROOT names a store other than the one {cwd} is working in: KB_ROOT is {named}, "
+                    f"the working directory is inside {above}; neither is guessed at",
+        )
+    return named, None
+
+
 QUIET = ("-c", "maintenance.auto=false", "-c", "gc.auto=0")
 
 
diff --git a/src/kb/values.py b/src/kb/values.py
index 1b405d2..757690e 100644
--- a/src/kb/values.py
+++ b/src/kb/values.py
@@ -7,7 +7,7 @@ from dataclasses import dataclass
 from datetime import datetime, timezone
 from pathlib import Path
 
-from kb import canonical, discovery, names
+from kb import canonical, names
 from kb.content import loads
 from kb.contract import kb_pb2
 
@@ -173,33 +173,22 @@ def starter(request: kb_pb2.Actor) -> Actor:
     return actor(request)
 
 
-def root(text: str) -> Path:
-    """The directory a store is started in, as the request names it; relative names stay relative. It must be a
-    directory that is there, with nothing called kb/ inside it, and inside no store."""
+@dataclass(frozen=True)
+class Root:
+    """The directory a store is started in, and the name the request gave it, which a refusal quotes."""
+    path: Path
+    named: str
+
+
+def root(text: str) -> Root:
+    """The directory a store is started in, as the request names it; relative names stay relative. What stands
+    there is the store's to check."""
     if not text:
         raise Refused([kb_pb2.Fault(
             rule="root",
             message="a store is started in a directory that was named and that exists; no directory was named",
         )])
-    named = Path(text)
-    if not named.exists():
-        raise Refused([kb_pb2.Fault(
-            rule="root", message=f"a store is started in a directory that exists; {text!r} does not",
-        )])
-    if not named.is_dir():
-        raise Refused([kb_pb2.Fault(
-            rule="root", message=f"a store is started in a directory, and {text!r} is not one",
-        )])
-    if (named / "kb").exists():
-        raise Refused([kb_pb2.Fault(
-            rule="root", message=f"a store is never started over another; {text!r} already has a store inside it",
-        )])
-    above = discovery.find_above(named.resolve().parent)
-    if above is not None:
-        raise Refused([kb_pb2.Fault(
-            rule="root", message=f"stores do not nest; {text!r} is inside the store at {str(above)!r}",
-        )])
-    return named
+    return Root(Path(text), text)
 
 
 def path(store_dir: Path, artifact_id: ArtifactId) -> Path:
diff --git a/src/kb/write.py b/src/kb/write.py
index 7f8cd0b..1ca25fa 100644
--- a/src/kb/write.py
+++ b/src/kb/write.py
@@ -2,14 +2,13 @@
 as the operations before it left it; only when every one passes is anything written, each artifact saved, one journal
 entry per operation naming the set, and one commit. A fault anywhere refuses the whole set with every fault found,
 and nothing is written. Starting a store and recording a snapshot write and commit here too."""
-from pathlib import Path
 from typing import NamedTuple
 
 from kb import canonical, edits, journal, refusals, requests
 from kb.metaschema import METASCHEMA
 from kb.edits import Change
-from kb.store import Draft, Store
-from kb.values import Actor, ArtifactId, Kind, Refused, Signed
+from kb.store import Draft, Store, vacant
+from kb.values import Actor, ArtifactId, Kind, Refused, Root, Signed
 
 METASCHEMA_ID = ArtifactId(Kind("schema"), "schema")
 
@@ -35,9 +34,11 @@ class Landing(NamedTuple):
     schema_version: int
 
 
-def start(root: Path, actor: Actor) -> None:
-    """A new store at root, holding the type of types, its start in the journal and in one commit."""
-    store, signed = Store(root), Signed(actor, "initialise store")
+def start(root: Root, actor: Actor) -> None:
+    """A new store at root, holding the type of types, its start in the journal and in one commit. Raises Refused
+    where no store can be started."""
+    vacant(root)
+    store, signed = Store(root.path), Signed(actor, "initialise store")
     store.start()
     metaschema = {"id": str(METASCHEMA_ID), "type": "schema", "schema_version": 1, "revision": 1, **METASCHEMA}
     text = canonical.dump(canonical.order(metaschema, METASCHEMA["schema"]))
```

- [ ] **Step 3: See the check pass**

Run: `make test`
Expected: `118 passed, 508 warnings in …`

Run: `grep -nE "exists\(|is_dir\(|is_file\(|glob\(|read_text\(|discovery" src/kb/values.py`
Expected: no output

Run: `ls src/kb/discovery.py; wc -l src/kb/store.py`
Expected: `No such file or directory`; 185 lines

Run: `.venv/bin/kb --help | head -1`
Expected: `usage: kb [-h] {init,validate} ...`

- [ ] **Step 4: Run the probe**

Run: `.venv/bin/python /tmp/kb-probe.py > /tmp/kb-probe-now.txt 2>&1; diff /tmp/kb-probe-after-57.txt /tmp/kb-probe-now.txt`
Expected: no output (the probe's output is identical to `/tmp/kb-probe-after-57.txt` (its `init` lines pin the root refusals, relative names quoted as given))

- [ ] **Step 5: Mark the slice green and commit**

In `docs/superpowers/plans/2026-09-24-kb-slices.md`, set slice 59's `Status:` to `green` and append a log line: `- <date> slice 59 green. <what its check showed>. Surprised by: <anything, or nothing>.`

```bash
git add -A src/kb docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 59: Converting a request touches no file

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 8: Slice 60, Reads are their own module

**Files:**
- Create: `src/kb/read.py`: `artifact(store, reading)`, `stub(store, field, target_id)`, and the whole, section, summary, resolution and inbound helpers
- Modify: `src/kb/refusals.py`: gains `no_section(artifact_id, title)`
- Modify: `src/kb/servicer.py`: Read is one call; Search, Refs and List use `read.stub`

**Interfaces:**
- Consumes: `requests.Reading` (task 2), `refusals` (task 6)
- Produces:
- `read.artifact(store, reading: Reading) -> kb_pb2.ReadResponse` (raises `Refused` for a missing name, a missing section, or an unreadable file, carrying the same faults as before)
- `read.stub(store, field: str, target_id: ArtifactId) -> kb_pb2.Stub`
- `refusals.no_section(artifact_id, title)`

- [ ] **Step 1: See the check fail**

Run: `ls src/kb/read.py; grep -c "def _whole\|def _section\|def _summary\|def _resolved\|def _stub\|def _inbound" src/kb/servicer.py`
Expected: `No such file or directory`; `7` (`def _summary` also matches `_summary_fields`)

- [ ] **Step 2: Apply the change**

Save the patch as `/tmp/kb-slice-60.patch`, then run: `git apply --check /tmp/kb-slice-60.patch && git apply /tmp/kb-slice-60.patch`
Expected: no output

```diff
diff --git a/src/kb/read.py b/src/kb/read.py
new file mode 100644
index 0000000..f9a5d37
--- /dev/null
+++ b/src/kb/read.py
@@ -0,0 +1,116 @@
+"""Reads: an artifact whole, with its links followed as far as asked; one of its sections; or its summary, with a stub
+of each artifact it links to, each part it holds, and how many artifacts point at it. The stub is every query's too."""
+from kb import canonical, refusals, validation, values
+from kb.content import dumps
+from kb.contract import kb_pb2
+from kb.requests import Reading
+from kb.store import Store, Unreadable
+from kb.values import ArtifactId, Locator, Refused
+
+
+def artifact(store: Store, reading: Reading) -> kb_pb2.ReadResponse:
+    """The artifact at the level asked. Raises Refused for a name the store lacks, a section it lacks, or a stored
+    file that cannot be read."""
+    locator = reading.locator
+    if not store.holds(locator.id):
+        raise Refused([refusals.not_found(locator.id)])
+    try:
+        if reading.level == "whole":
+            return _whole(store, locator, reading.depth)
+        if reading.level == "section":
+            return _section(store, locator, reading.section)
+        return _summary(store, locator)
+    except Unreadable as unreadable:
+        raise Refused([unreadable.fault]) from None
+
+
+def stub(store: Store, field: str, target_id: ArtifactId) -> kb_pb2.Stub:
+    """An artifact in brief, under the field that reached it: its identity and the fields its type shows at a glance."""
+    target = store.load(target_id)
+    schema = store.schema(target_id.kind)["schema"]
+    return kb_pb2.Stub(
+        field=field, id=target["id"], type=target["type"], title=target["title"],
+        fields=dumps(_summary_fields(target, schema)),
+    )
+
+
+def _whole(store: Store, locator: Locator, depth: int) -> kb_pb2.ReadResponse:
+    found = _resolved(store, locator.id, depth, {str(locator.id)})
+    content = {key: value for key, value in found.items() if key not in canonical.IDENTITY}
+    return _response(found, dumps(content))
+
+
+def _section(store: Store, locator: Locator, title: str) -> kb_pb2.ReadResponse:
+    """The first section with that title, at any depth, in the order the artifact holds them, and nothing else."""
+    found = store.load(locator.id)
+    section = _find_section(found.get("sections", []), title)
+    if section is None:
+        raise Refused([refusals.no_section(locator.id, title)])
+    return _response(found, dumps(section))
+
+
+def _summary(store: Store, locator: Locator) -> kb_pb2.ReadResponse:
+    found = store.load(locator.id)
+    schema = store.schema(locator.id.kind)["schema"]
+    response = _response(found, dumps(_summary_fields(found, schema)))
+    for field, _, target in validation.links(found, schema, store):
+        response.references.append(stub(store, field, values.artifact_id(target)))
+    for collection in schema.get("parts", {}):
+        for item in found.get(collection, []):
+            response.parts.append(kb_pb2.PartStub(collection=collection, id=item["id"], title=item["title"]))
+    for (type_name, field), count in _inbound(store, str(locator.id)).items():
+        response.inbound.append(kb_pb2.InboundCount(type=type_name, field=field, count=count))
+    return response
+
+
+def _response(found: dict, content: str) -> kb_pb2.ReadResponse:
+    return kb_pb2.ReadResponse(
+        id=found["id"], type=found["type"], schema_version=found["schema_version"], revision=found["revision"],
+        title=found["title"], content=content,
+    )
+
+
+def _resolved(store: Store, artifact_id: ArtifactId, depth: int, on_path: set) -> dict:
+    """The artifact as stored, each link followed depth steps with the target, itself resolved, in place of its
+    name. A target on the path already being filled in stays a name, so a loop ends."""
+    found = store.load(artifact_id)
+    if depth < 1:
+        return found
+    def fill(target):
+        if target in on_path:
+            return target
+        return _resolved(store, values.artifact_id(target), depth - 1, on_path | {target})
+    resolved = dict(found)
+    for field in validation.references(store.schema(artifact_id.kind)["schema"], store):
+        value = found.get(field)
+        if isinstance(value, list):
+            resolved[field] = [fill(target) for target in value]
+        elif value is not None:
+            resolved[field] = fill(value)
+    return resolved
+
+
+def _inbound(store: Store, artifact_id: str) -> dict:
+    """How many artifacts point at this one, by their type and the field they use."""
+    counts = {}
+    for other in store.artifacts():
+        schema = store.schema(values.kind(other["type"]))["schema"]
+        pointing = {field for field, _, target in validation.links(other, schema, store) if target == artifact_id}
+        for field in pointing:
+            counts[(other["type"], field)] = counts.get((other["type"], field), 0) + 1
+    return counts
+
+
+def _find_section(sections: list, title: str) -> dict | None:
+    """The first section titled so, looking at each section before the sections inside it."""
+    for section in sections:
+        if section["title"] == title:
+            return section
+        found = _find_section(section.get("sections", []), title)
+        if found is not None:
+            return found
+    return None
+
+
+def _summary_fields(found: dict, schema: dict) -> dict:
+    return {name: found[name] for name in schema.get("summary", []) if name in found}
diff --git a/src/kb/refusals.py b/src/kb/refusals.py
index 8698caf..ede4724 100644
--- a/src/kb/refusals.py
+++ b/src/kb/refusals.py
@@ -49,3 +49,10 @@ def still_linked(removed: ArtifactId, other: ArtifactId, place: str) -> kb_pb2.F
 def unwritable(artifact_id: ArtifactId, problem: str) -> kb_pb2.Fault:
     return kb_pb2.Fault(artifact=str(artifact_id), rule="content", message=problem)
 
+
+
+def no_section(artifact_id: ArtifactId, title: str) -> kb_pb2.Fault:
+    return kb_pb2.Fault(
+        artifact=str(artifact_id), path="sections", rule="not-found",
+        message=f"{str(artifact_id)!r} holds no section titled {title!r}",
+    )
diff --git a/src/kb/servicer.py b/src/kb/servicer.py
index a58be15..2f6ab9b 100644
--- a/src/kb/servicer.py
+++ b/src/kb/servicer.py
@@ -5,8 +5,8 @@ string that came from the request.
 """
 from datetime import datetime
 
-from kb import canonical, journal, requests, search, validation, values, write
-from kb.content import dumps, text
+from kb import canonical, journal, read, requests, search, validation, values, write
+from kb.content import text
 from kb.contract import kb_pb2, kb_pb2_grpc
 from kb.store import Store, Unreadable
 from kb.values import ArtifactId
@@ -74,81 +74,9 @@ class KbServicer(kb_pb2_grpc.KbServicer):
 
     def Read(self, request, context):
         try:
-            reading = requests.reading(request)
+            return read.artifact(self._store, requests.reading(request))
         except values.Refused as refused:
             return kb_pb2.ReadResponse(faults=refused.faults)
-        locator = reading.locator
-        if not self._store.holds(locator.id):
-            return kb_pb2.ReadResponse(faults=[_not_found(locator.id)])
-        try:
-            if reading.level == "whole":
-                return self._whole(locator, reading.depth)
-            if reading.level == "section":
-                return self._section(locator, reading.section)
-            return self._summary(locator)
-        except Unreadable as unreadable:
-            return kb_pb2.ReadResponse(faults=[unreadable.fault])
-
-    def _whole(self, locator, depth: int):
-        artifact = self._resolved(locator.id, depth, {str(locator.id)})
-        return kb_pb2.ReadResponse(
-            id=artifact["id"], type=artifact["type"],
-            schema_version=artifact["schema_version"], revision=artifact["revision"],
-            title=artifact["title"],
-            content=dumps({key: value for key, value in artifact.items() if key not in canonical.IDENTITY}),
-        )
-
-    def _section(self, locator, title: str):
-        """The first section with that title, at any depth, in the order the artifact holds them, and nothing else."""
-        artifact = self._store.load(locator.id)
-        found = _find_section(artifact.get("sections", []), title)
-        if found is None:
-            return kb_pb2.ReadResponse(faults=[kb_pb2.Fault(
-                artifact=str(locator.id), path="sections", rule="not-found",
-                message=f"{str(locator.id)!r} holds no section titled {title!r}",
-            )])
-        return kb_pb2.ReadResponse(
-            id=artifact["id"], type=artifact["type"],
-            schema_version=artifact["schema_version"], revision=artifact["revision"],
-            title=artifact["title"], content=dumps(found),
-        )
-
-    def _resolved(self, artifact_id: ArtifactId, depth: int, on_path: set) -> dict:
-        """The artifact as stored, each link followed depth steps with the target, itself resolved, in place of its
-        name. A target on the path already being filled in stays a name, so a loop ends."""
-        artifact = self._store.load(artifact_id)
-        if depth < 1:
-            return artifact
-        def fill(target):
-            if target in on_path:
-                return target
-            return self._resolved(values.artifact_id(target), depth - 1, on_path | {target})
-        resolved = dict(artifact)
-        for field in validation.references(self._store.schema(artifact_id.kind)["schema"], self._store):
-            value = artifact.get(field)
-            if isinstance(value, list):
-                resolved[field] = [fill(target) for target in value]
-            elif value is not None:
-                resolved[field] = fill(value)
-        return resolved
-
-    def _summary(self, locator):
-        artifact = self._store.load(locator.id)
-        schema = self._store.schema(locator.id.kind)["schema"]
-        response = kb_pb2.ReadResponse(
-            id=artifact["id"], type=artifact["type"],
-            schema_version=artifact["schema_version"], revision=artifact["revision"],
-            title=artifact["title"],
-            content=dumps(_summary_fields(artifact, schema)),
-        )
-        for field, _, target in validation.links(artifact, schema, self._store):
-            response.references.append(self._stub(field, values.artifact_id(target)))
-        for collection in schema.get("parts", {}):
-            for item in artifact.get(collection, []):
-                response.parts.append(kb_pb2.PartStub(collection=collection, id=item["id"], title=item["title"]))
-        for (type_name, field), count in self._inbound(str(locator.id)).items():
-            response.inbound.append(kb_pb2.InboundCount(type=type_name, field=field, count=count))
-        return response
 
     def Validate(self, request, context):
         """Every artifact checked against the current version of its type, and listed as stale when it was last
@@ -196,7 +124,7 @@ class KbServicer(kb_pb2_grpc.KbServicer):
         hits = search.rank(artifacts, searching.text, sections=searching.sections, fields=searching.fields)
         return kb_pb2.SearchResponse(matches=[
             kb_pb2.Match(
-                stub=self._stub("", values.artifact_id(hit.artifact)), section=hit.section, field=hit.field,
+                stub=read.stub(self._store, "", values.artifact_id(hit.artifact)), section=hit.section, field=hit.field,
                 snippet=hit.snippet,
             )
             for hit in hits
@@ -224,7 +152,7 @@ class KbServicer(kb_pb2_grpc.KbServicer):
                         continue
                     seen.add(str(other_id))
                     taken = [*route, kb_pb2.Hop(field=field, id=str(other_id))]
-                    reached.append(kb_pb2.Reached(stub=self._stub(field, other_id), route=taken))
+                    reached.append(kb_pb2.Reached(stub=read.stub(self._store, field, other_id), route=taken))
                     following.append((other_id, taken))
             frontier = following
         return kb_pb2.RefsResponse(reached=reached)
@@ -259,7 +187,7 @@ class KbServicer(kb_pb2_grpc.KbServicer):
         ]
         if listing.ids:
             return kb_pb2.ListResponse(ids=[str(artifact_id) for artifact_id in matched])
-        return kb_pb2.ListResponse(stubs=[self._stub("", artifact_id) for artifact_id in matched])
+        return kb_pb2.ListResponse(stubs=[read.stub(self._store, "", artifact_id) for artifact_id in matched])
 
     def Snapshot(self, request, context):
         """One journal entry listing each artifact named with its version now and the fingerprint of its file, under
@@ -285,25 +213,6 @@ class KbServicer(kb_pb2_grpc.KbServicer):
         signed = values.signed(request.actor, request.message)
         return kb_pb2.SnapshotResponse(entry=write.record(self._store, read, signed))
 
-    def _stub(self, field, target_id: ArtifactId):
-        target = self._store.load(target_id)
-        schema = self._store.schema(target_id.kind)["schema"]
-        return kb_pb2.Stub(
-            field=field, id=target["id"], type=target["type"], title=target["title"],
-            fields=dumps(_summary_fields(target, schema)),
-        )
-
-    def _inbound(self, artifact_id: str):
-        """How many artifacts point at this one, by their type and the field they use."""
-        counts = {}
-        for other in self._store.artifacts():
-            schema = self._store.schema(values.kind(other["type"]))["schema"]
-            pointing = {field for field, _, target in validation.links(other, schema, self._store) if target == artifact_id}
-            for field in pointing:
-                counts[(other["type"], field)] = counts.get((other["type"], field), 0) + 1
-        return counts
-
-
 def _holds(artifact: dict, fields) -> bool:
     """Whether each field named holds the value given, compared as the text the value is written as."""
     return all(field in artifact and text(artifact[field]) == value for field, value in fields.items())
@@ -318,19 +227,3 @@ def _entry(entry: dict) -> kb_pb2.Entry:
         schema_version=entry.get("schema_version", 0), digest=entry.get("digest", ""), message=entry["message"],
         batch=entry["batch"], read=[kb_pb2.Snapshotted(**read) for read in entry.get("read", [])],
     )
-
-
-def _find_section(sections: list, title: str) -> dict | None:
-    """The first section titled so, looking at each section before the sections inside it."""
-    for section in sections:
-        if section["title"] == title:
-            return section
-        found = _find_section(section.get("sections", []), title)
-        if found is not None:
-            return found
-    return None
-
-
-def _summary_fields(artifact, schema):
-    return {name: artifact[name] for name in schema.get("summary", []) if name in artifact}
-
```

- [ ] **Step 3: See the check pass**

Run: `make test`
Expected: `118 passed, 508 warnings in …`

Run: `grep -nE "\.save\(|\.remove\(|\.commit\(|journal\.(write|snapshot)" src/kb/read.py`
Expected: no output

Run: `wc -l src/kb/read.py src/kb/servicer.py`
Expected: 116 and 229

- [ ] **Step 4: Run the probe**

Run: `.venv/bin/python /tmp/kb-probe.py > /tmp/kb-probe-now.txt 2>&1; diff /tmp/kb-probe-after-57.txt /tmp/kb-probe-now.txt`
Expected: no output (the probe's output is identical to `/tmp/kb-probe-after-57.txt`)

- [ ] **Step 5: Mark the slice green and commit**

In `docs/superpowers/plans/2026-09-24-kb-slices.md`, set slice 60's `Status:` to `green` and append a log line: `- <date> slice 60 green. <what its check showed>. Surprised by: <anything, or nothing>.`

```bash
git add -A src/kb docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 60: Reads are their own module

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 9: Slice 61, Queries are their own module

**Files:**
- Create: `src/kb/query.py`: `listing`, `walk`, `found`, `entries`, `snapshotted`
- Modify: `src/kb/validation.py`: gains `check(store) -> kb_pb2.ValidateResponse`, the whole-store check
- Modify: `src/kb/servicer.py`: Validate, Journal, Search, Refs, List and Snapshot are each one call

**Interfaces:**
- Consumes: `read.stub` (task 8), `requests.*` query values (task 2), `write.record` (task 4)
- Produces:
- `query.listing(store, Listing) -> ListResponse`, `query.walk(store, Walk) -> RefsResponse` (raises `Refused` for a missing start), `query.found(store, Searching) -> SearchResponse`, `query.entries(store, JournalFilter) -> JournalResponse`, `query.snapshotted(store, named: list) -> list[dict]` (raises `Refused` with every fault, in the order named)
- `validation.check(store) -> kb_pb2.ValidateResponse`

- [ ] **Step 1: See the check fail**

Run: `ls src/kb/query.py; grep -c "def Validate\|def Journal\|def Search\|def Refs\|def List\|def Snapshot" src/kb/servicer.py; wc -l < src/kb/servicer.py`
Expected: `No such file or directory`; `6`; `229`

- [ ] **Step 2: Apply the change**

Save the patch as `/tmp/kb-slice-61.patch`, then run: `git apply --check /tmp/kb-slice-61.patch && git apply /tmp/kb-slice-61.patch`
Expected: no output

```diff
diff --git a/src/kb/query.py b/src/kb/query.py
new file mode 100644
index 0000000..7b5140d
--- /dev/null
+++ b/src/kb/query.py
@@ -0,0 +1,130 @@
+"""Questions asked of the loaded corpus: the artifacts of a kind, what links reach out of or into an artifact, where
+words occur, what the journal holds, and what a piece of work read. Nothing here writes."""
+from datetime import datetime
+
+from kb import journal, read, refusals, search, validation, values
+from kb.content import text
+from kb.contract import kb_pb2
+from kb.requests import JournalFilter, Listing, Refusal, Searching, Walk
+from kb.store import Store
+from kb.values import ArtifactId, Refused
+
+
+def listing(store: Store, asked: Listing) -> kb_pb2.ListResponse:
+    """Every artifact of a kind whose fields hold the values asked for, in path order, as stubs or names."""
+    matched = [
+        artifact_id for artifact_id in store.ids()
+        if artifact_id.kind == asked.kind and _holds(store.load(artifact_id), asked.fields)
+    ]
+    if asked.ids:
+        return kb_pb2.ListResponse(ids=[str(artifact_id) for artifact_id in matched])
+    return kb_pb2.ListResponse(stubs=[read.stub(store, "", artifact_id) for artifact_id in matched])
+
+
+def walk(store: Store, asked: Walk) -> kb_pb2.RefsResponse:
+    """What an artifact's links reach, out of it or into it, a step at a time out to the depth asked: each artifact
+    once, by the shortest route, the one asked about never. A via or a type narrows every step. Raises Refused for
+    a name the store lacks."""
+    start = asked.locator.id
+    if not store.holds(start):
+        raise Refused([refusals.not_found(start)])
+    step = _inward if asked.inward else _outward
+    reached, seen, frontier = [], {str(start)}, [(start, [])]
+    for _ in range(asked.depth):
+        following = []
+        for artifact_id, route in frontier:
+            for field, other_id in step(store, artifact_id):
+                if str(other_id) in seen or (asked.via and field != asked.via):
+                    continue
+                if asked.kind is not None and other_id.kind != asked.kind:
+                    continue
+                seen.add(str(other_id))
+                taken = [*route, kb_pb2.Hop(field=field, id=str(other_id))]
+                reached.append(kb_pb2.Reached(stub=read.stub(store, field, other_id), route=taken))
+                following.append((other_id, taken))
+        frontier = following
+    return kb_pb2.RefsResponse(reached=reached)
+
+
+def found(store: Store, asked: Searching) -> kb_pb2.SearchResponse:
+    """Every section whose prose, or field whose value, holds a word searched for, as the scope asks, among the
+    artifacts of one kind when a type is given, with a stub of its artifact, most often first."""
+    artifacts = (
+        artifact for artifact in store.artifacts() if asked.kind is None or artifact["type"] == asked.kind.name
+    )
+    hits = search.rank(artifacts, asked.text, sections=asked.sections, fields=asked.fields)
+    return kb_pb2.SearchResponse(matches=[
+        kb_pb2.Match(
+            stub=read.stub(store, "", values.artifact_id(hit.artifact)), section=hit.section, field=hit.field,
+            snippet=hit.snippet,
+        )
+        for hit in hits
+    ])
+
+
+def entries(store: Store, asked: JournalFilter) -> kb_pb2.JournalResponse:
+    """The journal's entries, oldest first, narrowed by each of artifact, role, piece of work, time and set given."""
+    return kb_pb2.JournalResponse(entries=[
+        _entry(entry) for entry in journal.entries(store.dir)
+        if (asked.artifact is None or entry.get("artifact") == str(asked.artifact))
+        and (not asked.role or entry["actor"]["role"] == asked.role)
+        and (not asked.execution or entry["actor"]["execution"] == asked.execution)
+        and (asked.since is None or datetime.fromisoformat(entry["at"]) >= asked.since)
+        and (not asked.batch or entry["batch"] == asked.batch)
+    ])
+
+
+def snapshotted(store: Store, named: list) -> list[dict]:
+    """Each artifact named with its version now and the fingerprint of its file. Raises Refused with a fault for
+    every name that did not convert or that the store lacks, in the order named."""
+    faults = []
+    for artifact_id in named:
+        if isinstance(artifact_id, Refusal):
+            faults += artifact_id.faults
+        elif not store.holds(artifact_id):
+            faults.append(refusals.not_found(artifact_id))
+    if faults:
+        raise Refused(faults)
+    return [
+        {
+            "artifact": str(artifact_id), "revision": store.load(artifact_id)["revision"],
+            "digest": journal.digest(store.path(artifact_id)),
+        }
+        for artifact_id in named
+    ]
+
+
+def _outward(store: Store, artifact_id: ArtifactId) -> list[tuple[str, ArtifactId]]:
+    """Each link out of an artifact, as the field and the name it points at."""
+    artifact = store.load(artifact_id)
+    schema = store.schema(artifact_id.kind)["schema"]
+    return [(field, values.artifact_id(target)) for field, _, target in validation.links(artifact, schema, store)]
+
+
+def _inward(store: Store, artifact_id: ArtifactId) -> list[tuple[str, ArtifactId]]:
+    """Each link into an artifact or a part inside it, as the field that points there and the artifact that holds
+    that field, in path order."""
+    pointing = []
+    for other_id in store.ids():
+        other = store.load(other_id)
+        schema = store.schema(other_id.kind)["schema"]
+        for field, _, target in validation.links(other, schema, store):
+            if validation.points_at(target, artifact_id):
+                pointing.append((field, other_id))
+    return pointing
+
+
+def _holds(artifact: dict, fields: dict) -> bool:
+    """Whether each field named holds the value given, compared as the text the value is written as."""
+    return all(field in artifact and text(artifact[field]) == value for field, value in fields.items())
+
+
+def _entry(entry: dict) -> kb_pb2.Entry:
+    """An entry as the contract carries it. A snapshot's entry has no artifact, place, version or fingerprint of its
+    own, only what was read."""
+    return kb_pb2.Entry(
+        id=entry["id"], at=entry["at"], actor=kb_pb2.Actor(**entry["actor"]), op=entry["op"],
+        artifact=entry.get("artifact", ""), path=entry.get("path", ""), revision=entry.get("revision", 0),
+        schema_version=entry.get("schema_version", 0), digest=entry.get("digest", ""), message=entry["message"],
+        batch=entry["batch"], read=[kb_pb2.Snapshotted(**each) for each in entry.get("read", [])],
+    )
diff --git a/src/kb/servicer.py b/src/kb/servicer.py
index 2f6ab9b..696a0d2 100644
--- a/src/kb/servicer.py
+++ b/src/kb/servicer.py
@@ -3,14 +3,9 @@
 Each rpc first turns what the request carries into checked values (kb.values); nothing past that point sees a
 string that came from the request.
 """
-from datetime import datetime
-
-from kb import canonical, journal, read, requests, search, validation, values, write
-from kb.content import text
+from kb import query, read, requests, validation, values, write
 from kb.contract import kb_pb2, kb_pb2_grpc
-from kb.store import Store, Unreadable
-from kb.values import ArtifactId
-from kb.refusals import not_found as _not_found
+from kb.store import Store
 
 
 class KbServicer(kb_pb2_grpc.KbServicer):
@@ -79,151 +74,36 @@ class KbServicer(kb_pb2_grpc.KbServicer):
             return kb_pb2.ReadResponse(faults=refused.faults)
 
     def Validate(self, request, context):
-        """Every artifact checked against the current version of its type, and listed as stale when it was last
-        checked against an older one; a file that cannot be read is reported and the check goes on."""
-        violations, stale = [], []
-        for artifact_id in self._store.ids():
-            try:
-                artifact = self._store.load(artifact_id)
-                schema = self._store.schema(artifact_id.kind)
-            except Unreadable as unreadable:
-                violations.append(unreadable.fault)
-                continue
-            if artifact["schema_version"] < schema["version"]:
-                stale.append(kb_pb2.Stale(
-                    artifact=str(artifact_id), schema_version=artifact["schema_version"], current=schema["version"],
-                ))
-            content = {key: value for key, value in artifact.items() if key not in canonical.IDENTITY[:4]}
-            violations += validation.validate(str(artifact_id), content, schema["schema"], self._store)
-        return kb_pb2.ValidateResponse(violations=violations, stale=stale)
+        return validation.check(self._store)
 
     def Journal(self, request, context):
-        """The journal's entries, oldest first, narrowed by each of artifact, role, piece of work, time and set given."""
         try:
-            wanted = requests.journal(request)
+            return query.entries(self._store, requests.journal(request))
         except values.Refused as refused:
             return kb_pb2.JournalResponse(faults=refused.faults)
-        return kb_pb2.JournalResponse(entries=[
-            _entry(entry) for entry in journal.entries(self._store.dir)
-            if (wanted.artifact is None or entry.get("artifact") == str(wanted.artifact))
-            and (not wanted.role or entry["actor"]["role"] == wanted.role)
-            and (not wanted.execution or entry["actor"]["execution"] == wanted.execution)
-            and (wanted.since is None or datetime.fromisoformat(entry["at"]) >= wanted.since)
-            and (not wanted.batch or entry["batch"] == wanted.batch)
-        ])
 
     def Search(self, request, context):
-        """Every section whose prose, or field whose value, holds a word searched for, as the scope asks, among the
-        artifacts of one kind when a type is given, with a stub of its artifact, most often first."""
         try:
-            searching = requests.searching(request)
+            return query.found(self._store, requests.searching(request))
         except values.Refused as refused:
             return kb_pb2.SearchResponse(faults=refused.faults)
-        kind = searching.kind
-        artifacts = (artifact for artifact in self._store.artifacts() if kind is None or artifact["type"] == kind.name)
-        hits = search.rank(artifacts, searching.text, sections=searching.sections, fields=searching.fields)
-        return kb_pb2.SearchResponse(matches=[
-            kb_pb2.Match(
-                stub=read.stub(self._store, "", values.artifact_id(hit.artifact)), section=hit.section, field=hit.field,
-                snippet=hit.snippet,
-            )
-            for hit in hits
-        ])
 
     def Refs(self, request, context):
-        """What an artifact's links reach, out of it or into it, a step at a time out to the depth asked: each artifact
-        once, by the shortest route, the one asked about never. A via or a type narrows every step."""
         try:
-            walk = requests.walk(request)
+            return query.walk(self._store, requests.walk(request))
         except values.Refused as refused:
             return kb_pb2.RefsResponse(faults=refused.faults)
-        locator, kind = walk.locator, walk.kind
-        if not self._store.holds(locator.id):
-            return kb_pb2.RefsResponse(faults=[_not_found(locator.id)])
-        step = self._inward if walk.inward else self._outward
-        reached, seen, frontier = [], {str(locator.id)}, [(locator.id, [])]
-        for _ in range(walk.depth):
-            following = []
-            for artifact_id, route in frontier:
-                for field, other_id in step(artifact_id):
-                    if str(other_id) in seen or (walk.via and field != walk.via):
-                        continue
-                    if kind is not None and other_id.kind != kind:
-                        continue
-                    seen.add(str(other_id))
-                    taken = [*route, kb_pb2.Hop(field=field, id=str(other_id))]
-                    reached.append(kb_pb2.Reached(stub=read.stub(self._store, field, other_id), route=taken))
-                    following.append((other_id, taken))
-            frontier = following
-        return kb_pb2.RefsResponse(reached=reached)
-
-    def _outward(self, artifact_id: ArtifactId) -> list[tuple[str, ArtifactId]]:
-        """Each link out of an artifact, as the field and the name it points at."""
-        artifact = self._store.load(artifact_id)
-        schema = self._store.schema(artifact_id.kind)["schema"]
-        return [(field, values.artifact_id(target)) for field, _, target in validation.links(artifact, schema, self._store)]
-
-    def _inward(self, artifact_id: ArtifactId) -> list[tuple[str, ArtifactId]]:
-        """Each link into an artifact or a part inside it, as the field that points there and the artifact that holds
-        that field, in path order."""
-        found = []
-        for other_id in self._store.ids():
-            other = self._store.load(other_id)
-            schema = self._store.schema(other_id.kind)["schema"]
-            for field, _, target in validation.links(other, schema, self._store):
-                if validation.points_at(target, artifact_id):
-                    found.append((field, other_id))
-        return found
 
     def List(self, request, context):
-        """Every artifact of a kind whose fields hold the values asked for, in path order, as stubs or names."""
         try:
-            listing = requests.listing(request)
+            return query.listing(self._store, requests.listing(request))
         except values.Refused as refused:
             return kb_pb2.ListResponse(faults=refused.faults)
-        matched = [
-            artifact_id for artifact_id in self._store.ids()
-            if artifact_id.kind == listing.kind and _holds(self._store.load(artifact_id), listing.fields)
-        ]
-        if listing.ids:
-            return kb_pb2.ListResponse(ids=[str(artifact_id) for artifact_id in matched])
-        return kb_pb2.ListResponse(stubs=[read.stub(self._store, "", artifact_id) for artifact_id in matched])
 
     def Snapshot(self, request, context):
-        """One journal entry listing each artifact named with its version now and the fingerprint of its file, under
-        the actor and the message given, in a commit of its own."""
-        named, faults = [], []
-        for artifact_id in requests.snapshotted(request.artifacts):
-            if isinstance(artifact_id, requests.Refusal):
-                faults += artifact_id.faults
-                continue
-            if not self._store.holds(artifact_id):
-                faults.append(_not_found(artifact_id))
-                continue
-            named.append(artifact_id)
-        if faults:
-            return kb_pb2.SnapshotResponse(faults=faults)
-        read = [
-            {
-                "artifact": str(artifact_id), "revision": self._store.load(artifact_id)["revision"],
-                "digest": journal.digest(self._store.path(artifact_id)),
-            }
-            for artifact_id in named
-        ]
+        try:
+            snapshotted = query.snapshotted(self._store, requests.snapshotted(request.artifacts))
+        except values.Refused as refused:
+            return kb_pb2.SnapshotResponse(faults=refused.faults)
         signed = values.signed(request.actor, request.message)
-        return kb_pb2.SnapshotResponse(entry=write.record(self._store, read, signed))
-
-def _holds(artifact: dict, fields) -> bool:
-    """Whether each field named holds the value given, compared as the text the value is written as."""
-    return all(field in artifact and text(artifact[field]) == value for field, value in fields.items())
-
-
-def _entry(entry: dict) -> kb_pb2.Entry:
-    """An entry as the contract carries it. A snapshot's entry has no artifact, place, version or fingerprint of its
-    own, only what was read."""
-    return kb_pb2.Entry(
-        id=entry["id"], at=entry["at"], actor=kb_pb2.Actor(**entry["actor"]), op=entry["op"],
-        artifact=entry.get("artifact", ""), path=entry.get("path", ""), revision=entry.get("revision", 0),
-        schema_version=entry.get("schema_version", 0), digest=entry.get("digest", ""), message=entry["message"],
-        batch=entry["batch"], read=[kb_pb2.Snapshotted(**read) for read in entry.get("read", [])],
-    )
+        return kb_pb2.SnapshotResponse(entry=write.record(self._store, snapshotted, signed))
diff --git a/src/kb/validation.py b/src/kb/validation.py
index 2ee2942..864decd 100644
--- a/src/kb/validation.py
+++ b/src/kb/validation.py
@@ -9,8 +9,9 @@ from referencing import Registry
 from referencing.exceptions import NoSuchResource
 from referencing.jsonschema import DRAFT202012
 
-from kb import values
+from kb import canonical, values
 from kb.contract import kb_pb2
+from kb.store import Store, Unreadable
 from kb.values import Kind
 
 TYPE_URI = "kb:"
@@ -87,6 +88,26 @@ def validate(artifact_id: str, content: dict, schema: dict, corpus) -> list[kb_p
     return faults
 
 
+def check(store: Store) -> kb_pb2.ValidateResponse:
+    """Every artifact checked against the current version of its type, and listed as stale when it was last
+    checked against an older one; a file that cannot be read is reported and the check goes on."""
+    violations, stale = [], []
+    for artifact_id in store.ids():
+        try:
+            artifact = store.load(artifact_id)
+            schema = store.schema(artifact_id.kind)
+        except Unreadable as unreadable:
+            violations.append(unreadable.fault)
+            continue
+        if artifact["schema_version"] < schema["version"]:
+            stale.append(kb_pb2.Stale(
+                artifact=str(artifact_id), schema_version=artifact["schema_version"], current=schema["version"],
+            ))
+        content = {key: value for key, value in artifact.items() if key not in canonical.IDENTITY[:4]}
+        violations += validate(str(artifact_id), content, schema["schema"], store)
+    return kb_pb2.ValidateResponse(violations=violations, stale=stale)
+
+
 def references(schema: dict, corpus) -> dict[str, dict]:
     """Every field that links to other artifacts, from every schema in the composition, base first, with its `ref`."""
     return {
```

- [ ] **Step 3: See the check pass**

Run: `make test`
Expected: `118 passed, 508 warnings in …`

Run: `for f in query validation; do grep -nE "\.save\(|\.remove\(|\.commit\(|journal\.(write|snapshot)" src/kb/$f.py; done`
Expected: no output

Run: `wc -l src/kb/query.py src/kb/validation.py src/kb/servicer.py`
Expected: 130, 197, 109

- [ ] **Step 4: Run the probe**

Run: `.venv/bin/python /tmp/kb-probe.py > /tmp/kb-probe-now.txt 2>&1; diff /tmp/kb-probe-after-57.txt /tmp/kb-probe-now.txt`
Expected: no output (the probe's output is identical to `/tmp/kb-probe-after-57.txt`)

- [ ] **Step 5: Mark the slice green and commit**

In `docs/superpowers/plans/2026-09-24-kb-slices.md`, set slice 61's `Status:` to `green` and append a log line: `- <date> slice 61 green. <what its check showed>. Surprised by: <anything, or nothing>.`

```bash
git add -A src/kb docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 61: Queries are their own module

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 10: Slice 62, The servicer is an adapter

**Files:**
- Modify: `src/kb/servicer.py`: one `_boundary(response)` wrapper; every rpc is request in, one domain call, response out
- Modify: `src/kb/write.py`: `record(store, named, signed)` gathers what was read through `query.snapshotted` and then records it, so Snapshot is one call

**Interfaces:**
- Consumes: everything above
- Produces:
- `servicer._boundary(response_type)`: the one place a `values.Refused` becomes an rpc's faults
- `write.record(store, named: list, signed) -> str`

- [ ] **Step 1: See the check fail**

Run: `grep -c "try:" src/kb/servicer.py; wc -l < src/kb/servicer.py`
Expected: `12`; `109`

- [ ] **Step 2: Apply the change**

Save the patch as `/tmp/kb-slice-62.patch`, then run: `git apply --check /tmp/kb-slice-62.patch && git apply /tmp/kb-slice-62.patch`
Expected: no output

```diff
diff --git a/src/kb/servicer.py b/src/kb/servicer.py
index 696a0d2..274f369 100644
--- a/src/kb/servicer.py
+++ b/src/kb/servicer.py
@@ -1,63 +1,67 @@
 """The contract's servicer: every rpc, over one store. Hosted in-process today; grpc.server can host it later.
 
-Each rpc first turns what the request carries into checked values (kb.values); nothing past that point sees a
-string that came from the request.
+Each rpc runs inside one boundary: its request becomes values (kb.requests, kb.values), one call is made into the
+domain, and its response is made from what comes back. A refusal anywhere becomes that rpc's faults, here and only
+here.
 """
+import functools
+
 from kb import query, read, requests, validation, values, write
 from kb.contract import kb_pb2, kb_pb2_grpc
 from kb.store import Store
 
 
+def _boundary(response):
+    """The rpc, answered with a response of this type carrying the faults when anything in it is refused."""
+    def wrap(rpc):
+        @functools.wraps(rpc)
+        def run(self, request, context=None):
+            try:
+                return rpc(self, request)
+            except values.Refused as refused:
+                return response(faults=refused.faults)
+        return run
+    return wrap
+
+
 class KbServicer(kb_pb2_grpc.KbServicer):
     def __init__(self, root=None):
         """Over the store at root; with none, a servicer that can only start a store, taking its root from the request."""
         self._store = Store(root) if root is not None else None
 
-    def Init(self, request, context):
-        try:
-            actor, root = requests.starting(request)
-            write.start(root, actor)
-        except values.Refused as refused:
-            return kb_pb2.InitResponse(faults=refused.faults)
+    @_boundary(kb_pb2.InitResponse)
+    def Init(self, request):
+        actor, root = requests.starting(request)
+        write.start(root, actor)
         return kb_pb2.InitResponse()
 
-    def Create(self, request, context):
+    @_boundary(kb_pb2.CreateResponse)
+    def Create(self, request):
         creation = kb_pb2.Creation(type=request.type, title=request.title, content=request.content)
-        try:
-            landed = self._land([kb_pb2.Operation(create=creation)], request)
-        except values.Refused as refused:
-            return kb_pb2.CreateResponse(faults=refused.faults)
-        return kb_pb2.CreateResponse(id=str(landed.results[0].artifact_id), revision=landed.results[0].revision)
+        result = self._land([kb_pb2.Operation(create=creation)], request).results[0]
+        return kb_pb2.CreateResponse(id=str(result.artifact_id), revision=result.revision)
 
-    def Write(self, request, context):
+    @_boundary(kb_pb2.WriteResponse)
+    def Write(self, request):
         replacement = kb_pb2.Replacement(locator=request.locator, content=request.content)
-        try:
-            landed = self._land([kb_pb2.Operation(write=replacement)], request)
-        except values.Refused as refused:
-            return kb_pb2.WriteResponse(faults=refused.faults)
-        return kb_pb2.WriteResponse(revision=landed.results[0].revision)
+        result = self._land([kb_pb2.Operation(write=replacement)], request).results[0]
+        return kb_pb2.WriteResponse(revision=result.revision)
 
-    def Append(self, request, context):
+    @_boundary(kb_pb2.AppendResponse)
+    def Append(self, request):
         addition = kb_pb2.Addition(locator=request.locator, content=request.content)
-        try:
-            landed = self._land([kb_pb2.Operation(append=addition)], request)
-        except values.Refused as refused:
-            return kb_pb2.AppendResponse(faults=refused.faults)
-        return kb_pb2.AppendResponse(id=landed.results[0].item, revision=landed.results[0].revision)
+        result = self._land([kb_pb2.Operation(append=addition)], request).results[0]
+        return kb_pb2.AppendResponse(id=result.item, revision=result.revision)
 
-    def Delete(self, request, context):
+    @_boundary(kb_pb2.DeleteResponse)
+    def Delete(self, request):
         removal = kb_pb2.Removal(locator=request.locator)
-        try:
-            landed = self._land([kb_pb2.Operation(delete=removal)], request)
-        except values.Refused as refused:
-            return kb_pb2.DeleteResponse(faults=refused.faults)
-        return kb_pb2.DeleteResponse(revision=landed.results[0].revision)
-
-    def Apply(self, request, context):
-        try:
-            landed = self._land(request.operations, request)
-        except values.Refused as refused:
-            return kb_pb2.ApplyResponse(faults=refused.faults)
+        result = self._land([kb_pb2.Operation(delete=removal)], request).results[0]
+        return kb_pb2.DeleteResponse(revision=result.revision)
+
+    @_boundary(kb_pb2.ApplyResponse)
+    def Apply(self, request):
+        landed = self._land(request.operations, request)
         return kb_pb2.ApplyResponse(batch=landed.batch, results=[
             kb_pb2.Result(id=str(result.artifact_id), revision=result.revision, item=result.item)
             for result in landed.results
@@ -67,43 +71,31 @@ class KbServicer(kb_pb2_grpc.KbServicer):
         """A set of operations landed under the request's actor and message."""
         return write.land(self._store, requests.operations(operations), values.signed(request.actor, request.message))
 
-    def Read(self, request, context):
-        try:
-            return read.artifact(self._store, requests.reading(request))
-        except values.Refused as refused:
-            return kb_pb2.ReadResponse(faults=refused.faults)
+    @_boundary(kb_pb2.ReadResponse)
+    def Read(self, request):
+        return read.artifact(self._store, requests.reading(request))
 
-    def Validate(self, request, context):
+    @_boundary(kb_pb2.ValidateResponse)
+    def Validate(self, request):
         return validation.check(self._store)
 
-    def Journal(self, request, context):
-        try:
-            return query.entries(self._store, requests.journal(request))
-        except values.Refused as refused:
-            return kb_pb2.JournalResponse(faults=refused.faults)
-
-    def Search(self, request, context):
-        try:
-            return query.found(self._store, requests.searching(request))
-        except values.Refused as refused:
-            return kb_pb2.SearchResponse(faults=refused.faults)
-
-    def Refs(self, request, context):
-        try:
-            return query.walk(self._store, requests.walk(request))
-        except values.Refused as refused:
-            return kb_pb2.RefsResponse(faults=refused.faults)
-
-    def List(self, request, context):
-        try:
-            return query.listing(self._store, requests.listing(request))
-        except values.Refused as refused:
-            return kb_pb2.ListResponse(faults=refused.faults)
-
-    def Snapshot(self, request, context):
-        try:
-            snapshotted = query.snapshotted(self._store, requests.snapshotted(request.artifacts))
-        except values.Refused as refused:
-            return kb_pb2.SnapshotResponse(faults=refused.faults)
-        signed = values.signed(request.actor, request.message)
-        return kb_pb2.SnapshotResponse(entry=write.record(self._store, snapshotted, signed))
+    @_boundary(kb_pb2.JournalResponse)
+    def Journal(self, request):
+        return query.entries(self._store, requests.journal(request))
+
+    @_boundary(kb_pb2.SearchResponse)
+    def Search(self, request):
+        return query.found(self._store, requests.searching(request))
+
+    @_boundary(kb_pb2.RefsResponse)
+    def Refs(self, request):
+        return query.walk(self._store, requests.walk(request))
+
+    @_boundary(kb_pb2.ListResponse)
+    def List(self, request):
+        return query.listing(self._store, requests.listing(request))
+
+    @_boundary(kb_pb2.SnapshotResponse)
+    def Snapshot(self, request):
+        named, signed = requests.snapshotted(request.artifacts), values.signed(request.actor, request.message)
+        return kb_pb2.SnapshotResponse(entry=write.record(self._store, named, signed))
diff --git a/src/kb/write.py b/src/kb/write.py
index 1ca25fa..6287273 100644
--- a/src/kb/write.py
+++ b/src/kb/write.py
@@ -4,7 +4,7 @@ entry per operation naming the set, and one commit. A fault anywhere refuses the
 and nothing is written. Starting a store and recording a snapshot write and commit here too."""
 from typing import NamedTuple
 
-from kb import canonical, edits, journal, refusals, requests
+from kb import canonical, edits, journal, query, refusals, requests
 from kb.metaschema import METASCHEMA
 from kb.edits import Change
 from kb.store import Draft, Store, vacant
@@ -57,9 +57,10 @@ def land(store: Store, operations: list, signed: Signed) -> Landed:
     return _written(store, _serialised(draft, changes), signed)
 
 
-def record(store: Store, read: list[dict], signed: Signed) -> str:
-    """One journal entry listing what a piece of work read, in a commit of its own. Returns the entry's id."""
-    entry = journal.snapshot(store.dir, signed=signed, read=read)
+def record(store: Store, named: list, signed: Signed) -> str:
+    """One journal entry listing each artifact named as it stands now, in a commit of its own. Returns the entry's
+    id; raises Refused, having written nothing, when a name did not convert or the store lacks it."""
+    entry = journal.snapshot(store.dir, signed=signed, read=query.snapshotted(store, named))
     store.commit([entry], signed)
     return entry.stem
 
```

- [ ] **Step 3: See the check pass**

Run: `make test`
Expected: `118 passed, 508 warnings in …`

Run: `grep -c "try:" src/kb/servicer.py; wc -l < src/kb/servicer.py`
Expected: `1`; `101`

Run: `wc -l src/kb/*.py | sort -n | tail -3`
Expected: the largest module is `values.py` at 205 lines, and the total is 1992

Run: `grep -rn "except Exception\|except:" src/kb`
Expected: no output

Run: `for i in $(seq 10); do .venv/bin/python -m pytest -q 2>&1 | tail -1; done`
Expected: ten lines, each `118 passed …`

- [ ] **Step 4: Run the probe**

Run: `.venv/bin/python /tmp/kb-probe.py > /tmp/kb-probe-now.txt 2>&1; diff /tmp/kb-probe-after-57.txt /tmp/kb-probe-now.txt`
Expected: no output (the probe's output is identical to `/tmp/kb-probe-after-57.txt`)

- [ ] **Step 5: Mark the slice green and commit**

In `docs/superpowers/plans/2026-09-24-kb-slices.md`, set slice 62's `Status:` to `green` and append a log line: `- <date> slice 62 green. <what its check showed>. Surprised by: <anything, or nothing>.`

```bash
git add -A src/kb docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 62: The servicer is an adapter

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## After task 10

The slice plan's log records that `CLAUDE.md` rules 1 and 3 hold only as far as slices 57 and 62 take them, with two `QUESTION FOR THE SPEC` entries (dated 2026-09-26):
- what a client gets when an rpc meets a failure no refusal covers;
- whether a set is checked as a whole.

They wait for scenarios. No task here answers them.
