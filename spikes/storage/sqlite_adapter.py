"""THROWAWAY. The storage port met by SQLite: one file per store, one IMMEDIATE transaction per change."""
from __future__ import annotations

import json
import re
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from port import Committed, Entry, Fault, Hit, Link, Reached, Refused

SCHEMA = """
CREATE TABLE IF NOT EXISTS kinds (name TEXT PRIMARY KEY, version INTEGER NOT NULL, base TEXT, body TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS docs (id TEXT PRIMARY KEY, kind TEXT NOT NULL, title TEXT NOT NULL,
                                 revision INTEGER NOT NULL, content TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS docs_kind ON docs(kind, id);
CREATE TABLE IF NOT EXISTS links (source TEXT NOT NULL, source_kind TEXT NOT NULL, field TEXT NOT NULL,
                                  place TEXT NOT NULL, target TEXT NOT NULL, target_doc TEXT NOT NULL,
                                  target_part TEXT NOT NULL, target_kind TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS links_out ON links(source, place);
CREATE INDEX IF NOT EXISTS links_in ON links(target_doc, source, place);
CREATE INDEX IF NOT EXISTS links_in_part ON links(target_doc, target_part);
CREATE TABLE IF NOT EXISTS commits (seq INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, role TEXT NOT NULL,
                                    execution TEXT NOT NULL, message TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS commits_at ON commits(at);
CREATE TABLE IF NOT EXISTS revisions (doc_id TEXT NOT NULL, revision INTEGER NOT NULL, seq INTEGER NOT NULL,
                                      pos INTEGER NOT NULL, op TEXT NOT NULL, kind TEXT NOT NULL, title TEXT,
                                      content TEXT, PRIMARY KEY (doc_id, revision));
CREATE INDEX IF NOT EXISTS revisions_seq ON revisions(seq, pos);
CREATE TABLE IF NOT EXISTS kind_events (seq INTEGER NOT NULL, op TEXT NOT NULL, name TEXT NOT NULL,
                                        version INTEGER NOT NULL, body TEXT);
CREATE VIRTUAL TABLE IF NOT EXISTS search USING fts5(id UNINDEXED, kind UNINDEXED, title, body,
                                                     tokenize='unicode61');
"""

TYPES = {"string", "text", "number", "boolean", "link"}
ITEM_ID = re.compile(r"^[^/#\s]+$")


def open_store(name: str, workdir: Path) -> "SqliteStore":
    return SqliteStore(Path(workdir) / f"{name}.sqlite3")


# ---- the type model -------------------------------------------------------------------------------------------

def base_chain(kinds: dict, name: str) -> list[dict]:
    """The kind and every kind it is built on, base first. Assumes no loop (define refuses one)."""
    chain, seen = [], set()
    while name and name in kinds and name not in seen:
        seen.add(name)
        chain.append(kinds[name])
        name = kinds[name].get("base")
    return list(reversed(chain))


def compose(kinds: dict, name: str) -> dict:
    fields, collections, sections = {}, {}, []
    for k in base_chain(kinds, name):
        fields.update(k.get("fields") or {})
        collections.update(k.get("collections") or {})
        sections += k.get("sections") or []
    return {"fields": fields, "collections": collections, "sections": sections}


def family(kinds: dict, name: str) -> set[str]:
    """The kind and every kind built on it, however deep."""
    return {k for k in kinds if any(c["name"] == name for c in base_chain(kinds, k))}


def kind_faults(kind: Any, kinds: dict) -> list[Fault]:
    """A kind as written, against the kinds it would sit among (itself included)."""
    if not isinstance(kind, dict) or not isinstance(kind.get("name"), str) or not kind.get("name"):
        return [Fault("kind", "", "", "a kind needs a name")]
    name, out = kind["name"], []

    def bad(path, message):
        out.append(Fault("kind", name, path, message))
    if "/" in name or "#" in name:
        bad("name", "a kind's name holds no '/' or '#'")
    if not isinstance(kind.get("version"), int) or isinstance(kind.get("version"), bool):
        bad("version", "version must be an integer")
    known = {**kinds, name: kind}
    base = kind.get("base")
    if base is not None:
        if base not in known:
            bad("base", f"no kind {base!r}")
        else:
            seen, cur = set(), name
            while cur is not None and cur in known:
                if cur in seen:
                    bad("base", "the kind is built on itself")
                    break
                seen.add(cur)
                cur = known[cur].get("base")
    if not isinstance(kind.get("sections", []), list) or not all(isinstance(s, str) for s in kind.get("sections", [])):
        bad("sections", "sections is a list of titles")

    def fields_and_collections(node, prefix):
        for fname, spec in (node.get("fields") or {}).items():
            where = f"{prefix}fields/{fname}"
            if not isinstance(spec, dict) or spec.get("type") not in TYPES:
                bad(where, "a field needs a type of " + ", ".join(sorted(TYPES)))
                continue
            if spec["type"] == "link":
                targets = spec.get("targets")
                if not isinstance(targets, list) or not targets:
                    bad(where, "a link names the kinds it may point at")
                for t in targets or []:
                    if t not in known:
                        bad(where, f"link target {t!r} names no kind")
        for cname, cspec in (node.get("collections") or {}).items():
            if not isinstance(cspec, dict):
                bad(f"{prefix}collections/{cname}", "a collection is a mapping")
                continue
            fields_and_collections(cspec, f"{prefix}collections/{cname}/")
    fields_and_collections(kind, "")
    return out


# ---- content: shape, links, parts -----------------------------------------------------------------------------

def shape_faults(doc: str, content: Any, comp: dict) -> list[Fault]:
    out = []

    def bad(path, message):
        out.append(Fault("shape", doc, path, message))
    if not isinstance(content, dict):
        bad("", "content is not a mapping")
        return out
    _check_node(content, comp["fields"], comp["collections"], "", bad, top=True)
    sections = content.get("sections", [])
    if not isinstance(sections, list):
        bad("sections", "sections is a list")
        return out
    _check_sections(sections, "sections", bad)
    titles = [s.get("title") for s in sections if isinstance(s, dict)]
    required = comp["sections"]
    if titles[:len(required)] != required:
        bad("sections", f"the sections must begin {required}, in order; found {titles}")
    return out


def _check_sections(sections, path, bad):
    for i, s in enumerate(sections):
        here = f"{path}/{i}"
        if not isinstance(s, dict):
            bad(here, "a section is a mapping")
            continue
        for key in set(s) - {"title", "body", "sections"}:
            bad(f"{here}/{key}", "unknown key in a section")
        if not isinstance(s.get("title"), str):
            bad(f"{here}/title", "a section has a title")
        if not isinstance(s.get("body", ""), str):
            bad(f"{here}/body", "a section's body is text")
        inner = s.get("sections", [])
        if not isinstance(inner, list):
            bad(f"{here}/sections", "sections is a list")
        else:
            _check_sections(inner, f"{here}/sections", bad)


def _check_node(node, fields, collections, prefix, bad, top):
    allowed = set(fields) | set(collections) | ({"sections"} if top else {"id"})
    for key in node:
        if key not in allowed:
            bad(prefix + key, "unknown field")
    for name, spec in fields.items():
        value = node.get(name)
        if value is None:
            if spec.get("required"):
                bad(prefix + name, "required field missing")
            continue
        values = value if spec.get("many") else [value]
        if spec.get("many") and not isinstance(value, list):
            bad(prefix + name, "expected a list")
            continue
        for v in values:
            if not _fits(spec["type"], v):
                bad(prefix + name, f"expected {spec['type']}, got {type(v).__name__}")
    for cname, cspec in collections.items():
        items = node.get(cname)
        if items is None:
            continue
        if not isinstance(items, list):
            bad(prefix + cname, "a collection is a list of items")
            continue
        ids = set()
        for i, item in enumerate(items):
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not ITEM_ID.match(item["id"]):
                bad(f"{prefix}{cname}/{i}", "an item is a mapping with an id holding no '/', '#' or space")
                continue
            if item["id"] in ids:
                bad(f"{prefix}{cname}/{item['id']}", "item id used twice in the collection")
            ids.add(item["id"])
            _check_node(item, cspec.get("fields") or {}, cspec.get("collections") or {},
                        f"{prefix}{cname}/{item['id']}/", bad, top=False)


def _fits(kind, v):
    if kind in ("string", "text", "link"):
        return isinstance(v, str)
    if kind == "number":
        return isinstance(v, (int, float)) and not isinstance(v, bool)
    return isinstance(v, bool)


def _items(node, collections, prefix):
    for cname, cspec in collections.items():
        items = node.get(cname) if isinstance(node, dict) else None
        for item in items if isinstance(items, list) else []:
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                yield item, cspec, f"{prefix}{cname}/{item['id']}"


def links_of(content, comp) -> list[tuple[str, str, str, dict]]:
    """(field, place, target, spec) for every link value in the content, wherever it sits."""
    out = []

    def walk(node, fields, collections, prefix):
        for name, spec in fields.items():
            if spec.get("type") != "link" or not isinstance(node, dict) or node.get(name) is None:
                continue
            value = node[name]
            if spec.get("many") and isinstance(value, list):
                out.extend((name, f"{prefix}{name}/{i}", v, spec) for i, v in enumerate(value) if isinstance(v, str))
            elif isinstance(value, str):
                out.append((name, prefix + name, value, spec))
        for item, cspec, path in _items(node, collections, prefix):
            walk(item, cspec.get("fields") or {}, cspec.get("collections") or {}, path + "/")
    walk(content, comp["fields"], comp["collections"], "")
    return out


def parts_of(content, comp) -> set[str]:
    out = set()

    def walk(node, collections, prefix):
        for item, cspec, path in _items(node, collections, prefix):
            out.add(path)
            walk(item, cspec.get("collections") or {}, path + "/")
    walk(content, comp["collections"], "")
    return out


def search_body(content, comp) -> str:
    words = []

    def texts(node, fields, collections, prefix):
        for name, spec in fields.items():
            if spec.get("type") == "text" and isinstance(node, dict):
                v = node.get(name)
                words.extend(x for x in (v if isinstance(v, list) else [v]) if isinstance(x, str))
        for item, cspec, path in _items(node, collections, prefix):
            texts(item, cspec.get("fields") or {}, cspec.get("collections") or {}, path + "/")

    def bodies(sections):
        for s in sections if isinstance(sections, list) else []:
            if isinstance(s, dict):
                if isinstance(s.get("body"), str):
                    words.append(s["body"])
                bodies(s.get("sections"))
    texts(content, comp["fields"], comp["collections"], "")
    bodies(content.get("sections") if isinstance(content, dict) else None)
    return "\n".join(words)


def resolve_refs(value, keys, faults, path=""):
    if isinstance(value, dict) and set(value) == {"ref"}:
        if value["ref"] in keys:
            return keys[value["ref"]]
        faults.append(Fault("set", "", path, f"no create in the set carries key {value['ref']!r}"))
        return value
    if isinstance(value, dict):
        return {k: resolve_refs(v, keys, faults, f"{path}/{k}" if path else k) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve_refs(v, keys, faults, f"{path}/{i}") for i, v in enumerate(value)]
    return value


def utc(moment: str) -> str:
    """An ISO 8601 moment as UTC in the one fixed format commits are stamped in, so strings compare in order."""
    parsed = datetime.fromisoformat(moment)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat(timespec="microseconds")


# ---- the store ------------------------------------------------------------------------------------------------

class SqliteStore:
    def __init__(self, path: Path):
        self._lock = threading.RLock()
        self._db = sqlite3.connect(str(path), timeout=30, isolation_level=None, check_same_thread=False)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=NORMAL")
        with self._write():
            for statement in SCHEMA.split(";"):
                if statement.strip():
                    self._db.execute(statement)

    # transactions

    @contextmanager
    def _write(self):
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                yield self._db
            except BaseException:
                self._db.execute("ROLLBACK")
                raise
            self._db.execute("COMMIT")

    @contextmanager
    def _read(self):
        with self._lock:
            self._db.execute("BEGIN")
            try:
                yield self._db
            finally:
                self._db.execute("COMMIT")

    def _kinds(self) -> dict:
        return {name: json.loads(body) for name, body in self._db.execute("SELECT name, body FROM kinds")}

    def _stamp(self, sig: dict) -> tuple[int, str]:
        at = datetime.now(timezone.utc).isoformat(timespec="microseconds")
        cur = self._db.execute("INSERT INTO commits (at, role, execution, message) VALUES (?, ?, ?, ?)",
                               (at, str(sig.get("role", "")), str(sig.get("execution", "")),
                                str(sig.get("message", ""))))
        return cur.lastrowid, f"c{cur.lastrowid}"

    def _seq(self, commit: str) -> int:
        row = self._db.execute("SELECT seq FROM commits WHERE 'c' || seq = ?", (commit,)).fetchone()
        if not row:
            raise Refused([Fault("not-found", commit, "", "no such commit")])
        return row[0]

    # types

    def define(self, kind: dict, sig: dict) -> None:
        with self._write() as db:
            kinds = self._kinds()
            faults = kind_faults(kind, kinds)
            if faults:
                raise Refused(faults)
            held = kinds.get(kind["name"])
            if held is not None and kind["version"] <= held["version"]:
                raise Refused([Fault("version", kind["name"], "version",
                                     f"held at version {held['version']}; a replacement must move it on")])
            db.execute("INSERT OR REPLACE INTO kinds VALUES (?, ?, ?, ?)",
                       (kind["name"], kind["version"], kind.get("base"), json.dumps(kind)))
            seq, _ = self._stamp(sig)
            db.execute("INSERT INTO kind_events VALUES (?, 'define', ?, ?, ?)",
                       (seq, kind["name"], kind["version"], json.dumps(kind)))

    def remove_kind(self, name: str, sig: dict) -> None:
        with self._write() as db:
            kinds = self._kinds()
            if name not in kinds:
                raise Refused([Fault("kind", name, "", "no such kind")])
            faults = []
            for k in sorted(family(kinds, name)):
                n = db.execute("SELECT count(*) FROM docs WHERE kind = ?", (k,)).fetchone()[0]
                if n:
                    faults.append(Fault("in-use", name, "", f"{n} documents of kind {k!r}"))
            for other, body in kinds.items():
                if other == name:
                    continue
                if body.get("base") == name:
                    faults.append(Fault("in-use", name, "", f"kind {other!r} is built on it"))
                if name in _targets(body):
                    faults.append(Fault("in-use", name, "", f"kind {other!r} links to it"))
            if faults:
                raise Refused(faults)
            db.execute("DELETE FROM kinds WHERE name = ?", (name,))
            seq, _ = self._stamp(sig)
            db.execute("INSERT INTO kind_events VALUES (?, 'remove-kind', ?, ?, NULL)",
                       (seq, name, kinds[name]["version"]))

    def kinds(self) -> list[str]:
        with self._read() as db:
            return [r[0] for r in db.execute("SELECT name FROM kinds ORDER BY name")]

    # changes

    def commit(self, changes: list[dict], sig: dict, expect: dict[str, int] | None = None) -> Committed:
        with self._write():
            return self._apply(changes, sig, expect or {}, keep_ids=False)

    def _apply(self, changes, sig, expect, keep_ids) -> Committed:
        db, kinds, faults = self._db, self._kinds(), []
        if not isinstance(changes, list) or not changes:
            raise Refused([Fault("set", "", "", "a set holds at least one change")])
        for id, revision in expect.items():
            row = db.execute("SELECT revision FROM docs WHERE id = ?", (id,)).fetchone()
            if not row or row[0] != revision:
                faults.append(Fault("conflict", id, "", f"expected revision {revision}, "
                                                        f"found {row[0] if row else 'none'}"))
        keys, ids = self._mint(changes, keep_ids, faults)
        before: dict[str, tuple | None] = {}   # id -> the stored row as the adapter read it, or None
        draft: dict[str, dict | None] = {}     # id -> the document as the set leaves it, None when removed
        steps = []                              # (op, id, doc-after-change or None)

        def current(id):
            if id in draft:
                return draft[id]
            if id not in before:
                row = db.execute("SELECT kind, title, revision, content FROM docs WHERE id = ?", (id,)).fetchone()
                before[id] = row
            row = before[id]
            return None if row is None else {"kind": row[0], "title": row[1], "revision": row[2],
                                             "content": json.loads(row[3])}

        for i, change in enumerate(changes):
            op = change.get("op") if isinstance(change, dict) else None
            if op == "create":
                id = ids[i]
                before.setdefault(id, None)
                kind = change.get("kind")
                if kind not in kinds:
                    faults.append(Fault("kind", id, "", f"no kind {kind!r}"))
                if not isinstance(change.get("title"), str) or not change["title"].strip():
                    faults.append(Fault("shape", id, "title", "a document has a title"))
                content = resolve_refs(change.get("content", {}), keys, faults)
                draft[id] = {"kind": kind, "title": change.get("title"), "revision": 1, "content": content}
            elif op in ("replace", "remove"):
                id = change.get("id")
                doc = current(id) if isinstance(id, str) else None
                if doc is None:
                    faults.append(Fault("not-found", str(id), "", "no such document"))
                    continue
                if op == "replace":
                    content = resolve_refs(change.get("content", {}), keys, faults)
                    draft[id] = {**doc, "revision": doc["revision"] + 1, "content": content}
                else:
                    draft[id] = None
                    steps.append(("remove", id, {**doc, "revision": doc["revision"] + 1, "removed": True}))
                    continue
            else:
                faults.append(Fault("set", "", str(i), f"unknown op {op!r}"))
                continue
            steps.append((op, id, draft[id]))

        faults += self._validate(draft, before, kinds, current)
        if faults:
            raise Refused(faults)
        return self._write_set(steps, draft, before, kinds, sig)

    def _mint(self, changes, keep_ids, faults):
        keys, ids, minted = {}, {}, set()
        for i, change in enumerate(changes):
            if not isinstance(change, dict) or change.get("op") != "create":
                continue
            if keep_ids:
                id = change["id"]
            else:
                stem = f"{change.get('kind')}/{change.get('slug')}"
                id, n = stem, 1
                while id in minted or self._db.execute("SELECT 1 FROM revisions WHERE doc_id = ? LIMIT 1",
                                                       (id,)).fetchone():
                    n += 1
                    id = f"{stem}-{n}"
            minted.add(id)
            ids[i] = id
            key = change.get("key")
            if key is not None:
                if key in keys:
                    faults.append(Fault("set", id, "key", f"key {key!r} captured twice"))
                keys[key] = id
        return keys, ids

    def _validate(self, draft, before, kinds, current) -> list[Fault]:
        faults, comps = [], {}

        def comp(kind):
            if kind not in comps:
                comps[kind] = compose(kinds, kind)
            return comps[kind]
        for id, doc in draft.items():
            if doc is None or doc["kind"] not in kinds:
                continue
            faults += shape_faults(id, doc["content"], comp(doc["kind"]))
            for field, place, target, spec in links_of(doc["content"], comp(doc["kind"])):
                fault = self._landing(id, place, target, spec, kinds, current, comp)
                if fault:
                    faults.append(fault)
        for id, row in list(before.items()):
            if row is None or id not in draft:
                continue   # created in this set, or only read to land a link
            doc = draft[id]
            lost = parts_of(json.loads(row[3]), comp(row[0]))
            if doc is not None:
                lost -= parts_of(doc["content"], comp(doc["kind"]))
                if not lost:
                    continue
            for source, place, target, part in self._db.execute(
                    "SELECT source, place, target, target_part FROM links WHERE target_doc = ?", (id,)):
                if source in draft:
                    continue   # its links as the set leaves them were checked above
                if doc is None or part in lost:
                    faults.append(Fault("linked", id, part, f"{source} links to {target} at {place}"))
        return faults

    def _landing(self, id, place, target, spec, kinds, current, comp) -> Fault | None:
        doc_id, _, part = target.partition("#")
        if part and not spec.get("parts"):
            return Fault("ref", id, place, f"{target}: the field does not accept a place inside a document")
        found = current(doc_id)
        if found is None:
            return Fault("ref", id, place, f"{target}: no such document")
        allowed = set().union(*(family(kinds, t) for t in spec.get("targets") or []))
        if found["kind"] not in allowed:
            return Fault("ref", id, place, f"{target}: a {found['kind']} where {spec.get('targets')} is wanted")
        if part and part not in parts_of(found["content"], comp(found["kind"])):
            return Fault("ref", id, place, f"{target}: no such part")
        return None

    def _write_set(self, steps, draft, before, kinds, sig) -> Committed:
        db = self._db
        seq, commit_id = self._stamp(sig)
        results = []
        for pos, (op, id, doc) in enumerate(steps):
            content = None if doc.get("removed") else json.dumps(doc["content"])
            db.execute("INSERT INTO revisions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (id, doc["revision"], seq, pos, op, doc["kind"], doc["title"], content))
            results.append({"id": id, "revision": doc["revision"]})
        for id, doc in draft.items():
            read = before.get(id)
            if read is not None:   # compare-and-set against the revision read at the start of the set
                if db.execute("DELETE FROM docs WHERE id = ? AND revision = ?", (id, read[2])).rowcount != 1:
                    raise Refused([Fault("conflict", id, "", "the document moved while the set was applied")])
            db.execute("DELETE FROM links WHERE source = ?", (id,))
            db.execute("DELETE FROM search WHERE id = ?", (id,))
            if doc is None:
                continue
            last = max(d["revision"] for op, i, d in steps if i == id)
            db.execute("INSERT INTO docs VALUES (?, ?, ?, ?, ?)",
                       (id, doc["kind"], doc["title"], last, json.dumps(doc["content"])))
            comp = compose(kinds, doc["kind"])
            db.executemany("INSERT INTO links VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
                (id, doc["kind"], field, place, target, target.partition("#")[0], target.partition("#")[2],
                 target.split("/", 1)[0]) for field, place, target, _ in links_of(doc["content"], comp)])
            db.execute("INSERT INTO search VALUES (?, ?, ?, ?)",
                       (id, doc["kind"], doc["title"], search_body(doc["content"], comp)))
        return Committed(commit_id, results)

    # reads

    def read(self, id: str, at: str | None = None) -> dict:
        with self._read() as db:
            if at is None:
                row = db.execute("SELECT id, kind, title, revision, content FROM docs WHERE id = ?", (id,)).fetchone()
            else:
                row = db.execute("SELECT doc_id, kind, title, revision, content FROM revisions WHERE doc_id = ? "
                                 "AND seq <= ? ORDER BY revision DESC LIMIT 1", (id, self._seq(at))).fetchone()
            if row is None or row[4] is None:
                raise Refused([Fault("not-found", id, "", "no such document" + (f" at {at}" if at else ""))])
            return {"id": row[0], "kind": row[1], "title": row[2], "revision": row[3], "content": json.loads(row[4])}

    def list(self, kind: str, where: dict[str, Any] | None = None, at: str | None = None) -> list[str]:
        with self._read() as db:
            kinds = self._kinds()
            if kind not in kinds:
                raise Refused([Fault("kind", kind, "", "no such kind")])
            names = sorted(family(kinds, kind))
            marks = ",".join("?" * len(names))
            if at is None:
                sql = f"SELECT id, content FROM docs WHERE kind IN ({marks})"
                args: list = names
            else:
                sql = (f"SELECT doc_id, content FROM revisions r WHERE kind IN ({marks}) AND seq <= ? AND revision = "
                       f"(SELECT max(revision) FROM revisions WHERE doc_id = r.doc_id AND seq <= ?) "
                       f"AND content IS NOT NULL")
                seq = self._seq(at)
                args = names + [seq, seq]
            post = {}
            for field, value in (where or {}).items():
                if isinstance(value, (str, int, float)) and not isinstance(value, bool) or value is None:
                    sql += " AND json_extract(content, ?) IS ?" if value is None else " AND json_extract(content, ?) = ?"
                    args += [f'$."{field}"', value]
                elif isinstance(value, bool):
                    sql += " AND json_type(content, ?) = ?"
                    args += [f'$."{field}"', "true" if value else "false"]
                else:
                    post[field] = value
            rows = db.execute(sql + " ORDER BY 1", args).fetchall()
            return [id for id, content in rows
                    if not post or all(json.loads(content).get(f) == v for f, v in post.items())]

    def links_out(self, id: str, place: str | None = None, field: str | None = None,
                  kind: str | None = None) -> list[Link]:
        with self._read() as db:
            sql, args = "SELECT source, field, place, target FROM links WHERE source = ?", [id]
            if place is not None:
                sql += " AND substr(place, 1, ?) = ?"
                args += [len(place) + 1, place + "/"]
            sql, args = self._narrow(sql, args, field, kind, "target_kind")
            return [Link(*r) for r in db.execute(sql + " ORDER BY place", args)]

    def links_in(self, id: str, field: str | None = None, kind: str | None = None) -> list[Link]:
        with self._read() as db:
            sql, args = self._narrow("SELECT source, field, place, target FROM links WHERE target_doc = ?", [id],
                                     field, kind, "source_kind")
            return [Link(*r) for r in db.execute(sql + " ORDER BY source, place", args)]

    def _narrow(self, sql, args, field, kind, column):
        if field is not None:
            sql, args = sql + " AND field = ?", args + [field]
        if kind is not None:
            names = sorted(family(self._kinds(), kind)) or [kind]
            sql, args = sql + f" AND {column} IN ({','.join('?' * len(names))})", args + names
        return sql, args

    def inbound_counts(self, id: str) -> dict[tuple[str, str], int]:
        with self._read() as db:
            return {(k, f): n for k, f, n in db.execute(
                "SELECT source_kind, field, count(*) FROM links WHERE target_doc = ? GROUP BY source_kind, field",
                (id,))}

    def traverse(self, id: str, direction: str, depth: int, field: str | None = None,
                 kind: str | None = None) -> list[Reached]:
        if direction not in ("in", "out"):
            raise Refused([Fault("set", id, "", "direction is 'in' or 'out'")])
        near, far, far_kind = (("source", "target_doc", "target_kind") if direction == "out"
                               else ("target_doc", "source", "source_kind"))
        with self._read() as db:
            routes, frontier, out = {id: []}, [id], []
            for _ in range(depth):
                if not frontier:
                    break
                sql = (f"SELECT {near}, field, {far} FROM links WHERE {near} IN ({','.join('?' * len(frontier))})")
                sql, args = self._narrow(sql, list(frontier), field, kind, far_kind)
                step = {}
                for here, f, there in db.execute(sql + f" ORDER BY {near}, field, place", args):
                    if there not in routes and there not in step:
                        step[there] = routes[here] + [(f, there)]
                routes.update(step)
                frontier = sorted(step)
                out += [Reached(r, step[r]) for r in frontier]
            return out

    def search(self, text: str, kind: str | None = None) -> list[Hit]:
        words = re.findall(r"\w+", text)
        if not words:
            return []
        query = " ".join('"' + w.replace('"', '""') + '"' for w in words)
        with self._read() as db:
            sql = ("SELECT id, -bm25(search, 0, 0, 5.0, 1.0), snippet(search, -1, '[', ']', '...', 12) "
                   "FROM search WHERE search MATCH ?")
            args: list = [query]
            if kind is not None:
                names = sorted(family(self._kinds(), kind)) or [kind]
                sql += f" AND kind IN ({','.join('?' * len(names))})"
                args += names
            return [Hit(*r) for r in db.execute(sql + " ORDER BY 2 DESC, 1", args)]

    def history(self, id: str | None = None, role: str | None = None, execution: str | None = None,
                since: str | None = None) -> list[Entry]:
        sql, args = "SELECT seq, at, role, execution, message FROM commits WHERE 1", []
        if id is not None:
            sql, args = sql + " AND seq IN (SELECT seq FROM revisions WHERE doc_id = ?)", args + [id]
        if role is not None:
            sql, args = sql + " AND role = ?", args + [role]
        if execution is not None:
            sql, args = sql + " AND execution = ?", args + [execution]
        if since is not None:
            sql, args = sql + " AND at >= ?", args + [utc(since)]
        with self._read() as db:
            out = []
            for seq, at, r, e, m in db.execute(sql + " ORDER BY seq", args).fetchall():
                changes = [tuple(c) for c in db.execute(
                    "SELECT op, doc_id, revision FROM revisions WHERE seq = ? ORDER BY pos", (seq,))]
                changes += [tuple(c) for c in db.execute(
                    "SELECT op, name, version FROM kind_events WHERE seq = ?", (seq,))]
                out.append(Entry(f"c{seq}", at, r, e, m, changes))
            return out

    def check(self) -> list[Fault]:
        with self._read() as db:
            kinds, faults, comps = self._kinds(), [], {}
            docs = {id: {"kind": k, "content": json.loads(c)}
                    for id, k, c in db.execute("SELECT id, kind, content FROM docs ORDER BY id")}

            def comp(kind):
                if kind not in comps:
                    comps[kind] = compose(kinds, kind)
                return comps[kind]
            for id, doc in docs.items():
                if doc["kind"] not in kinds:
                    faults.append(Fault("kind", id, "", f"no kind {doc['kind']!r}"))
                    continue
                faults += shape_faults(id, doc["content"], comp(doc["kind"]))
                for f, place, target, spec in links_of(doc["content"], comp(doc["kind"])):
                    fault = self._landing(id, place, target, spec, kinds, docs.get, comp)
                    if fault:
                        faults.append(fault)
            return faults

    # moving a corpus

    def export(self) -> Iterator[dict]:
        with self._read() as db:
            kinds = self._kinds()
            rows = db.execute("SELECT id, kind, title, revision, content FROM docs ORDER BY id").fetchall()
        done: list[str] = []
        while len(done) < len(kinds):   # bases before the kinds built on them
            for name in sorted(kinds):
                if name not in done and (kinds[name].get("base") in done or kinds[name].get("base") is None):
                    done.append(name)
        for name in done:
            yield {"kind": kinds[name]}
        for id, kind, title, revision, content in rows:
            yield {"id": id, "kind": kind, "title": title, "revision": revision, "content": json.loads(content)}

    def import_(self, items: list[dict], sig: dict) -> None:
        with self._write() as db:
            if db.execute("SELECT (SELECT count(*) FROM kinds) + (SELECT count(*) FROM revisions)").fetchone()[0]:
                raise Refused([Fault("set", "", "", "import goes into an empty store")])
            kinds = {i["kind"]["name"]: i["kind"] for i in items if isinstance(i.get("kind"), dict)}
            faults = [f for k in kinds.values() for f in kind_faults(k, kinds)]
            if faults:
                raise Refused(faults)
            for k in kinds.values():
                db.execute("INSERT INTO kinds VALUES (?, ?, ?, ?)", (k["name"], k["version"], k.get("base"),
                                                                     json.dumps(k)))
            docs = [i for i in items if "id" in i]
            faults = [Fault("set", d["id"], "", "an id is kind/slug of its kind") for d in docs
                      if d["id"].split("/", 1)[0] != d["kind"]]
            if faults:
                raise Refused(faults)
            if docs:
                self._apply([{"op": "create", "id": d["id"], "kind": d["kind"], "title": d["title"],
                              "content": d["content"]} for d in docs], sig, {}, keep_ids=True)


def _targets(kind: dict) -> set[str]:
    out = set()

    def walk(node):
        for spec in (node.get("fields") or {}).values():
            out.update(spec.get("targets") or [] if isinstance(spec, dict) else [])
        for cspec in (node.get("collections") or {}).values():
            walk(cspec)
    walk(kind)
    return out
