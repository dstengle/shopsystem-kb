"""THROWAWAY. The Store port over TerminusDB 12 (server v12.0.7, Python client `terminusdb` 12.0.5).

What TerminusDB does and what this adapter builds around it is written up in REPORT-terminus.md. In short:
- each kind is a TerminusDB class (Lexical key on the slug, so the port's "kind/slug" id IS the TerminusDB id);
  a base is @inherits; a collection is a Set of @subdocument classes keyed on the item id, ordered by a kb_pos;
  many-valued fields are Arrays; sections are an Array of KbSection subdocuments; a link is a class-typed
  reference, and a link that may point into parts is a KbPartLink subdocument (reference to the document + the
  part's path as text); the neutral kind dict rides in the class's @metadata.
- a set of changes is ONE WOQL query (InsertDocument / UpdateDocument / DeleteDocument) = one commit, all or
  nothing. Guards in the same query (the revision each change was read at, and "nothing else links here" for a
  removal) are re-evaluated by TerminusDB when it retries a contended transaction, which is what refuses a
  lost update: TerminusDB's own data-version header does not (see the report).
"""
from __future__ import annotations

import atexit
import json
import os
import re
import subprocess
import threading
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import requests
from terminusdb_client import Client
from terminusdb_client import WOQLQuery as WQ

from port import Committed, Entry, Fault, Hit, Link, Reached, Refused

IMAGE = "terminusdb/terminusdb-server:v12.0.7"
TEAM, USER, KEY = "admin", "admin", "root"
META = ("kb_title", "kb_slug", "kb_revision", "kb_pos")
MEASURED: dict[str, float] = {}
# Document-API responses are streamed (chunked); on a kept-alive connection each one stalls ~40 ms (the pattern of
# Nagle against delayed ACK). A fresh connection per document-API call avoids it; WOQL answers are not affected.
CLOSE = {"Connection": "close"}

# ---------------------------------------------------------------------------------------------------- the server

_server_lock = threading.Lock()
_server_url: str | None = None


def _docker(*args: str) -> str:
    return subprocess.check_output(["docker", *args], text=True).strip()


def _own_network() -> str | None:
    """When this process runs inside a container on the same Docker daemon, the network it sits on."""
    try:
        nets = json.loads(_docker("inspect", os.uname().nodename, "--format", "{{json .NetworkSettings.Networks}}"))
    except Exception:
        return None
    return next((n for n in nets if n not in ("host", "none")), None)


def _bypass_proxy(host: str) -> None:
    for var in ("NO_PROXY", "no_proxy"):
        os.environ[var] = ",".join(filter(None, [os.environ.get(var, ""), host]))


def _start_server() -> str:
    started = time.perf_counter()
    net = _own_network()
    args = ["run", "-d", "--rm"] + (["--network", net] if net else ["-p", "127.0.0.1::6363"]) + [IMAGE]
    cid = _docker(*args)
    atexit.register(lambda: subprocess.run(["docker", "stop", "-t", "2", cid], capture_output=True))
    if net:
        host = _docker("inspect", cid, "--format", f'{{{{(index .NetworkSettings.Networks "{net}").IPAddress}}}}')
        url = f"http://{host}:6363"
    else:
        host, url = "127.0.0.1", "http://127.0.0.1:" + _docker("port", cid, "6363").splitlines()[0].rsplit(":", 1)[1]
    _bypass_proxy(host)
    session = _session()
    deadline = time.time() + 90
    while time.time() < deadline:
        try:
            if session.get(url + "/api/info", timeout=1).status_code == 200:
                MEASURED["server_start_s"] = time.perf_counter() - started
                MEASURED["container"] = cid
                return url
        except requests.RequestException:
            pass
        time.sleep(0.05)
    raise RuntimeError("TerminusDB did not answer within 90 s")


def server_url() -> str:
    global _server_url
    with _server_lock:
        if _server_url is None:
            env = os.environ.get("TERMINUSDB_URL")
            if env:
                _server_url = env.rstrip("/")
                _bypass_proxy(re.sub(r"^\w+://|:\d+$|/.*$", "", _server_url))
            else:
                _server_url = _start_server()
        return _server_url


def _session() -> requests.Session:
    s = requests.Session()
    s.trust_env = False
    s.auth = (USER, KEY)
    return s


# ---------------------------------------------------------------------------------------------------- kinds

BASE_SCHEMA = [
    {"@type": "Class", "@id": "KbRef", "@abstract": []},
    {"@type": "Class", "@id": "KbSection", "@subdocument": [], "@key": {"@type": "Random"},
     "title": "xsd:string", "body": {"@type": "Optional", "@class": "xsd:string"},
     "sections": {"@type": "Array", "@class": "KbSection"}},
    {"@type": "Class", "@id": "KbPartLink", "@subdocument": [], "@key": {"@type": "Random"},
     "to": "KbDoc", "part": {"@type": "Optional", "@class": "xsd:string"}},
    {"@type": "Class", "@id": "KbDoc", "@abstract": [], "@inherits": ["KbRef"],
     "kb_title": "xsd:string", "kb_slug": "xsd:string", "kb_revision": "xsd:integer",
     "sections": {"@type": "Array", "@class": "KbSection"}},
]
NATIVE_TYPE = {"string": "xsd:string", "text": "xsd:string", "number": "xsd:decimal", "boolean": "xsd:boolean"}


def chain(kinds: dict, name: str) -> list[str]:
    """The kind and its bases, nearest first."""
    out = []
    while name and name in kinds and name not in out:
        out.append(name)
        name = kinds[name].get("base")
    return out


def is_a(kinds: dict, name: str, target: str) -> bool:
    return target in chain(kinds, name)


def _coll_spec(owner_cls: str, name: str, spec: dict) -> dict:
    cls = f"{owner_cls}__{name}"
    return {"cls": cls, "fields": spec.get("fields", {}),
            "collections": {n: _coll_spec(cls, n, s) for n, s in spec.get("collections", {}).items()}}


def resolve(kinds: dict, name: str) -> dict:
    """A kind with everything its bases give it, the base's first."""
    out = {"fields": {}, "collections": {}, "sections": []}
    for k in reversed(chain(kinds, name)):
        kind = kinds[k]
        out["fields"].update(kind.get("fields", {}))
        out["collections"].update({c: _coll_spec(k, c, s) for c, s in kind.get("collections", {}).items()})
        out["sections"] += kind.get("sections", [])
    return out


def _prop(spec: dict) -> dict:
    if spec["type"] == "link":
        targets = spec.get("targets") or []
        # A link that may point into parts is a KbPartLink subdocument: a native reference to the document and
        # the part's path as text. A native reference to another document's subdocument cannot be used: TerminusDB
        # then cascades any update or delete of the linking document into the linked part (see the report).
        cls = "KbPartLink" if spec.get("parts") else targets[0] if len(targets) == 1 else "KbDoc"
    else:
        cls = NATIVE_TYPE[spec["type"]]
    # Never mandatory: the port accepts a kind that leaves held documents unfit (check reports them), and
    # TerminusDB refuses a schema its instances do not satisfy. "required" is the adapter's check.
    return {"@type": "Array" if spec.get("many") else "Optional", "@class": cls}


def _retained(existing: dict, cls: str) -> dict:
    """Properties an earlier version declared: kept, so documents holding them stay valid to TerminusDB."""
    return {k: v for k, v in existing.get(cls, {}).items() if not k.startswith("@")}


def _sub_classes(cls: str, spec: dict, existing: dict) -> list[dict]:
    doc = {"@type": "Class", "@id": cls, "@subdocument": [], "@inherits": ["KbRef"],
           "@key": {"@type": "Lexical", "@fields": ["id"]}, **_retained(existing, cls),
           "id": "xsd:string", "kb_pos": "xsd:integer"}
    out = [doc]
    doc.update({f: _prop(s) for f, s in spec.get("fields", {}).items()})
    for c, s in spec.get("collections", {}).items():
        doc[c] = {"@type": "Set", "@class": f"{cls}__{c}"}
        out += _sub_classes(f"{cls}__{c}", s, existing)
    return out


def classes_for(kind: dict, existing: dict) -> list[dict]:
    name = kind["name"]
    main = {"@type": "Class", "@id": name, "@inherits": [kind.get("base") or "KbDoc"],
            "@key": {"@type": "Lexical", "@fields": ["kb_slug"]}, "@metadata": {"kb": kind},
            **_retained(existing, name)}
    out = [main]
    main.update({f: _prop(s) for f, s in kind.get("fields", {}).items()})
    for c, s in kind.get("collections", {}).items():
        main[c] = {"@type": "Set", "@class": f"{name}__{c}"}
        out += _sub_classes(f"{name}__{c}", s, existing)
    return out


def _link_fields(kind: dict) -> Iterator[dict]:
    yield from (f for f in kind.get("fields", {}).values() if f.get("type") == "link")
    stack = list(kind.get("collections", {}).values())
    while stack:
        c = stack.pop()
        yield from (f for f in c.get("fields", {}).values() if f.get("type") == "link")
        stack += list(c.get("collections", {}).values())


def kind_faults(kinds: dict, kind: dict) -> list[Fault]:
    name, base, faults = kind["name"], kind.get("base"), []
    if base and (base == name or base not in kinds or name in chain(kinds, base)):
        faults.append(Fault("kind", name, "base", f"base {base!r} is not a kind it can be built on"))
    for f in _link_fields(kind):
        for t in f.get("targets", []):
            if t != name and t not in kinds:
                faults.append(Fault("kind", name, "", f"link target {t!r} names no kind"))
    return faults


# ---------------------------------------------------------------------------------------------------- content

def kind_of(id: str) -> str:
    return id.split("/", 1)[0]


def part_link(value: str) -> dict:
    doc, _, frag = value.partition("#")
    return {"@type": "KbPartLink", "to": Node(doc), **({"part": frag} if frag else {})}


def part_paths(content: dict) -> Iterator[str]:
    """Every "collection/item(/collection/item)*" a document's content holds."""
    for k, v in content.items():
        if isinstance(v, list) and all(isinstance(it, dict) and "id" in it for it in v):
            for it in v:
                yield f"{k}/{it['id']}"
                yield from (f"{k}/{it['id']}/{q}" for q in part_paths(it))


class Node(str):
    """A reference: sent to WOQL as a node, not a string."""


def woql_value(o: Any) -> dict:
    """A document as a WOQL Value. The client's own `Doc` sends every string as an xsd:string literal, which
    TerminusDB accepts for a single reference but refuses inside an Array ("ascribed_type_not_subsumed")."""
    if isinstance(o, Node):
        return {"@type": "Value", "node": str(o)}
    if isinstance(o, dict):
        return {"@type": "Value", "dictionary": {"@type": "DictionaryTemplate", "data": [
            {"@type": "FieldValuePair", "field": k, "value": woql_value(v)} for k, v in o.items()]}}
    if isinstance(o, list):
        return {"@type": "Value", "list": [woql_value(x) for x in o]}
    xsd = ("xsd:boolean" if isinstance(o, bool) else "xsd:integer" if isinstance(o, int)
           else "xsd:decimal" if isinstance(o, float) else "xsd:string")
    return {"@type": "Value", "data": {"@type": xsd, "@value": o}}


def _enc_section(s: dict) -> dict:
    out = {"@type": "KbSection", "title": s.get("title"), "sections": [_enc_section(x) for x in s.get("sections") or []]}
    if s.get("body") is not None:
        out["body"] = s["body"]
    return out


def _enc_body(kinds: dict, spec: dict, content: dict) -> dict:
    out = {}
    for k, v in content.items():
        if v is None:
            continue
        if k == "sections":
            out[k] = [_enc_section(s) for s in v]
        elif k in spec["collections"]:
            cs = spec["collections"][k]
            out[k] = [{"@type": cs["cls"], "id": it["id"], "kb_pos": i,
                       **_enc_body(kinds, cs, {x: y for x, y in it.items() if x != "id"})} for i, it in enumerate(v)]
        elif spec["fields"].get(k, {}).get("type") == "link":
            one = part_link if spec["fields"][k].get("parts") else Node
            out[k] = [one(x) for x in v] if isinstance(v, list) else one(v)
        else:
            out[k] = v
    return out


def encode(kinds: dict, kind: str, id: str, slug: str, title: str, rev: int, content: dict) -> dict:
    return {"@type": kind, "@id": id, "kb_slug": slug, "kb_title": title, "kb_revision": rev,
            **_enc_body(kinds, resolve(kinds, kind), content)}


def _dec_section(s: dict) -> dict:
    return {"title": s.get("title"), "body": s.get("body"), "sections": [_dec_section(x) for x in s.get("sections", [])]}


def _dec_scalar(x: Any) -> Any:
    if isinstance(x, dict) and x.get("@type") == "KbPartLink":
        return x["to"] + ("#" + x["part"] if x.get("part") else "")
    return x


def _dec_body(obj: dict) -> dict:
    out = {}
    for k, v in obj.items():
        if k.startswith("@") or k in META:
            continue
        if k == "sections":
            v = [_dec_section(s) for s in v]
        elif isinstance(v, list) and v and isinstance(v[0], dict) and "kb_pos" in v[0]:
            v = [_dec_body(it) for it in sorted(v, key=lambda it: it["kb_pos"])]
        elif isinstance(v, list):
            v = [_dec_scalar(x) for x in v]
        else:
            v = _dec_scalar(v)
        if v != []:
            out[k] = v
    return out


def decode(raw: dict) -> dict:
    return {"id": raw["@id"], "kind": raw["@type"], "title": raw["kb_title"], "revision": raw["kb_revision"],
            "content": _dec_body(raw)}


def substitute(value: Any, refs: dict) -> Any:
    if isinstance(value, dict):
        if set(value) == {"ref"}:
            return refs.get(value["ref"], value)
        return {k: substitute(v, refs) for k, v in value.items()}
    if isinstance(value, list):
        return [substitute(v, refs) for v in value]
    return value


def refs_used(value: Any) -> Iterator[str]:
    if isinstance(value, dict):
        if set(value) == {"ref"}:
            yield value["ref"]
        else:
            for v in value.values():
                yield from refs_used(v)
    elif isinstance(value, list):
        for v in value:
            yield from refs_used(v)


# ---------------------------------------------------------------------------------------------------- the adapter's checks
# What TerminusDB cannot say: required fields and sections (the native schema is kept loose, see _prop), the kind
# a link lands on (TerminusDB checks a reference lands on *a* typed object, never that it is of the range class),
# whether a field may point into parts, and unknown fields against the current version (older versions' fields
# are retained natively). `full` adds what TerminusDB checks natively on every write, for `check`.

def _type_ok(t: str, x: Any) -> bool:
    if t in ("string", "text"):
        return isinstance(x, str)
    if t == "number":
        return isinstance(x, (int, float)) and not isinstance(x, bool)
    return isinstance(x, bool)


def _link_faults(kinds: dict, f: dict, x: Any, doc: str, path: str, known: set | None) -> list[Fault]:
    if not isinstance(x, str) or "/" not in x:
        return [Fault("ref", doc, path, f"{x!r} is not a link")]
    target, _, frag = x.partition("#")
    k = kind_of(target)
    if k not in kinds or not any(is_a(kinds, k, t) for t in f.get("targets", [])):
        return [Fault("ref", doc, path, f"{x} is not a {' or '.join(f.get('targets', []))}")]
    if frag:
        if not f.get("parts"):
            return [Fault("ref", doc, path, f"{x}: this field does not point into parts")]
        spec, segs = resolve(kinds, k), frag.split("/")
        for coll in segs[0::2]:
            if coll not in spec["collections"] or len(segs) % 2:
                return [Fault("ref", doc, path, f"{x}: no such part")]
            spec = spec["collections"][coll]
    if known is not None and x not in known:
        return [Fault("ref", doc, path, f"{x} does not land")]
    return []


def _section_faults(sections: Any, required: list, doc: str) -> list[Fault]:
    if not isinstance(sections, list) or not all(isinstance(s, dict) and isinstance(s.get("title"), str)
                                                 for s in sections):
        return [Fault("shape", doc, "sections", "sections must be a list of {title, body, sections}")]
    if [s["title"] for s in sections[:len(required)]] != required:
        return [Fault("shape", doc, "sections", f"the sections must begin {required}")]
    return []


def body_faults(kinds: dict, spec: dict, content: Any, doc: str, path: str = "", full: bool = False,
                known: set | None = None, top: bool = True) -> list[Fault]:
    if not isinstance(content, dict):
        return [Fault("shape", doc, path, "content must be a mapping")]
    faults = []
    allowed = set(spec["fields"]) | set(spec["collections"]) | ({"sections"} if top else {"id"})
    faults += [Fault("shape", doc, path + k, "unknown field") for k in content if k not in allowed]
    for name, f in spec["fields"].items():
        v, p = content.get(name), path + name
        if v is None:
            if f.get("required"):
                faults.append(Fault("shape", doc, p, "required"))
            continue
        if f.get("many") and not isinstance(v, list):
            faults.append(Fault("shape", doc, p, "must be a list"))
            continue
        for i, x in enumerate(v if f.get("many") else [v]):
            if f["type"] == "link":
                faults += _link_faults(kinds, f, x, doc, f"{p}/{i}" if f.get("many") else p, known)
            elif full and not _type_ok(f["type"], x):
                faults.append(Fault("shape", doc, p, f"not a {f['type']}"))
    for name, cs in spec["collections"].items():
        items = content.get(name)
        if items is None:
            continue
        if not isinstance(items, list):
            faults.append(Fault("shape", doc, path + name, "must be a list"))
            continue
        seen = set()
        for it in items:
            if not isinstance(it, dict) or not isinstance(it.get("id"), str) or it["id"] in seen:
                faults.append(Fault("shape", doc, path + name, "an item needs an id unique in its collection"))
                continue
            seen.add(it["id"])
            faults += body_faults(kinds, cs, it, doc, f"{path}{name}/{it['id']}/", full, known, top=False)
    if top:
        faults += _section_faults(content.get("sections", []), spec["sections"], doc)
    return faults


# ---------------------------------------------------------------------------------------------------- native faults

def _witness_rule(w: dict) -> str:
    kinds = {w.get("@type")} | {v.get("@type") for v in w.values() if isinstance(v, dict)}
    if "deleted_object_still_referenced" in kinds:
        return "linked"
    if any(str(k).startswith("references_untyped") for k in kinds):
        return "ref"
    return "shape"


class _IdTaken(Exception):
    pass


def native_faults(body: dict) -> list[Fault]:
    err = body.get("api:error", {})
    t = err.get("@type", "")
    if t.endswith("SchemaCheckFailure"):
        return [Fault(_witness_rule(w), str(w.get("subject", "")), str(w.get("predicate", "")),
                      "TerminusDB: " + json.dumps(w)[:300]) for w in err.get("api:witnesses", [])]
    if t == "api:DocumentNotFound":
        return [Fault("not-found", str(err.get("api:document_id", "")), "", "TerminusDB: document not found")]
    if t == "api:DocumentIdAlreadyExists":
        raise _IdTaken(err.get("api:document_id"))
    if t == "api:DataVersionMismatch":
        return [Fault("conflict", "", "", "TerminusDB: data version moved")]
    raise RuntimeError(f"TerminusDB: {json.dumps(body)[:1000]}")


# ---------------------------------------------------------------------------------------------------- the store

class TerminusStore:
    def __init__(self, name: str, url: str):
        self.db, self.url = name, url
        self.client = Client(url)
        self.client.connect(team=TEAM, user=USER, key=KEY)
        self.client._session.trust_env = False
        if not self.client.has_database(name, team=TEAM):
            started = time.perf_counter()
            try:
                self.client.create_database(name, team=TEAM, label=name, include_schema=True)
            except Exception:
                if not self.client.has_database(name, team=TEAM):
                    raise
            else:
                self._put_schema(BASE_SCHEMA, "kb", "store", create=False)
                MEASURED.setdefault("create_db_s", []).append(time.perf_counter() - started)  # type: ignore[union-attr]
        self.s = _session()

    # -- transport ---------------------------------------------------------------------------------------------

    def _path(self, api: str, at: str | None = None) -> str:
        where = f"commit/{at}" if at else "branch/main"
        return f"{self.url}/api/{api}/{TEAM}/{self.db}/local/{where}"

    @staticmethod
    def _message(sig: dict, changes: list) -> dict:
        return {"author": sig.get("role", ""), "message": json.dumps(
            {"kb": 1, "execution": sig.get("execution", ""), "message": sig.get("message", ""), "changes": changes})}

    def _woql(self, query: WQ | dict, sig: dict | None = None, changes: list | None = None) -> tuple[dict, str]:
        body = {"query": query.to_dict() if isinstance(query, WQ) else query}
        if sig is not None:
            body["commit_info"] = self._message(sig, changes or [])
        r = self.s.post(self._path("woql"), json=body)
        data = r.json()
        if r.status_code >= 400:
            raise Refused(native_faults(data))
        return data, r.headers.get("TerminusDB-Data-Version", "")

    def _put_schema(self, docs: list[dict], role: str, message: str, create: bool = True) -> str:
        s = getattr(self, "s", None) or _session()
        params = {"graph_type": "schema", **self._message({"role": role, "message": message}, [])}
        if create:
            r = s.put(self._path("document"), params={**params, "create": "true"}, json=docs, headers=CLOSE)
        else:
            r = s.post(self._path("document"), params=params, json=docs, headers=CLOSE)
        if r.status_code >= 400:
            raise Refused(native_faults(r.json()))
        return r.headers.get("TerminusDB-Data-Version", "")

    def _schema(self, at: str | None = None) -> dict:
        r = self.s.get(self._path("document", at), params={"graph_type": "schema", "as_list": "true"}, headers=CLOSE)
        r.raise_for_status()
        return {d["@id"]: d for d in r.json() if "@id" in d}

    def _kinds(self, at: str | None = None) -> dict:
        return {k: d["@metadata"]["kb"] for k, d in self._schema(at).items() if "kb" in d.get("@metadata", {})}

    def _raw(self, id: str, at: str | None = None) -> dict | None:
        """One document as TerminusDB stores it. Through WOQL's ReadDocument, not the document API: a document-API
        GET costs a flat ~45 ms per call on this server however small the database, WOQL ~5 ms (see the report)."""
        body = {"query": WQ().read_document(id, "v:D").to_dict()}
        r = self.s.post(self._path("woql", at), json=body)
        data = r.json()
        if r.status_code == 404 or data.get("api:error", {}).get("@type") == "api:DocumentNotFound":
            return None
        if r.status_code >= 400:
            raise Refused(native_faults(data))
        raw = data["bindings"][0]["D"] if data.get("bindings") else None
        return raw if isinstance(raw, dict) and "kb_revision" in raw else None

    def _all(self) -> list[dict]:
        r = self.s.get(self._path("document"), params={"as_list": "true"}, headers=CLOSE)
        r.raise_for_status()
        return [d for d in r.json() if "kb_revision" in d]

    # -- types -------------------------------------------------------------------------------------------------

    def define(self, kind: dict, sig: dict) -> None:
        kinds = self._kinds()
        faults = kind_faults(kinds, kind)
        held = kinds.get(kind["name"])
        if held is not None and kind.get("version", 0) <= held.get("version", 0):
            faults.append(Fault("version", kind["name"], "", "a changed kind needs a higher version"))
        if faults:
            raise Refused(faults)
        self._put_schema(classes_for(kind, self._schema()), sig.get("role", ""), sig.get("message", ""))

    def remove_kind(self, name: str, sig: dict) -> None:
        schema = self._schema()
        if "kb" not in schema.get(name, {}).get("@metadata", {}):
            raise Refused([Fault("kind", name, "", "no such kind")])
        ids = [name] + [c for c in schema if c.startswith(name + "__")]
        params = {"graph_type": "schema", **self._message(sig, [])}
        r = self.s.delete(self._path("document"), params=params, json=ids, headers=CLOSE)
        if r.status_code >= 400:
            # TerminusDB refuses dropping a class while instances, subclasses or ranges still name it.
            faults = native_faults(r.json())
            raise Refused([Fault("in-use", name, f.path, f.message) for f in faults])

    def kinds(self) -> list[str]:
        return sorted(self._kinds())

    # -- changes -----------------------------------------------------------------------------------------------

    def commit(self, changes: list[dict], sig: dict, expect: dict[str, int] | None = None) -> Committed:
        for _ in range(8):
            try:
                return self._commit_once(changes, sig, expect or {})
            except _IdTaken:
                continue   # another writer took a minted id between our look and our write: mint again
        raise Refused([Fault("conflict", "", "", "ids kept being taken by other writers")])

    def _set_faults(self, changes: list[dict]) -> tuple[dict, list[Fault]]:
        keys, faults = {}, []
        for i, ch in enumerate(changes):
            if ch.get("op") == "create" and ch.get("key"):
                if ch["key"] in keys:
                    faults.append(Fault("set", "", "", f"key {ch['key']!r} captured twice"))
                keys[ch["key"]] = i
        for key in {k for ch in changes for k in refs_used(ch.get("content"))} - set(keys):
            faults.append(Fault("set", "", "", f"key {key!r} is never captured"))
        return keys, faults

    def _mint(self, kinds: dict, changes: list[dict]) -> tuple[dict, list[Fault]]:
        minted, faults, taken = {}, [], set()
        for i, ch in enumerate(changes):
            if ch.get("op") != "create":
                continue
            if ch.get("kind") not in kinds:
                faults.append(Fault("kind", f"{ch.get('kind')}/{ch.get('slug')}", "", "no such kind"))
                continue
            base = f"{ch['kind']}/{ch['slug']}"
            id, n = base, 2
            while id in taken or self._raw(id) is not None:
                id, n = f"{base}-{n}", n + 1
            taken.add(id)
            minted[i] = id
        return minted, faults

    def _inbound(self, iri: str) -> list[tuple[str, str]]:
        """(subject, owning document) of every triple pointing at `iri`, in one WOQL query: a link held in an
        Array hangs off an Array cell (sys:value), whose holder is one more hop; anything else is its own holder
        (a document, or a subdocument whose id starts with its document's)."""
        q = WQ().select("v:S", "v:O").woql_or(
            WQ().woql_and(WQ().triple("v:S", "sys:value", iri), WQ().triple("v:O", "v:F", "v:S")),
            WQ().woql_and(WQ().triple("v:S", "v:P", iri), WQ().woql_not(WQ().triple("v:S", "sys:value", iri)),
                          WQ().eq("v:O", "v:S")))
        data, _ = self._woql(q)
        return sorted({(b["S"], "/".join(b["O"].split("/")[:2])) for b in data["bindings"]})

    def _commit_once(self, changes: list[dict], sig: dict, expect: dict[str, int]) -> Committed:
        kinds = self._kinds()
        keys, faults = self._set_faults(changes)
        if faults:
            raise Refused(faults)
        minted, faults = self._mint(kinds, changes)
        refs = {k: minted[i] for k, i in keys.items() if i in minted}
        state: dict[str, dict] = {}
        results, journal = [], []
        for i, ch in enumerate(changes):
            op = ch.get("op")
            if op == "create":
                if i not in minted:
                    continue
                id = minted[i]
                state[id] = {"kind": ch["kind"], "slug": id.split("/", 1)[1], "title": ch.get("title", ""),
                             "rev": 1, "read": None, "removed": False,
                             "content": substitute(ch.get("content") or {}, refs)}
            elif op in ("replace", "remove"):
                id = ch.get("id", "")
                cur = state.get(id) or self._loaded(id)
                if cur is None or cur["removed"]:
                    faults.append(Fault("not-found", id, "", "no such document"))
                    continue
                cur = {**cur, "rev": cur["rev"] + 1}
                if op == "replace":
                    cur["content"] = substitute(ch.get("content") or {}, refs)
                else:
                    cur["removed"] = True
                state[id] = cur
            else:
                faults.append(Fault("shape", "", "", f"unknown op {op!r}"))
                continue
            results.append({"id": id, "revision": state[id]["rev"]})
            journal.append([op, id, state[id]["rev"]])
        guards = []
        for id, rev in expect.items():
            now = state[id]["read"] if id in state and state[id]["read"] is not None else (self._raw(id) or {}).get("kb_revision")
            if now != rev:
                faults.append(Fault("conflict", id, "", f"read at revision {rev}, now {now}"))
            guards.append(WQ().triple(id, "kb_revision", rev))
        faults += self._integrity(kinds, state, guards)
        if faults:
            raise Refused(faults)
        ops = []
        for id, st in state.items():
            if st["read"] is not None:
                guards.append(WQ().triple(id, "kb_revision", st["read"]))
            if st["removed"]:
                if st["read"] is not None:
                    ops.append(WQ().delete_document(id))
                continue
            doc = woql_value(encode(kinds, st["kind"], id, st["slug"], st["title"], st["rev"], st["content"]))
            ops.append(WQ().insert_document(doc) if st["read"] is None else WQ().update_document(doc))
        if not ops and not guards:
            return Committed(commit=self._head(), results=results)
        data, version = self._woql(WQ().woql_and(*guards, *ops), sig, journal)
        if not data.get("bindings"):
            raise Refused(self._why_not(state, expect))
        return Committed(commit=version.split(":", 1)[-1], results=results)

    def _integrity(self, kinds: dict, state: dict, guards: list) -> list[Fault]:
        """What TerminusDB does not refuse itself, checked against the store as the set leaves it, with a guard
        per check so that TerminusDB's retry of a contended transaction re-checks it."""
        faults, removed = [], {id for id, st in state.items() if st["removed"]}
        for id, st in state.items():
            if st["removed"]:
                continue
            found = body_faults(kinds, resolve(kinds, st["kind"]), st["content"], id)
            faults += found or self._landing_faults(kinds, state, id, st, removed, guards)
        for n, id in enumerate(sorted(i for i, st in state.items() if st["read"] is not None)):
            st = state[id]
            dropped = set() if st["removed"] else set(part_paths(st["was"])) - set(part_paths(st["content"]))
            if not st["removed"] and not dropped:
                continue
            inbound = self._inbound(id)
            for owner in sorted({o for _, o in inbound if o not in state}):
                hits = [l for l in self.links_out(owner, kinds=kinds) if l.target.split("#")[0] == id
                        and (st["removed"] or l.target.partition("#")[2] in dropped
                             or any(l.target.partition("#")[2].startswith(d + "/") for d in dropped))]
                faults += [Fault("linked", id, l.target.partition("#")[2], f"{owner} links to it") for l in hits]
            # Nothing but what links here now may link here when TerminusDB runs (or re-runs) the set.
            allowed = [WQ().woql_not(WQ().eq(f"v:S{n}", WQ().iri(s))) for s, _ in inbound]
            guards.append(WQ().woql_not(WQ().woql_and(WQ().triple(f"v:S{n}", f"v:P{n}", id), *allowed)))
        return faults

    def _landing_faults(self, kinds: dict, state: dict, id: str, st: dict, removed: set, guards: list) -> list[Fault]:
        faults = []
        for l in self._walk(kinds, st["kind"], id, st["content"]):
            target, _, frag = l.target.partition("#")
            if target in removed:
                faults.append(Fault("ref", id, l.place, f"{l.target} is removed in this set"))
            elif frag:
                other = state.get(target) or self._loaded(target)
                if other is None:
                    continue   # no such document: TerminusDB refuses the dangling reference itself
                if frag not in set(part_paths(other["content"])):
                    faults.append(Fault("ref", id, l.place, f"{l.target}: no such part"))
                elif target not in state:   # the part must still be there when TerminusDB runs the set
                    guards.append(WQ().triple(target, "kb_revision", other["rev"]))
        return faults

    def _why_not(self, state: dict, expect: dict) -> list[Fault]:
        """A guard failed when TerminusDB (re)ran the set: say which."""
        faults = []
        for id, rev in list(expect.items()) + [(i, st["read"]) for i, st in state.items() if st["read"] is not None]:
            now = (self._raw(id) or {}).get("kb_revision")
            if now != rev:
                faults.append(Fault("conflict", id, "", f"read at revision {rev}, now {now}"))
        for id in (i for i, st in state.items() if st["removed"] and st["read"] is not None):
            faults += [Fault("linked", id, "", f"{o} links to it") for _, o in self._inbound(id) if o not in state]
        return faults or [Fault("conflict", "", "", "the store moved under the set")]

    def _loaded(self, id: str) -> dict | None:
        raw = self._raw(id)
        if raw is None:
            return None
        d = decode(raw)
        return {"kind": d["kind"], "slug": raw["kb_slug"], "title": d["title"], "rev": d["revision"],
                "read": d["revision"], "removed": False, "content": d["content"], "was": d["content"]}

    def _head(self) -> str:
        r = self.s.get(f"{self.url}/api/log/{TEAM}/{self.db}", params={"count": 1})
        r.raise_for_status()
        log = r.json()
        return log[0]["identifier"] if log else ""

    # -- reads -------------------------------------------------------------------------------------------------

    def read(self, id: str, at: str | None = None) -> dict:
        raw = self._raw(id, at)
        if raw is None:
            raise Refused([Fault("not-found", id, "", "no such document")])
        return decode(raw)

    def list(self, kind: str, where: dict[str, Any] | None = None, at: str | None = None) -> list[str]:
        """WOQL: `isa` answers for kinds built on `kind` too; each `where` is a triple on a literal. (The
        document API's query does the same natively but scans: 1.35 s over 10,000 documents of a kind.)"""
        if kind not in self._kinds(at):
            raise Refused([Fault("kind", kind, "", "no such kind")])
        # The literal triples first: TerminusDB evaluates in order, and a bound object is an index lookup.
        clauses = [WQ().triple("v:D", f, self._literal(v)) for f, v in (where or {}).items()] + [WQ().isa("v:D", kind)]
        r = self.s.post(self._path("woql", at), json={"query": WQ().select("v:D").woql_and(*clauses).to_dict()})
        data = r.json()
        if r.status_code >= 400:
            raise Refused(native_faults(data))
        return sorted({b["D"] for b in data["bindings"]})

    @staticmethod
    def _literal(v: Any) -> Any:
        xsd = ("xsd:boolean" if isinstance(v, bool) else "xsd:decimal" if isinstance(v, (int, float))
               else "xsd:string")
        return {"@type": xsd, "@value": v} if not (isinstance(v, str) and "/" in v) else v

    def _walk(self, kinds: dict, kind: str, id: str, content: dict) -> Iterator[Link]:
        def walk(spec: dict, body: dict, prefix: str) -> Iterator[Link]:
            for name, f in spec["fields"].items():
                v = body.get(name)
                if f["type"] != "link" or v is None:
                    continue
                if f.get("many") and isinstance(v, list):
                    yield from (Link(id, name, f"{prefix}{name}/{i}", x) for i, x in enumerate(v))
                else:
                    yield Link(id, name, prefix + name, v)
            for name, cs in spec["collections"].items():
                for it in body.get(name) or []:
                    yield from walk(cs, it, f"{prefix}{name}/{it['id']}/")
        yield from walk(resolve(kinds, kind), content, "")

    def links_out(self, id: str, place: str | None = None, field: str | None = None,
                  kind: str | None = None, kinds: dict | None = None) -> list[Link]:
        kinds = kinds or self._kinds()
        doc = self.read(id)
        links = [l for l in self._walk(kinds, doc["kind"], id, doc["content"])
                 if (place is None or l.place.startswith(place.rstrip("/") + "/"))
                 and (field is None or l.field == field)
                 and (kind is None or is_a(kinds, kind_of(l.target), kind))]
        return sorted(links, key=lambda l: l.place)

    def links_in(self, id: str, field: str | None = None, kind: str | None = None,
                 kinds: dict | None = None) -> list[Link]:
        raw = self._raw(id)
        if raw is None:
            raise Refused([Fault("not-found", id, "", "no such document")])
        kinds = kinds or self._kinds()
        sources = sorted({o for _, o in self._inbound(id)})
        links = [l for src in sources if kind is None or is_a(kinds, kind_of(src), kind)
                 for l in self.links_out(src, field=field, kinds=kinds)
                 if l.target == id or l.target.startswith(id + "#")]
        return sorted(links, key=lambda l: (l.source, l.place))

    def inbound_counts(self, id: str) -> dict[tuple[str, str], int]:
        return dict(Counter((kind_of(l.source), l.field) for l in self.links_in(id)))

    def traverse(self, id: str, direction: str, depth: int, field: str | None = None,
                 kind: str | None = None) -> list[Reached]:
        kinds = self._kinds()
        seen, frontier, out = {id}, [(id, [])], []
        for _ in range(depth):
            reached = []
            for node, route in frontier:
                if direction == "out":
                    edges = [(l.field, l.target.split("#")[0]) for l in self.links_out(node, field=field, kinds=kinds)]
                else:
                    edges = [(l.field, l.source) for l in self.links_in(node, field=field, kinds=kinds)]
                for f, other in edges:
                    if other in seen or (kind and not is_a(kinds, kind_of(other), kind)):
                        continue
                    seen.add(other)
                    reached.append((other, route + [(f, other)]))
            reached.sort(key=lambda r: r[0])
            out += [Reached(n, r) for n, r in reached]
            frontier = reached
        return out

    def search(self, text: str, kind: str | None = None) -> list[Hit]:
        """An adapter-side scan: TerminusDB 12 has no text index (see the report)."""
        words = re.findall(r"\w+", text.lower())
        kinds, hits = self._kinds(), []
        for raw in self._all():
            d = decode(raw)
            if kind and not is_a(kinds, d["kind"], kind):
                continue
            texts = [d["title"], *self._prose(resolve(kinds, d["kind"]), d["content"])]
            counts = Counter(w for t in texts for w in re.findall(r"\w+", t.lower()))
            if words and all(counts[w] for w in words):
                snippet = next(t for t in texts if words[0] in t.lower())
                hits.append(Hit(d["id"], float(sum(counts[w] for w in words)), snippet[:120]))
        return sorted(hits, key=lambda h: (-h.score, h.id))

    def _prose(self, spec: dict, body: dict) -> Iterator[str]:
        for name, f in spec["fields"].items():
            if f["type"] == "text" and body.get(name) is not None:
                yield from (body[name] if isinstance(body[name], list) else [body[name]])
        for name, cs in spec["collections"].items():
            for it in body.get(name) or []:
                yield from self._prose(cs, it)
        stack = list(body.get("sections") or [])
        while stack:
            s = stack.pop(0)
            yield from ([s["body"]] if s.get("body") else [])
            stack += s.get("sections") or []

    def history(self, id: str | None = None, role: str | None = None, execution: str | None = None,
                since: str | None = None) -> list[Entry]:
        r = self.s.get(f"{self.url}/api/log/{TEAM}/{self.db}", params={"count": -1})
        r.raise_for_status()
        moment = datetime.fromisoformat(since) if since else None
        if moment and moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone.utc)
        out = []
        for c in reversed(r.json()):
            try:
                m = json.loads(c.get("message", ""))
            except ValueError:
                continue
            if not isinstance(m, dict) or m.get("kb") != 1:
                continue
            at = datetime.fromtimestamp(c["timestamp"], timezone.utc)
            e = Entry(c["identifier"], at.isoformat(), c.get("author", ""), m["execution"], m["message"],
                      [tuple(x) for x in m["changes"]])
            if ((id is None or any(x[1] == id for x in e.changes)) and (role is None or e.role == role)
                    and (execution is None or e.execution == execution) and (moment is None or at >= moment)):
                out.append(e)
        return out

    def check(self) -> list[Fault]:
        kinds, docs = self._kinds(), self._all()
        known = {d["@id"] for d in docs} | {f"{d['@id']}#{p}" for d in docs for p in part_paths(decode(d)["content"])}
        faults = []
        for raw in docs:
            d = decode(raw)
            if d["kind"] not in kinds:
                faults.append(Fault("kind", d["id"], "", "its kind is gone"))
                continue
            faults += body_faults(kinds, resolve(kinds, d["kind"]), d["content"], d["id"], full=True, known=known)
        return faults

    # -- moving a corpus ---------------------------------------------------------------------------------------

    def export(self) -> Iterator[dict]:
        kinds = self._kinds()
        order = sorted(kinds, key=lambda k: (len(chain(kinds, k)), k))
        for k in order:
            yield {"kind": kinds[k]}
        for raw in sorted(self._all(), key=lambda d: d["@id"]):
            yield decode(raw)

    def import_(self, items: list[dict], sig: dict) -> None:
        kinds = [it["kind"] for it in items if "id" not in it]
        schema = self._schema()
        self._put_schema([c for k in kinds for c in classes_for(k, schema)], sig.get("role", ""),
                         sig.get("message", ""))
        docs = [it for it in items if "id" in it]
        self.commit([{"op": "create", "kind": d["kind"], "slug": d["id"].split("/", 1)[1], "title": d["title"],
                      "content": d["content"]} for d in docs], sig)


def open_store(name: str, workdir: Path) -> TerminusStore:
    return TerminusStore(name, server_url())
