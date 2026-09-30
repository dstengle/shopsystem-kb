"""THROWAWAY. One test per usage pattern (p01..p29) and per diagnosis hole (h1, h2, h5, h5b, h8), for every adapter.

Patterns kb keeps above the port (reading one section or node, adding an item, names from titles, filling in link
targets on a read, names-only listings) are not here: they need nothing of an adapter beyond what p05, p06, p13 and
p16 test."""
import threading
from datetime import datetime, timedelta, timezone

import pytest

from model import DECISION, SIG, TAG, create, plain, remove, replace, sections
from port import Refused


def one(store, change, sig=SIG, expect=None):
    return store.commit([change], sig, expect).results[0]


def decision(store, slug="use-yaml", title="Use YAML", **fields):
    return one(store, create("decision", slug, title, {"sections": sections(), **fields}))["id"]


def refused(rule, call, *args, **kwargs):
    with pytest.raises(Refused) as caught:
        call(*args, **kwargs)
    assert rule in caught.value.rules, caught.value.faults
    return caught.value


# Lifecycle, types

def test_p01_a_new_store_holds_nothing(opener):
    assert opener().kinds() == []


def test_p03_kinds_are_versioned_and_checked(opener):
    s = opener()
    s.define(TAG, SIG)
    assert "tag" in s.kinds()
    refused("version", s.define, {**TAG, "fields": {"colour": plain()}}, SIG)
    s.define({**TAG, "version": 2, "fields": {"colour": plain()}}, SIG)
    refused("kind", s.define, {**TAG, "name": "orphan", "base": "nothing"}, SIG)
    refused("kind", s.define, {**TAG, "name": "loop", "base": "loop"}, SIG)
    refused("kind", s.define, {**TAG, "name": "bad-link", "fields": {"to": {"type": "link", "targets": ["nothing"],
                                                                             "many": False, "parts": False,
                                                                             "required": False}}}, SIG)


# Documents

def test_p04_create_mints_the_id_and_numbers_a_clash(store):
    first = one(store, create("tag", "pricing", "Pricing", {}))
    second = one(store, create("tag", "pricing", "Pricing", {}))
    assert (first["id"], first["revision"]) == ("tag/pricing", 1)
    assert second["id"] == "tag/pricing-2"


def test_p05_read_gives_the_document_or_refuses(store):
    id = decision(store, owner="shopkeeper")
    got = store.read(id)
    assert (got["id"], got["kind"], got["title"], got["revision"]) == (id, "decision", "Use YAML", 1)
    assert got["content"]["owner"] == "shopkeeper"
    assert [s["title"] for s in got["content"]["sections"]] == ["Purpose", "Rationale"]
    refused("not-found", store.read, "decision/nothing")


def test_p06_replace_moves_the_revision_on(store):
    id = decision(store)
    result = one(store, replace(id, {"sections": sections(rationale="Changed."), "status": "accepted"}))
    assert result["revision"] == 2
    got = store.read(id)
    assert got["content"]["status"] == "accepted" and got["title"] == "Use YAML"


def test_p06_content_that_does_not_fit_is_refused(store):
    refused("shape", store.commit, [create("decision", "x", "X", {"sections": sections(), "colour": "red"})], SIG)
    refused("shape", store.commit, [create("decision", "x", "X", {"sections": sections()[:1]})], SIG)
    refused("shape", store.commit, [create("work-item", "x", "X", {"estimate": "lots"})], SIG)
    refused("kind", store.commit, [create("invoice", "x", "X", {})], SIG)
    extra = sections() + [{"title": "Notes", "body": "More.", "sections": []}]
    assert one(store, create("decision", "x", "X", {"sections": extra}))["revision"] == 1


def test_p08_remove_is_refused_while_linked(store):
    tag = one(store, create("tag", "pricing", "Pricing", {}))["id"]
    lone = one(store, create("tag", "lone", "Lone", {}))["id"]
    decision(store, tags=[tag])
    refused("linked", store.commit, [remove(tag)], SIG)
    one(store, remove(lone))
    refused("not-found", store.read, lone)
    refused("not-found", store.commit, [remove("tag/nothing")], SIG)


# Change sets

def test_p09_a_set_lands_whole_or_not_at_all(store):
    before = store.list("decision")
    refused("shape", store.commit, [
        create("decision", "good", "Good", {"sections": sections()}),
        create("decision", "bad", "Bad", {"sections": []}),
    ], SIG)
    assert store.list("decision") == before


def test_p10_new_documents_link_by_references_within_the_set(store):
    item = one(store, create("work-item", "reprice", "Reprice", {}))["id"]
    landed = store.commit([
        replace(item, {"decisions": [{"ref": "d"}]}),
        create("decision", "weekly", "Weekly reviews", {"sections": sections()}, key="d"),
    ], SIG)
    new = landed.results[1]["id"]
    assert store.read(item)["content"]["decisions"] == [new]


def test_p10_a_set_referring_to_a_key_never_captured_or_captured_twice_is_refused(store):
    refused("set", store.commit, [create("work-item", "x", "X", {"decisions": [{"ref": "nobody"}]})], SIG)
    refused("set", store.commit, [create("tag", "a", "A", {}, key="k"), create("tag", "b", "B", {}, key="k")], SIG)


def test_h8_two_new_documents_that_must_point_at_each_other(store):
    landed = store.commit([
        create("pair", "left", "Left", {"partner": {"ref": "r"}}, key="l"),
        create("pair", "right", "Right", {"partner": {"ref": "l"}}, key="r"),
    ], SIG)
    left, right = (r["id"] for r in landed.results)
    assert store.read(left)["content"]["partner"] == right
    assert store.read(right)["content"]["partner"] == left


def test_p11_an_expected_revision_that_moved_refuses_the_set(store):
    id = decision(store)
    one(store, replace(id, {"sections": sections(), "status": "a"}))
    refused("conflict", store.commit, [replace(id, {"sections": sections(), "status": "b"})], SIG, {id: 1})
    assert store.read(id)["content"]["status"] == "a"
    one(store, replace(id, {"sections": sections(), "status": "c"}), expect={id: 2})


def _race(first, second):
    """Both calls run at once; each result is its value or the Refused it raised."""
    out = {}

    def run(name, call):
        try:
            out[name] = call()
        except Refused as refusal:
            out[name] = refusal
    threads = [threading.Thread(target=run, args=("a", first)), threading.Thread(target=run, args=("b", second))]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return out["a"], out["b"]


def test_h5b_two_writers_to_one_document_never_lose_an_update(opener):
    a = opener("shared")
    for kind in (TAG, {**DECISION, "base": None, "fields": {"status": plain()}}):
        a.define(kind, SIG)
    b = opener("shared")
    id = a.commit([create("decision", "d", "D", {"sections": sections()})], SIG).results[0]["id"]
    for attempt in range(10):
        x, y = _race(lambda: a.commit([replace(id, {"sections": sections(), "status": f"a{attempt}"})], SIG),
                     lambda: b.commit([replace(id, {"sections": sections(), "status": f"b{attempt}"})], SIG))
        landed = [r for r in (x, y) if not isinstance(r, Refused)]
        for r in (x, y):
            if isinstance(r, Refused):
                assert "conflict" in r.rules, r.faults
        revisions = sorted(r.results[0]["revision"] for r in landed)
        assert len(set(revisions)) == len(revisions), "two writes claimed one revision: an update was lost"
        assert a.read(id)["revision"] == revisions[-1]


def test_h5_a_removal_and_a_new_link_to_it_never_both_land(opener):
    a = opener("shared")
    for kind in (TAG, {**DECISION, "base": None, "fields": {"tags": {"type": "link", "targets": ["tag"],
                                                                        "many": True, "parts": False,
                                                                        "required": False}}}):
        a.define(kind, SIG)
    b = opener("shared")
    for attempt in range(10):
        tag = a.commit([create("tag", f"t{attempt}", "T", {})], SIG).results[0]["id"]
        _race(lambda: a.commit([remove(tag)], SIG),
              lambda: b.commit([create("decision", f"d{attempt}", "D", {"sections": sections(), "tags": [tag]})],
                               SIG))
        assert a.check() == []


def test_p12_every_commit_records_who_for_what_and_why(store):
    sig = {"role": "agent", "execution": "run-7", "message": "Record the decision"}
    id = store.commit([create("decision", "d", "D", {"sections": sections()})], sig).results[0]["id"]
    entry = store.history(id=id)[-1]
    assert (entry.role, entry.execution, entry.message) == ("agent", "run-7", "Record the decision")
    assert entry.changes == [("create", id, 1)]


# Lookup

def test_p13_p14_list_by_kind_and_fields_including_derived_kinds(store):
    a = decision(store, "a", "A", status="accepted")
    b = decision(store, "b", "B", status="proposed")
    w = one(store, create("work-item", "w", "W", {"status": "accepted"}))["id"]
    assert store.list("decision") == [a, b]
    assert store.list("decision", {"status": "accepted"}) == [a]
    assert store.list("shop-artifact", {"status": "accepted"}) == sorted([a, w])
    refused("kind", store.list, "invoice")


# Links

@pytest.fixture
def graph(store):
    """tag/pricing <- decision/old <- decision/new <- work-item/w1, work-item/w2; note -> process step."""
    tag = one(store, create("tag", "pricing", "Pricing", {}))["id"]
    old = decision(store, "old", "Old", tags=[tag])
    new = decision(store, "new", "New", supersedes=old, tags=[tag])
    w1 = one(store, create("work-item", "w1", "W1", {"decisions": [new]}))["id"]
    w2 = one(store, create("work-item", "w2", "W2", {"decisions": [new, old]}))["id"]
    step = one(store, create("step", "count", "Count the till", {}))["id"]
    proc = one(store, create("process", "open", "Open the shop", {"steps": [
        {"id": "unlock", "title": "Unlock"}, {"id": "count", "title": "Count the till", "uses": step}]}))["id"]
    note = one(store, create("note", "watch", "Watch the till", {"about": f"{proc}#steps/count"}))["id"]
    return {"tag": tag, "old": old, "new": new, "w1": w1, "w2": w2, "step": step, "proc": proc, "note": note}


def test_p16_links_out_of_a_document_or_one_place_in_it(store, graph):
    out = store.links_out(graph["new"])
    assert {(l.field, l.target) for l in out} == {("supersedes", graph["old"]), ("tags", graph["tag"])}
    assert [l.target for l in store.links_out(graph["new"], field="tags")] == [graph["tag"]]
    assert [l.target for l in store.links_out(graph["proc"], place="steps/count")] == [graph["step"]]
    assert store.links_out(graph["proc"], place="steps/unlock") == []


def test_p17_p18_links_in_including_into_parts_narrowed(store, graph):
    assert {l.source for l in store.links_in(graph["new"])} == {graph["w1"], graph["w2"]}
    assert {l.source for l in store.links_in(graph["old"])} == {graph["new"], graph["w2"]}
    assert {l.source for l in store.links_in(graph["old"], field="supersedes")} == {graph["new"]}
    assert {l.source for l in store.links_in(graph["old"], kind="work-item")} == {graph["w2"]}
    into_part = store.links_in(graph["proc"])
    assert [(l.source, l.target) for l in into_part] == [(graph["note"], f"{graph['proc']}#steps/count")]


def test_p19_inbound_counts_by_kind_and_field(store, graph):
    assert store.inbound_counts(graph["old"]) == {("decision", "supersedes"): 1, ("work-item", "decisions"): 1}
    assert store.inbound_counts(graph["tag"]) == {("decision", "tags"): 2}


def test_p20_traversal_with_routes_ending_at_loops(store, graph):
    reached = store.traverse(graph["w1"], "out", 2)
    assert [(r.id, r.route) for r in reached] == [
        (graph["new"], [("decisions", graph["new"])]),
        (graph["old"], [("decisions", graph["new"]), ("supersedes", graph["old"])]),
        (graph["tag"], [("decisions", graph["new"]), ("tags", graph["tag"])]),
    ]
    inward = store.traverse(graph["old"], "in", 2, kind="work-item")
    assert [r.id for r in inward] == [graph["w2"]]
    loop = store.commit([create("pair", "a", "A", {"partner": {"ref": "b"}}, key="a"),
                         create("pair", "b", "B", {"partner": {"ref": "a"}}, key="b")], SIG)
    a, b = (r["id"] for r in loop.results)
    assert [r.id for r in store.traverse(a, "out", 5)] == [b]


# Search

def test_p23_search_ranks_by_the_words(store):
    once = decision(store, "once", "Once", status="x")
    store.commit([replace(once, {"sections": sections(rationale="Restocking matters.")})], SIG)
    twice = decision(store, "twice", "Twice")
    store.commit([replace(twice, {"sections": sections(purpose="Restocking.", rationale="Restocking again.")})], SIG)
    one(store, create("step", "restock", "Restock the shelves", {"body": "Restocking weekly."}))
    hits = store.search("restocking")
    assert hits[0].id == twice
    assert {h.id for h in hits} == {twice, once, "step/restock"}
    assert {h.id for h in store.search("restocking", kind="step")} == {"step/restock"}
    assert store.search("nonexistentword") == []


# History and past states

def test_p24_history_narrowed_by_document_role_work_and_moment(store):
    start = datetime.now(timezone.utc) - timedelta(seconds=1)
    id = store.commit([create("tag", "t", "T", {})], {"role": "keeper", "execution": "", "message": "one"}).results[0]["id"]
    store.commit([replace(id, {})], {"role": "agent", "execution": "run-1", "message": "two"})
    assert [e.message for e in store.history(id=id)] == ["one", "two"]
    assert [e.message for e in store.history(role="agent")] == ["two"]
    assert [e.message for e in store.history(execution="run-1")] == ["two"]
    assert "one" in [e.message for e in store.history(since=start.isoformat())]
    assert store.history(since=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()) == []


def test_p25_p26_reads_as_the_store_stood_at_a_commit(store):
    first = store.commit([create("tag", "t", "T", {})], SIG)
    id = first.results[0]["id"]
    store.commit([create("tag", "u", "U", {})], SIG)
    store.commit([remove(id)], SIG)
    assert store.read(id, at=first.commit)["revision"] == 1
    assert store.list("tag", at=first.commit) == [id]
    assert store.list("tag") == ["tag/u"]


# Integrity

def test_p27_links_must_land_on_the_right_kind(store):
    refused("ref", store.commit, [create("work-item", "x", "X", {"decisions": ["decision/nothing"]})], SIG)
    tag = one(store, create("tag", "t", "T", {}))["id"]
    refused("ref", store.commit, [create("work-item", "x", "X", {"decisions": [tag]})], SIG)
    refused("ref", store.commit, [create("work-item", "x", "X", {"tags": ["tag/t#steps/x"]})], SIG)


def test_h1_removing_a_part_something_links_into_is_refused(store, graph):
    refused("linked", store.commit, [replace(graph["proc"], {"steps": [{"id": "unlock", "title": "Unlock"}]})], SIG)
    assert store.check() == []


def test_h2_removing_a_kind_with_documents_is_refused(store, graph):
    refused("in-use", store.remove_kind, "note", SIG)
    refused("in-use", store.remove_kind, "shop-artifact", SIG)
    store.commit([remove(graph["note"])], SIG)
    store.remove_kind("note", SIG)
    assert "note" not in store.kinds()


def test_p28_check_reports_what_a_newer_kind_no_longer_accepts(store):
    decision(store)
    tightened = {**DECISION, "version": 2, "fields": {**DECISION["fields"], "approver": plain(required=True)}}
    store.define(tightened, SIG)
    assert {f.rule for f in store.check()} == {"shape"}


# Moving a corpus

def test_p29_export_then_import_gives_the_same_corpus(store, graph, opener):
    items = list(store.export())
    fresh = opener("copy")
    fresh.import_(items, SIG)
    docs = {d["id"]: d for d in items if "id" in d}
    for id, doc in docs.items():
        got = fresh.read(id)
        assert (got["kind"], got["title"], got["content"]) == (doc["kind"], doc["title"], doc["content"])
    assert {l.source for l in fresh.links_in(graph["old"])} == {graph["new"], graph["w2"]}
