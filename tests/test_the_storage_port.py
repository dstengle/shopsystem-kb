"""Every storage adapter against the same cases of the port, each in a database of its own under its own tmp_path.
Kinds, shapes and composition stay above the port, so none of them is here."""
import itertools
import threading
from datetime import datetime, timedelta, timezone

import pytest

from kb import port, search, sqlite_store
from kb.values import Kind, artifact_id

ADAPTERS = {"sqlite": (sqlite_store.make, sqlite_store.opened)}

T0 = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)
_sets = itertools.count(1)


@pytest.fixture(params=sorted(ADAPTERS))
def opener(request, tmp_path):
    """Opens a new connection to one new database each time it is called."""
    make, opened = ADAPTERS[request.param]
    path = tmp_path / "store.sqlite3"
    make(path)
    return lambda: opened(path)


@pytest.fixture
def store(opener):
    with opener() as opened:
        yield opened


def name(text):
    return artifact_id(text)


def put(text, content, read=0, links=(), parts=()):
    """A change landing content, with the rows it is found by as kb gives them."""
    searched = tuple(search.searchable(content))
    return port.Change(name(text), content, tuple(links), tuple(parts), read, read + 1, searched=searched)


def removal(text, read):
    return port.Change(name(text), None, read=read, revision=read + 1)


def link(field, place, target, kinds, part=""):
    return port.Link(field, place, name(target), part, tuple(kinds))


def entry(entry_id, at=T0, seq=1, batch="", artifact="", role="tester", execution=""):
    record = {"id": entry_id, "at": at.isoformat(), "artifact": artifact}
    return port.Entry(entry_id, at, seq, record, artifact, role, execution, batch or entry_id)


def land(store, *changes, at=T0):
    """The changes landed as one set under one entry; the set's name."""
    number = next(_sets)
    batch = f"set-{number}"
    store.land(list(changes), [entry(batch, at=at, seq=number)])
    return batch


def typed(value):
    """A value with the type of every scalar in it, keys included, so 1, 1.0 and True stay apart."""
    if isinstance(value, dict):
        return [("dict", typed(key), typed(item)) for key, item in value.items()]
    if isinstance(value, list):
        return ["list", *(typed(item) for item in value)]
    return type(value).__name__, repr(value)


def written(store):
    """Everything the store holds that a refused set could have touched."""
    return [(str(each), store.artifact(each)) for each in store.ids()], store.history()


def test_a_new_database_holds_nothing_and_a_landed_create_reads_back_equal(store):
    assert (store.ids(), store.history()) == ([], [])
    content = {
        "id": "note/a", "title": "A", "n": 123456789012345678901234567890, "x": float("inf"), "d": "2026-10-01",
        "f": 1.5, "flag": True, 1: "a number for a key", None: "nothing for a key", 2.5: "a float for a key",
        "nested": {"~pairs": [[1, 2]], "deeper": [{"k": None, 3: [False]}]}, "only": {"~pairs": [[1, 2]]},
    }
    land(store, put("note/a", content))
    assert typed(store.artifact(name("note/a"))) == typed(content)


def test_holds(store):
    land(store, put("note/a", {"title": "A"}))
    assert store.holds(name("note/a")) and not store.holds(name("note/b"))
    land(store, removal("note/a", 1))
    assert not store.holds(name("note/a"))


def test_names_come_back_in_one_order(store):
    for text in ("work-item/y", "note/pricea", "note/price", "work/x", "note/price-b", "note/price-2"):
        land(store, put(text, {"title": text}))
    assert [str(each) for each in store.ids()] == [
        "note/price-2", "note/price-b", "note/price", "note/pricea", "work/x", "work-item/y",
    ]
    assert [str(each) for each in store.ids(Kind("work"))] == ["work/x"]


def test_a_set_lands_whole_or_not_at_all(store):
    with pytest.raises(port.Conflict):
        land(store, put("note/a", {"title": "A"}), put("note/b", {"title": "B"}, read=4))
    assert written(store) == ([], [])
    land(store, put("note/a", {"title": "A"}), put("note/b", {"title": "B"}))
    assert [str(each) for each in store.ids()] == ["note/a", "note/b"]


def test_a_replacement_read_at_a_moved_revision_is_refused_and_writes_nothing(store):
    land(store, put("note/a", {"title": "A", "v": 1}))
    land(store, put("note/a", {"title": "A", "v": 2}, read=1))
    before = written(store)
    with pytest.raises(port.Conflict):
        land(store, put("note/a", {"title": "A", "v": 3}, read=1))
    assert written(store) == before



def test_a_change_read_through_a_type_that_has_since_moved_is_refused_and_writes_nothing(store):
    land(store, put("schema/note", {"title": "Note", "v": 1}), put("schema/tag", {"title": "Tag"}))
    land(store, put("schema/note", {"title": "Note", "v": 2}, read=1))
    before = written(store)
    through = ((name("schema/note"), 1), (name("schema/tag"), 1))
    with pytest.raises(port.Conflict):
        land(store, put("note/a", {"title": "A"}), port.Change(name("note/b"), {"title": "B"}, through=through))
    assert written(store) == before
    land(store, port.Change(name("note/b"), {"title": "B"}, revision=1, through=((name("schema/note"), 2),)))
    assert store.holds(name("note/b"))

def _race(opener, *sets):
    """Each set landed on a connection of its own, all let go at once; what each gave, None when it landed."""
    outcomes, ready = [None] * len(sets), threading.Barrier(len(sets))

    def run(index, changes):
        with opener() as own:
            ready.wait()
            try:
                own.land(changes, [entry(f"race-{index}", seq=index)])
            except port.Refusal as refusal:
                outcomes[index] = refusal

    threads = [threading.Thread(target=run, args=pair) for pair in enumerate(sets)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return outcomes


def test_an_artifact_of_a_kind_read_anew_that_the_set_does_not_restate_is_refused_and_writes_nothing(store):
    land(store, put("schema/note", {"v": 1}), put("note/a", {}), put("note/b", {}))
    before = written(store)
    restating_a = [port.Relink(name("note/a"), (), 1)]
    with pytest.raises(port.Conflict):
        store.land([put("schema/note", {"v": 2}, read=1)], [entry("short")], restating_a, (Kind("note"),))
    assert written(store) == before
    store.land([put("schema/note", {"v": 2}, read=1), put("note/c", {})], [entry("whole")],
               [*restating_a, port.Relink(name("note/b"), (), 1)], (Kind("note"),))
    assert store.artifact(name("schema/note")) == {"v": 2}


def test_a_block_holding_the_write_lock_keeps_its_sets_a_refused_one_taken_back_alone(opener, store):
    with store.exclusive():
        land(store, put("note/a", {"title": "A"}))
        with pytest.raises(port.Conflict):
            land(store, put("note/b", {"title": "B"}, read=3))
        land(store, put("note/c", {"title": "C"}))
    with opener() as other:
        assert [str(each) for each in other.ids()] == ["note/a", "note/c"]


def test_nothing_lands_from_another_connection_while_a_block_holds_the_write_lock(opener, store):
    landed = threading.Event()

    def other_lands():
        with opener() as other:
            land(other, put("note/b", {"title": "B"}))
        landed.set()

    with store.exclusive():
        land(store, put("note/a", {"title": "A"}))
        thread = threading.Thread(target=other_lands)
        thread.start()
        assert not landed.wait(0.3)
        assert [str(each) for each in store.ids()] == ["note/a"]
    thread.join()
    assert [str(each) for each in store.ids()] == ["note/a", "note/b"]


def test_a_block_that_raises_keeps_nothing_it_landed(opener, store):
    with pytest.raises(RuntimeError):
        with store.exclusive():
            land(store, put("note/a", {"title": "A"}))
            raise RuntimeError("the block gave up")
    assert written(store) == ([], [])


def test_two_writers_to_one_artifact_on_two_connections_the_second_is_refused(opener, store):
    land(store, put("note/a", {"title": "A"}))
    outcomes = _race(opener, [put("note/a", {"title": "A", "by": 1}, read=1)], [put("note/a", {"title": "A", "by": 2}, read=1)])
    assert sorted(type(outcome).__name__ for outcome in outcomes) == ["Conflict", "NoneType"]
    assert store.artifact(name("note/a"))["by"] == 1 + outcomes.index(None)


def test_a_removal_and_a_new_link_to_it_on_two_connections_never_both_land(opener, store):
    land(store, put("decision/d", {"title": "D"}), put("note/n", {"title": "N"}))
    linking = put("note/n", {"title": "N", "about": "decision/d"}, read=1,
                  links=[link("about", "about", "decision/d", ["decision"])])
    removing, adding = _race(opener, [removal("decision/d", 1)], [linking])
    assert (removing is None) != (adding is None)
    assert isinstance(removing or adding, port.Linked if removing else port.Unlanded)


def test_a_link_must_land_on_an_artifact_or_part_of_a_kind_it_allows(store):
    land(store, put("decision/d", {"title": "D"}, parts=["options/a"]))
    land(store, put("note/fine", {}, links=[link("about", "about", "decision/d", ["decision"], "options/a")]))
    for target, kinds, part in (("decision/d", ["work"], ""), ("decision/gone", ["decision"], ""),
                                ("decision/d", ["decision"], "options/b")):
        wrong = link("about", "about", target, kinds, part)
        with pytest.raises(port.Unlanded) as refused:
            land(store, put("note/wrong", {}, links=[wrong]))
        assert refused.value.links == [port.Linking(name("note/wrong"), "about", "about", name(target), part)]
    assert not store.holds(name("note/wrong"))


def test_two_new_artifacts_in_one_set_that_link_each_other_land(store):
    land(store,
         put("note/a", {"to": "note/b"}, links=[link("to", "to", "note/b", ["note"])]),
         put("note/b", {"to": "note/a"}, links=[link("to", "to", "note/a", ["note"])]))
    assert [str(each.source) for each in store.links_in(name("note/a"))] == ["note/b"]


def test_removing_an_artifact_something_outside_the_set_links_into_is_refused_naming_each_link(store):
    land(store, put("decision/d", {}, parts=["options/a"]))
    land(store,
         put("note/one", {}, links=[link("about", "about", "decision/d", ["decision"])]),
         put("note/two", {}, links=[link("uses", "steps/0/uses", "decision/d", ["decision"], "options/a")]))
    with pytest.raises(port.Linked) as refused:
        land(store, removal("decision/d", 1))
    assert refused.value.links == [
        port.Linking(name("note/one"), "about", "about", name("decision/d"), ""),
        port.Linking(name("note/two"), "uses", "steps/0/uses", name("decision/d"), "options/a"),
    ]
    land(store, removal("note/one", 1), removal("note/two", 1), removal("decision/d", 1))
    assert store.ids() == []


def test_a_replacement_dropping_a_part_something_links_into_is_refused(store):
    land(store, put("decision/d", {}, parts=["options/a", "options/b"]))
    land(store, put("note/n", {}, links=[link("uses", "uses", "decision/d", ["decision"], "options/a")]))
    with pytest.raises(port.Linked) as refused:
        land(store, put("decision/d", {"v": 2}, read=1, parts=["options/b"]))
    assert refused.value.links == [port.Linking(name("note/n"), "uses", "uses", name("decision/d"), "options/a")]
    land(store, put("decision/d", {"v": 2}, read=1, parts=["options/a"]))


def test_a_link_handed_as_the_implicit_type_link_blocks_the_types_removal(store):
    land(store, put("schema/note", {"title": "Note"}))
    land(store, put("note/a", {"title": "A"}, links=[link("type", "type", "schema/note", ["schema"])]))
    with pytest.raises(port.Linked):
        land(store, removal("schema/note", 1))
    land(store, removal("note/a", 1))
    land(store, removal("schema/note", 1))
    assert store.ids() == []


def test_a_removed_name_may_be_held_again(store):
    land(store, put("note/a", {"v": 1}))
    land(store, removal("note/a", 1))
    land(store, put("note/a", {"v": 2}))
    assert store.artifact(name("note/a")) == {"v": 2}


def test_names_by_kind_with_field_equality_on_the_text_form(store):
    land(store,
         put("note/a", {"n": 123456789012345678901234567890, "flag": True, "count": 3, "on": "2026-10-01"}),
         put("note/b", {"n": 1, "flag": False, "count": 3}),
         put("work/c", {"count": 3}))
    note = Kind("note")
    assert [str(each) for each in store.ids(note, {"n": "123456789012345678901234567890"})] == ["note/a"]
    assert [str(each) for each in store.ids(note, {"flag": "true"})] == ["note/a"]
    assert [str(each) for each in store.ids(note, {"count": "3"})] == ["note/a", "note/b"]
    assert [str(each) for each in store.ids(note, {"count": "3", "on": "2026-10-01"})] == ["note/a"]
    assert store.ids(note, {"absent": ""}) == []


def test_links_in_narrowed_by_field_and_source_kind_into_parts_too(store):
    land(store, put("decision/d", {}, parts=["options/a"]))
    land(store,
         put("work/w", {}, links=[link("uses", "uses", "decision/d", ["decision"], "options/a")]),
         put("note/n", {}, links=[link("about", "about", "decision/d", ["decision"])]))
    into = name("decision/d")
    assert store.links_in(into) == [
        port.Linking(name("note/n"), "about", "about", into, ""),
        port.Linking(name("work/w"), "uses", "uses", into, "options/a"),
    ]
    assert [str(each.source) for each in store.links_in(into, field="uses")] == ["work/w"]
    assert [str(each.source) for each in store.links_in(into, kind=Kind("note"))] == ["note/n"]


def test_inbound_counts_by_source_kind_and_field_each_source_counted_once(store):
    land(store, put("decision/d", {}, parts=["options/a"]))
    about = lambda place, part="": link("about", place, "decision/d", ["decision"], part)
    land(store,
         put("note/one", {}, links=[about("about/0"), about("about/1", "options/a")]),
         put("note/two", {}, links=[about("about/0")]),
         put("work/w", {}, links=[link("uses", "uses", "decision/d", ["decision"])]))
    assert store.inbound(name("decision/d")) == {("note", "about"): 2, ("work", "uses"): 1}


def test_search_candidates_per_section_and_per_field_keeping_the_section_title(store):
    land(store,
         put("note/a", {"title": "Prices", "summary": "Reviewed weekly", "sections": [
             {"title": "Purpose", "body": "Keep prices in step.\n",
              "sections": [{"title": "When", "body": "Weekly, on Mondays.\n"}]}]}),
         put("note/b", {"title": "Done✅", "body_note": "foo_bar"}),
         put("work/c", {"summary": "weekly too"}))
    weekly = search.terms("WEEKLY")
    assert store.search(weekly) == [
        port.Candidate(name("note/a"), "When", ""), port.Candidate(name("note/a"), "", "summary"),
        port.Candidate(name("work/c"), "", "summary"),
    ]
    assert store.search(weekly, kind=Kind("note"), fields=False) == [port.Candidate(name("note/a"), "When", "")]
    assert store.search(weekly, sections=False, kind=Kind("work")) == [port.Candidate(name("work/c"), "", "summary")]
    assert store.search(search.terms("done")) == [port.Candidate(name("note/b"), "", "title")]
    assert store.search(search.terms("foo_bar")) == [port.Candidate(name("note/b"), "", "body_note")]
    assert store.search(search.terms("foo")) == []



def test_search_finds_an_artifact_by_what_it_holds_now_and_nothing_once_it_is_removed(store):
    land(store, put("note/a", {"summary": "zebra"}))
    land(store, put("note/a", {"summary": "okapi"}, read=1))
    found = [port.Candidate(name("note/a"), "", "summary")]
    assert (store.search(search.terms("zebra")), store.search(search.terms("okapi"))) == ([], found)
    land(store, removal("note/a", read=2))
    assert (store.search(search.terms("zebra")), store.search(search.terms("okapi"))) == ([], [])


def test_an_artifact_changed_and_then_removed_leaves_no_row_matching_its_words(store):
    def held(word):
        return {"title": f"About {word}", "summary": word, "sections": [{"title": "One", "body": f"{word} again\n"}]}
    land(store, put("note/a", held("zebra")), put("note/b", held("okapi")))
    land(store, put("note/a", held("gnu"), read=1), put("note/c", held("lemur")))
    land(store, removal("note/a", read=2))
    found = {word: store.search(search.terms(word)) for word in ("zebra", "gnu", "okapi", "lemur")}
    assert (found["zebra"], found["gnu"]) == ([], [])
    assert [len(found["okapi"]), len(found["lemur"])] == [3, 3]


def test_history_filtered_by_artifact_role_piece_of_work_moment_and_set_oldest_first(store):
    later, half = T0 + timedelta(hours=2), T0 + timedelta(milliseconds=500)
    store.land([], [entry("late", at=later, artifact="note/a", role="writer")])
    store.land([], [entry("first", seq=1, batch="pair", artifact="note/a", execution="run-1"),
                    entry("second", seq=2, batch="pair", artifact="note/b", execution="run-1")])
    store.land([], [entry("half", at=half, role="writer")])
    ids = lambda **filters: [record["id"] for record in store.history(**filters)]
    assert ids() == ["first", "second", "half", "late"]
    assert ids(artifact=name("note/a")) == ["first", "late"]
    assert ids(role="writer") == ["half", "late"]
    assert ids(execution="run-1") == ["first", "second"]
    assert ids(since=half) == ["half", "late"]
    assert ids(since=T0 + timedelta(milliseconds=1)) == ["half", "late"]
    assert ids(batch="pair") == ["first", "second"]
    assert sorted(store.entry_ids(T0)) == ["first", "second"]


def test_an_entry_id_already_held_is_refused(store):
    store.land([put("note/a", {})], [entry("once")])
    before = written(store)
    with pytest.raises(port.Conflict):
        store.land([put("note/b", {})], [entry("once")])
    assert written(store) == before


def test_links_restated_without_a_new_revision_at_the_revision_read(store):
    land(store, put("tag/t", {}), put("note/n", {"about": "tag/t"}))
    store.land([], [entry("restated")], [port.Relink(name("note/n"), (link("about", "about", "tag/t", ["tag"]),), 1)])
    assert [str(each.source) for each in store.links_in(name("tag/t"))] == ["note/n"]
    with pytest.raises(port.Linked):
        land(store, removal("tag/t", 1))
    unlanded = port.Relink(name("note/n"), (link("about", "about", "tag/gone", ["tag"]),), 1)
    store.land([], [entry("dangling")], [unlanded])
    assert [str(each.source) for each in store.links_in(name("tag/gone"))] == ["note/n"]
    with pytest.raises(port.Conflict):
        store.land([], [entry("moved")], [port.Relink(name("note/n"), (), 2)])
    assert store.artifact(name("note/n")) == {"about": "tag/t"} and store.history(batch="moved") == []
    assert [str(each) for each in store.ids()] == ["note/n", "tag/t"]


def test_a_relink_read_through_a_type_that_has_since_moved_is_refused_and_writes_nothing(store):
    land(store, put("schema/note", {"v": 1}), put("tag/t", {}), put("note/n", {}))
    land(store, put("schema/note", {"v": 2}, read=1))
    before = written(store)
    moved = port.Relink(name("note/n"), (link("about", "about", "tag/t", ["tag"]),), 1, ((name("schema/note"), 1),))
    with pytest.raises(port.Conflict):
        store.land([], [entry("moved-type")], [moved])
    assert written(store) == before


def test_reads_at_one_moment_see_the_store_as_it_stood_whatever_lands_meanwhile(opener, store):
    land(store, put("note/a", {"title": "A"}))
    with store.at_one_moment():
        first = store.ids()
        with opener() as other:
            land(other, put("note/a", {"title": "A", "v": 2}, read=1), put("note/b", {"title": "B"}))
        assert (store.ids(), store.artifact(name("note/a"))) == (first, {"title": "A"})
    assert [str(each) for each in store.ids()] == ["note/a", "note/b"]
