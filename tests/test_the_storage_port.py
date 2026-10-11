"""Every storage adapter against the same cases of the port, each in a database of its own under its own tmp_path.
Kinds, shapes and composition stay above the port, so none of them is here."""
import dataclasses
import itertools
import threading
from datetime import datetime, timedelta, timezone

import pytest

import calls
import kb
from calls import TYPE_OF_TYPES, TYPES, TYPES_AT, iri, type_iri
from kb import client as kb_client
from kb import port, port_values, search, sqlite_store
from kb import store as stores
from kb.values import ArtifactId, Below, Kind, Version

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
    """The IRI the cases name an artifact by, `<kind>/<name>`, stands for: `schema/<kind>` a type's."""
    kind_name, _, slug = text.partition("/")
    return ArtifactId(iri(kind_name, slug))


def short(artifact_id):
    """An IRI as the cases name it."""
    under = str(artifact_id).removeprefix(TYPES_AT)
    return under if "/" in under else f"{TYPES}/{under}"


def kind(kind_name):
    """A kind as the port takes it, its type's IRI."""
    return Kind(type_iri(kind_name))


def kind_of(text):
    """The kind of the artifact the cases name."""
    return kind(text.partition("/")[0])


def put(text, content, read=0, links=(), parts=()):
    """A change landing content, with the rows it is found by as kb gives them."""
    searched = tuple(search.searchable(content))
    return port_values.Change(
        name(text), content, tuple(links), tuple(parts), read, read + 1, searched=searched, kind=kind_of(text),
    )


def removal(text, read):
    return port_values.Change(name(text), None, read=read, revision=read + 1)


def link(field, place, target, kinds, part="", under=None, waits=False, holder=""):
    """A link as kb hands it; `under` the held type kb says a target not held sits under, as the cases name it;
    `waits` whether kb says the store already held this very link, waiting; `holder` what kb says holds it."""
    return port_values.Link(field, place, name(target), part, tuple(type_iri(each) for each in kinds),
                     under=under and name(under), waits=waits, holder=holder)


def entry(entry_id, at=T0, seq=1, batch="", artifact="", role="tester", execution=""):
    record = {"id": entry_id, "at": at.isoformat(), "artifact": artifact}
    return port_values.Entry(entry_id, at, seq, record, artifact, role, execution, batch or entry_id)


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
    return [(short(each), store.artifact(each)) for each in store.ids()], store.history()


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
    assert [short(each) for each in store.ids()] == [
        "note/price-2", "note/price-b", "note/price", "note/pricea", "work/x", "work-item/y",
    ]
    assert [short(each) for each in store.ids(kind("work"))] == ["work/x"]


def test_a_set_lands_whole_or_not_at_all(store):
    with pytest.raises(port.Conflict):
        land(store, put("note/a", {"title": "A"}), put("note/b", {"title": "B"}, read=4))
    assert written(store) == ([], [])
    land(store, put("note/a", {"title": "A"}), put("note/b", {"title": "B"}))
    assert [short(each) for each in store.ids()] == ["note/a", "note/b"]


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
        land(store, put("note/a", {"title": "A"}), port_values.Change(name("note/b"), {"title": "B"}, through=through, kind=kind("note")))
    assert written(store) == before
    land(store, port_values.Change(name("note/b"), {"title": "B"}, revision=1, through=((name("schema/note"), 2),), kind=kind("note")))
    assert store.holds(name("note/b"))

def test_a_change_read_through_a_type_that_has_since_been_removed_is_refused_and_writes_nothing(store):
    """A removed type stands at no revision, so it differs from every revision it was read at."""
    land(store, put("schema/note", {"title": "Note"}), put("schema/tag", {"title": "Tag"}))
    land(store, removal("schema/tag", 1))
    before = written(store)
    with pytest.raises(port.Conflict):
        land(store, dataclasses.replace(put("note/a", {"title": "A"}), through=((name("schema/tag"), 1),)))
    assert written(store) == before


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


def test_a_block_holding_the_write_lock_keeps_its_sets_a_refused_one_taken_back_alone(opener, store):
    with store.exclusive():
        land(store, put("note/a", {"title": "A"}))
        with pytest.raises(port.Conflict):
            land(store, put("note/b", {"title": "B"}, read=3))
        land(store, put("note/c", {"title": "C"}))
    with opener() as other:
        assert [short(each) for each in other.ids()] == ["note/a", "note/c"]


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
        assert [short(each) for each in store.ids()] == ["note/a"]
    thread.join()
    assert [short(each) for each in store.ids()] == ["note/a", "note/b"]


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


def _a_removal_and_a_new_link_to_it(store):
    """A store holding a decision, its type and a note; the decision's removal, and the note linked to it anew, the
    link carrying the held type the decision's IRI sits under."""
    land(store, put("schema/decision", {"title": "Decision"}), put("decision/d", {"title": "D"}),
         put("note/n", {"title": "N"}))
    about = link("about", "about", "decision/d", ["decision"], under="schema/decision")
    return removal("decision/d", 1), put("note/n", {"title": "N", "about": "decision/d"}, read=1, links=[about])


def test_a_removal_landing_second_on_another_connection_is_refused_for_the_link_that_landed_first(opener, store):
    removing, linking = _a_removal_and_a_new_link_to_it(store)
    with opener() as one, opener() as other:
        land(one, linking)
        with pytest.raises(port.Linked) as refused:
            land(other, removing)
    assert refused.value.links == [port_values.Linking(name("note/n"), "about", "about", name("decision/d"), "")]
    assert store.holds(name("decision/d"))
    assert store.links_in(name("decision/d")) == refused.value.links


def test_a_link_landing_second_on_another_connection_lands_on_the_iri_the_removal_left_unheld(opener, store):
    removing, linking = _a_removal_and_a_new_link_to_it(store)
    with opener() as one, opener() as other:
        land(one, removing)
        land(other, linking)
    assert not store.holds(name("decision/d"))
    assert store.artifact(name("note/n")) == {"title": "N", "about": "decision/d"}
    assert store.links_in(name("decision/d")) == [
        port_values.Linking(name("note/n"), "about", "about", name("decision/d"), ""),
    ]


def test_a_removal_and_a_new_link_to_it_let_go_at_once_are_each_judged_against_what_the_other_left(opener, store):
    removing, linking = _a_removal_and_a_new_link_to_it(store)
    removed, linked = _race(opener, [removing], [linking])
    assert linked is None
    assert store.links_in(name("decision/d")) == [
        port_values.Linking(name("note/n"), "about", "about", name("decision/d"), ""),
    ]
    if store.holds(name("decision/d")):
        assert isinstance(removed, port.Linked)
    else:
        assert removed is None


def test_a_link_to_an_iri_not_held_and_a_create_at_that_iri_let_go_at_once_both_land(opener, store):
    land(store, put("schema/decision", {"title": "Decision"}))
    about = link("about", "about", "decision/d", ["decision"], under="schema/decision")
    outcomes = _race(opener, [put("note/n", {"title": "N"}, links=[about])], [put("decision/d", {"title": "D"})])
    assert outcomes == [None, None]
    assert store.links_in(name("decision/d")) == [
        port_values.Linking(name("note/n"), "about", "about", name("decision/d"), ""),
    ]
    with pytest.raises(port.Linked):
        land(store, removal("decision/d", 1))


def test_a_link_must_land_on_an_artifact_or_part_of_a_kind_it_allows(store):
    land(store, put("decision/d", {"title": "D"}, parts=["options/a"]))
    land(store, put("note/fine", {}, links=[link("about", "about", "decision/d", ["decision"], "options/a")]))
    for target, kinds, part in (("decision/d", ["work"], ""), ("decision/d", ["decision"], "options/b")):
        wrong = link("about", "about", target, kinds, part)
        with pytest.raises(port.Unlanded) as refused:
            land(store, put("note/wrong", {}, links=[wrong]))
        assert refused.value.links == [port_values.Linking(name("note/wrong"), "about", "about", name(target), part)]
    assert not store.holds(name("note/wrong"))


def test_a_link_to_an_iri_not_held_lands_when_it_carries_a_held_type_it_allows(store):
    land(store, put("schema/decision", {"title": "Decision"}))
    about = link("about", "about", "decision/gone", ["work", "decision"], under="schema/decision")
    land(store, put("note/fine", {"about": "decision/gone"}, links=[about]))
    assert store.artifact(name("note/fine")) == {"about": "decision/gone"}
    assert not store.holds(name("decision/gone"))
    assert store.links_in(name("decision/gone")) == [
        port_values.Linking(name("note/fine"), "about", "about", name("decision/gone"), ""),
    ]


@pytest.mark.parametrize("kinds, under", [
    (["decision"], None),
    (["work"], "schema/decision"),
    (["work"], "schema/work"),
    (["decision"], "decision/d"),
], ids=["carrying none", "a held type it does not allow", "a type not held", "a held artifact it does not allow"])
def test_a_link_to_an_iri_not_held_is_refused_unless_the_type_it_carries_is_held_and_allowed(store, kinds, under):
    land(store, put("schema/decision", {"title": "Decision"}), put("decision/d", {"title": "D"}))
    before = written(store)
    wrong = link("about", "about", "decision/gone", kinds, under=under)
    with pytest.raises(port.Unlanded) as refused:
        land(store, put("note/wrong", {}, links=[wrong]))
    assert refused.value.links == [port_values.Linking(name("note/wrong"), "about", "about", name("decision/gone"), "")]
    assert written(store) == before


def test_a_link_to_a_held_artifact_is_checked_by_its_kind_whatever_type_the_link_carries(store):
    land(store, put("schema/decision", {"title": "Decision"}), put("schema/work", {"title": "Work"}),
         put("decision/d", {"title": "D"}, parts=["options/a"]))
    for kinds, part in ((["work"], ""), (["decision"], "options/b")):
        wrong = link("about", "about", "decision/d", kinds, part, under=f"schema/{kinds[0]}")
        with pytest.raises(port.Unlanded):
            land(store, put("note/wrong", {}, links=[wrong]))
    land(store, put("note/fine", {}, links=[link("about", "about", "decision/d", ["decision"], under="schema/work")]))


def test_an_artifact_whose_own_type_is_not_held_is_refused_whatever_its_implicit_link_carries(store):
    """No artifact lands under a type the store does not hold: the link to its type never lands on an IRI not held."""
    land(store, put("schema/schema", {"title": "Schema"}))
    before = written(store)
    of_its_type = dataclasses.replace(
        link("", "", "schema/note", ["schema"], under="schema/schema"), implicit=True,
    )
    with pytest.raises(port.Unlanded) as refused:
        land(store, put("note/a", {"title": "A"}, links=[of_its_type]))
    assert refused.value.links == [port_values.Linking(name("note/a"), "", "", name("schema/note"), "")]
    assert written(store) == before
    with pytest.raises(port.Unlanded):
        land(store, put("note/a", {"title": "A"}, links=[dataclasses.replace(of_its_type, under=None)]))


def test_an_artifact_created_at_an_iri_a_link_already_names_is_what_the_link_lands_on_from_then(store):
    land(store, put("schema/decision", {"title": "Decision"}))
    about = link("about", "about", "decision/later", ["decision"], under="schema/decision")
    land(store, put("note/n", {"about": "decision/later"}, links=[about]))
    assert store.ids(kind("decision")) == []
    land(store, put("decision/later", {"title": "Later"}))
    into = [port_values.Linking(name("note/n"), "about", "about", name("decision/later"), "")]
    assert store.links_in(name("decision/later")) == into
    assert store.inbound(name("decision/later")) == {(type_iri("note"), "about"): 1}
    with pytest.raises(port.Linked) as refused:
        land(store, removal("decision/later", 1))
    assert refused.value.links == into


def test_a_link_to_an_iri_not_held_is_refused_once_the_type_it_carries_has_been_removed(opener, store):
    land(store, put("schema/decision", {"title": "Decision"}))
    about = link("about", "about", "decision/gone", ["decision"], under="schema/decision")
    with opener() as one, opener() as other:
        land(one, removal("schema/decision", 1))
        with pytest.raises(port.Unlanded):
            land(other, put("note/n", {"about": "decision/gone"}, links=[about]))
    assert store.ids() == []


def test_the_port_lands_the_removal_of_a_type_a_link_waits_under_which_kb_refuses_before_it_hands_the_set(store):
    """The port keeps nothing of the type a waiting link was handed under and knows nothing of which IRIs sit under
    which, so it lands what it is handed; kb refuses such a removal as it drafts it, holding the write lock
    (tests/test_a_type_removed_while_a_link_waits_under_it.py). The link still reads as waiting."""
    land(store, put("schema/decision", {"title": "Decision"}))
    about = link("about", "about", "decision/later", ["decision"], under="schema/decision")
    land(store, put("note/n", {"about": "decision/later"}, links=[about]))
    land(store, removal("schema/decision", 1))
    assert not store.holds(name("schema/decision"))
    assert store.waiting() == [port_values.Linking(name("note/n"), "about", "about", name("decision/later"), "")]


def test_two_new_artifacts_in_one_set_that_link_each_other_land(store):
    land(store,
         put("note/a", {"to": "note/b"}, links=[link("to", "to", "note/b", ["note"])]),
         put("note/b", {"to": "note/a"}, links=[link("to", "to", "note/a", ["note"])]))
    assert [short(each.source) for each in store.links_in(name("note/a"))] == ["note/b"]


def test_removing_an_artifact_something_outside_the_set_links_into_is_refused_naming_each_link(store):
    land(store, put("decision/d", {}, parts=["options/a"]))
    land(store,
         put("note/one", {}, links=[link("about", "about", "decision/d", ["decision"])]),
         put("note/two", {}, links=[link("uses", "steps/0/uses", "decision/d", ["decision"], "options/a")]))
    with pytest.raises(port.Linked) as refused:
        land(store, removal("decision/d", 1))
    assert refused.value.links == [
        port_values.Linking(name("note/one"), "about", "about", name("decision/d"), ""),
        port_values.Linking(name("note/two"), "uses", "steps/0/uses", name("decision/d"), "options/a"),
    ]
    land(store, removal("note/one", 1), removal("note/two", 1), removal("decision/d", 1))
    assert store.ids() == []


def test_a_replacement_dropping_a_part_something_links_into_is_refused(store):
    land(store, put("decision/d", {}, parts=["options/a", "options/b"]))
    land(store, put("note/n", {}, links=[link("uses", "uses", "decision/d", ["decision"], "options/a")]))
    with pytest.raises(port.Linked) as refused:
        land(store, put("decision/d", {"v": 2}, read=1, parts=["options/b"]))
    assert refused.value.links == [port_values.Linking(name("note/n"), "uses", "uses", name("decision/d"), "options/a")]
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
    note = kind("note")
    assert [short(each) for each in store.ids(note, {"n": "123456789012345678901234567890"})] == ["note/a"]
    assert [short(each) for each in store.ids(note, {"flag": "true"})] == ["note/a"]
    assert [short(each) for each in store.ids(note, {"count": "3"})] == ["note/a", "note/b"]
    assert [short(each) for each in store.ids(note, {"count": "3", "on": "2026-10-01"})] == ["note/a"]
    assert store.ids(note, {"absent": ""}) == []


def below(text):
    """A path below a type as the port takes it, written as its segments joined by slashes."""
    return Below(tuple(text.split("/")))


def test_names_by_a_path_below_the_type_are_matched_by_whole_segments_across_every_kind(store):
    """No case escapes a `%` or a `_` in a segment: kb's grammar gives a segment neither, so none can arise."""
    for text in ("note/plan", "note/plan/a", "note/plan/a/b", "note/planning", "note/plan-b", "note/plan.b",
                 "note/old/plan", "work/plan", "work/plan/a", "work/plans/a"):
        land(store, put(text, {"title": text}))
    assert [short(each) for each in store.ids(path=below("plan"))] == [
        "note/plan/a/b", "note/plan/a", "note/plan", "work/plan/a", "work/plan",
    ]
    assert [short(each) for each in store.ids(path=below("plan/a"))] == ["note/plan/a/b", "note/plan/a", "work/plan/a"]
    assert [short(each) for each in store.ids(path=below("plan/a/b"))] == ["note/plan/a/b"]
    assert [short(each) for each in store.ids(path=below("old"))] == ["note/old/plan"]
    assert store.ids(path=below("pla")) == []
    assert store.ids(path=below("plan/a/b/c")) == []
    assert store.ids(path=below("a")) == []


def test_names_by_a_path_below_the_type_are_narrowed_by_a_kind_and_by_fields_when_those_are_given(store):
    land(store,
         put("note/plan/a", {"count": 3}), put("note/plan/b", {"count": 4}), put("note/other", {"count": 3}),
         put("work/plan/a", {"count": 3}))
    assert [short(each) for each in store.ids(kind("note"), path=below("plan"))] == ["note/plan/a", "note/plan/b"]
    assert [short(each) for each in store.ids(kind("note"), {"count": "3"}, below("plan"))] == ["note/plan/a"]
    assert [short(each) for each in store.ids(None, {"count": "3"}, below("plan"))] == ["note/plan/a", "work/plan/a"]
    assert store.ids(kind("tag"), path=below("plan")) == []


def test_a_path_below_the_type_is_read_below_the_kind_each_artifact_was_landed_with(store):
    """A type whose IRI sits under another's: what is of its kind has its path below it, not below the other."""
    nested = dataclasses.replace(put("note/sub/plan", {"title": "nested"}), kind=kind("note/sub"))
    land(store, nested, put("note/plan", {"title": "plain"}))
    assert [short(each) for each in store.ids(path=below("plan"))] == ["note/plan", "note/sub/plan"]
    assert store.ids(path=below("sub")) == []
    assert [short(each) for each in store.ids(kind("note/sub"), path=below("plan"))] == ["note/sub/plan"]


def test_names_by_a_path_alone_leave_out_what_is_of_the_kind_of_types(store):
    """A type is of the kind of types, and one may sit under the IRI of the type that describes types."""
    a_type = ArtifactId(f"{TYPE_OF_TYPES}/plan")
    land(store, dataclasses.replace(put("schema/plan", {"title": "a type"}), artifact=a_type),
         put("note/plan", {"title": "a note"}))
    assert [short(each) for each in store.ids(path=below("plan"))] == ["note/plan"]
    assert store.ids(kind("schema"), path=below("plan")) == [a_type]
    assert a_type in store.ids()


def test_links_in_narrowed_by_field_and_source_kind_into_parts_too(store):
    land(store, put("decision/d", {}, parts=["options/a"]))
    land(store,
         put("work/w", {}, links=[link("uses", "uses", "decision/d", ["decision"], "options/a")]),
         put("note/n", {}, links=[link("about", "about", "decision/d", ["decision"])]))
    into = name("decision/d")
    assert store.links_in(into) == [
        port_values.Linking(name("note/n"), "about", "about", into, ""),
        port_values.Linking(name("work/w"), "uses", "uses", into, "options/a"),
    ]
    assert [short(each.source) for each in store.links_in(into, field="uses")] == ["work/w"]
    assert [short(each.source) for each in store.links_in(into, kind=kind("note"))] == ["note/n"]


def test_the_links_landing_on_nothing_held_are_given_by_what_they_point_at_then_by_what_holds_them(store):
    land(store, put("schema/decision", {"title": "Decision"}), put("decision/held", {}, parts=["options/a"]))
    to = lambda field, place, target, part="": link(field, place, target, ["decision"], part, under="schema/decision")
    assert store.waiting() == []
    land(store,
         put("work/w", {}, links=[to("uses", "uses/0", "decision/b"), to("uses", "uses/1", "decision/held"),
                                  to("uses", "uses/2", "decision/a"), to("uses", "uses/3", "decision/b")]),
         put("note/n", {}, links=[to("about", "about", "decision/b"), to("into", "into", "decision/held", "options/a"),
                                  to("into", "into/1", "decision/b", "options/x")]))
    assert store.waiting() == [
        port_values.Linking(name("work/w"), "uses", "uses/2", name("decision/a"), ""),
        port_values.Linking(name("note/n"), "about", "about", name("decision/b"), ""),
        port_values.Linking(name("note/n"), "into", "into/1", name("decision/b"), "options/x"),
        port_values.Linking(name("work/w"), "uses", "uses/0", name("decision/b"), ""),
        port_values.Linking(name("work/w"), "uses", "uses/3", name("decision/b"), ""),
    ]


def test_a_link_into_a_part_of_an_iri_not_held_still_waits_when_what_is_created_there_lacks_the_part(store):
    land(store, put("schema/decision", {"title": "Decision"}))
    to = lambda place, part: link("into", place, "decision/later", ["decision"], part, under="schema/decision")
    land(store, put("note/n", {}, links=[to("into/0", "options/a"), to("into/1", "options/b"), to("into/2", "")]))
    assert [(each.place, each.part) for each in store.waiting()] == [
        ("into/0", "options/a"), ("into/1", "options/b"), ("into/2", ""),
    ]
    land(store, put("decision/later", {}, parts=["options/b"]))
    assert store.waiting() == [port_values.Linking(name("note/n"), "into", "into/0", name("decision/later"), "options/a")]


def test_the_links_landing_on_nothing_held_are_given_for_one_artifact_when_it_is_named(store):
    land(store, put("schema/decision", {"title": "Decision"}), put("decision/held", {}, parts=["options/a"]))
    to = lambda place, target, part="": link("uses", place, target, ["decision"], part, under="schema/decision")
    land(store,
         put("work/w", {}, links=[to("uses/0", "decision/b"), to("uses/1", "decision/held", "options/a"),
                                  to("uses/2", "decision/a", "options/x")]),
         put("note/n", {}, links=[to("uses", "decision/b")]))
    assert store.waiting(name("work/w")) == [
        port_values.Linking(name("work/w"), "uses", "uses/2", name("decision/a"), "options/x"),
        port_values.Linking(name("work/w"), "uses", "uses/0", name("decision/b"), ""),
    ]
    assert store.waiting(name("note/n")) == [port_values.Linking(name("note/n"), "uses", "uses", name("decision/b"), "")]
    assert store.waiting(name("decision/held")) == []
    assert store.waiting(name("decision/nowhere")) == []


def _a_note_waiting_on_an_option_its_decision_was_created_without(store):
    """A store holding a note whose link into option `a` of a decision landed while the decision was not held, and
    the decision, created since with option `b` only. Returns that link as kb hands it again, saying it waits."""
    land(store, put("schema/decision", {"title": "Decision"}))
    into = link("into", "into", "decision/d", ["decision"], "options/a", under="schema/decision")
    land(store, put("note/n", {"title": "N"}, links=[into]))
    land(store, put("decision/d", {"title": "D"}, parts=["options/b"]), put("decision/e", {"title": "E"}))
    return dataclasses.replace(into, waits=True)


WAITING = port_values.Linking(name("note/n"), "into", "into", name("decision/d"), "options/a")


def test_a_link_into_a_part_its_held_target_lacks_lands_again_when_it_says_it_waits_and_the_artifact_held_it(store):
    waits = _a_note_waiting_on_an_option_its_decision_was_created_without(store)
    land(store, put("note/n", {"title": "N, said again"}, read=1, links=[waits]))
    assert store.artifact(name("note/n")) == {"title": "N, said again"}
    assert store.waiting() == [WAITING]
    assert store.links_in(name("decision/d")) == [WAITING]
    land(store, put("note/n", {"title": "N, a third time"}, read=2, links=[waits]))
    assert store.waiting() == [WAITING]


@pytest.mark.parametrize("handed", [
    pytest.param(lambda waits: [dataclasses.replace(waits, waits=False)], id="not saying it waits"),
    pytest.param(lambda waits: [dataclasses.replace(waits, part="options/c")], id="into another part it lacks"),
    pytest.param(lambda waits: [dataclasses.replace(waits, holder="steps/one")], id="held by another thing"),
    pytest.param(lambda waits: [dataclasses.replace(waits, holder=None)], id="held by nothing named"),
    pytest.param(lambda waits: [dataclasses.replace(waits, target=name("decision/e"))], id="to another held target"),
    pytest.param(lambda waits: [dataclasses.replace(waits, field="about", place="about")], id="in another field"),
    pytest.param(lambda waits: [waits, dataclasses.replace(waits, place="into/1")], id="a second beside the first"),
    pytest.param(lambda waits: [dataclasses.replace(waits, kinds=(type_iri("work"),))], id="of a kind it may not land on"),
])
def test_a_link_into_a_part_its_held_target_lacks_is_refused_unless_it_is_the_very_link_that_waits(store, handed):
    links = handed(_a_note_waiting_on_an_option_its_decision_was_created_without(store))
    before = written(store)
    with pytest.raises(port.Unlanded) as refused:
        land(store, put("note/n", {"title": "N, said again"}, read=1, links=links))
    wrong = links[-1]
    assert refused.value.links == [port_values.Linking(name("note/n"), wrong.field, wrong.place, wrong.target, wrong.part)]
    assert written(store) == before
    assert store.waiting() == [WAITING]


def test_a_link_saying_it_waits_is_refused_from_an_artifact_that_did_not_hold_it(store):
    waits = _a_note_waiting_on_an_option_its_decision_was_created_without(store)
    with pytest.raises(port.Unlanded) as refused:
        land(store, put("note/other", {"title": "Other"}, links=[waits]))
    assert refused.value.links == [port_values.Linking(name("note/other"), "into", "into", name("decision/d"), "options/a")]
    assert not store.holds(name("note/other"))


def test_a_link_saying_it_waits_is_refused_from_another_held_artifact_alone_or_beside_its_holder(store):
    waits = _a_note_waiting_on_an_option_its_decision_was_created_without(store)
    land(store, put("note/other", {"title": "Other"}))
    before = written(store)
    again = put("note/n", {"title": "N, said again"}, read=1, links=[waits])
    for changes in ([put("note/other", {"title": "Other"}, read=1, links=[waits])],
                    [again, put("note/other", {"title": "Other"}, read=1, links=[waits])],
                    [again, put("note/new", {"title": "New"}, links=[waits])]):
        with pytest.raises(port.Unlanded) as refused:
            land(store, *changes)
        assert refused.value.links == [dataclasses.replace(WAITING, source=changes[-1].artifact)]
        assert written(store) == before
        assert store.waiting() == [WAITING]


def test_a_link_that_waits_is_the_very_link_wherever_it_stands_in_what_holds_it_and_is_held_once(store):
    """Decision 14 of batch 35: the adapter tells the link by what kb says holds it, never by its place."""
    land(store, put("schema/decision", {"title": "Decision"}))
    into = link("into", "steps/1/into/1", "decision/d", ["decision"], "options/a", under="schema/decision",
                holder="steps/one")
    land(store, put("note/n", {"title": "N"}, links=[into]))
    land(store, put("decision/d", {"title": "D"}, parts=["options/b"]))
    held = port_values.Linking(name("note/n"), "into", "steps/1/into/1", name("decision/d"), "options/a", "steps/one")
    assert store.waiting() == store.waiting(name("note/n")) == store.links_in(name("decision/d")) == [held]
    moved = dataclasses.replace(into, place="steps/0/into/0", waits=True)
    land(store, put("note/n", {"title": "N, its steps reordered"}, read=1, links=[moved]))
    assert store.waiting() == [dataclasses.replace(held, place="steps/0/into/0")]
    for wrong in (dataclasses.replace(moved, place="steps/0/into/1"), dataclasses.replace(moved, holder="steps/two"),
                  dataclasses.replace(moved, holder="")):
        with pytest.raises(port.Unlanded) as refused:
            land(store, put("note/n", {"title": "N"}, read=2, links=[moved, wrong]))
        assert [(each.place, each.part) for each in refused.value.links] == [(wrong.place, "options/a")]
    assert store.waiting() == [dataclasses.replace(held, place="steps/0/into/0")]


def test_a_link_saying_it_waits_is_refused_when_the_artifact_held_it_landing_and_its_set_drops_the_part(store):
    land(store, put("decision/d", {"title": "D"}, parts=["options/a"]))
    into = link("into", "into", "decision/d", ["decision"], "options/a")
    land(store, put("note/n", {"title": "N"}, links=[into]))
    with pytest.raises(port.Unlanded) as refused:
        land(store, put("decision/d", {"title": "D"}, read=1),
             put("note/n", {"title": "N"}, read=1, links=[dataclasses.replace(into, waits=True)]))
    assert refused.value.links == [WAITING]
    assert store.waiting() == []


def test_a_link_drafted_while_its_target_was_not_held_lands_after_a_create_there_without_its_part(opener, store):
    land(store, put("schema/decision", {"title": "Decision"}))
    into = link("into", "into", "decision/d", ["decision"], "options/a", under="schema/decision")
    land(store, put("note/n", {"title": "N"}, links=[into]))
    with opener() as one, opener() as other:
        land(one, put("decision/d", {"title": "D"}, parts=["options/b"]))
        land(other, put("note/n", {"title": "N, said again"}, read=1, links=[dataclasses.replace(into, waits=True)]))
    assert store.artifact(name("note/n")) == {"title": "N, said again"}
    assert store.waiting() == [WAITING]


def test_a_link_saying_it_waits_lands_on_the_part_once_its_target_has_gained_it(opener, store):
    waits = _a_note_waiting_on_an_option_its_decision_was_created_without(store)
    with opener() as one, opener() as other:
        land(one, put("decision/d", {"title": "D"}, read=1, parts=["options/a", "options/b"]))
        land(other, put("note/n", {"title": "N, said again"}, read=1, links=[waits]))
    assert store.waiting() == []
    with pytest.raises(port.Linked):
        land(store, put("decision/d", {"title": "D"}, read=2, parts=["options/b"]))


def test_a_link_saying_it_waits_whose_target_is_still_not_held_lands_by_the_type_it_carries(store):
    land(store, put("schema/decision", {"title": "Decision"}))
    into = link("into", "into", "decision/d", ["decision"], "options/a", under="schema/decision")
    land(store, put("note/n", {"title": "N"}, links=[into]))
    land(store, put("note/n", {"title": "N, said again"}, read=1, links=[dataclasses.replace(into, waits=True)]))
    assert store.waiting() == [WAITING]
    with pytest.raises(port.Unlanded):
        land(store, put("note/n", {"title": "N"}, read=2, links=[dataclasses.replace(into, waits=True, under=None)]))


def test_a_link_stops_waiting_when_the_artifact_holding_it_drops_it_or_is_removed(store):
    land(store, put("schema/decision", {"title": "Decision"}))
    about = link("about", "about", "decision/gone", ["decision"], under="schema/decision")
    land(store, put("note/one", {}, links=[about]), put("note/two", {}, links=[about]))
    land(store, put("note/one", {}, read=1), removal("note/two", 1))
    assert store.waiting() == []


def test_the_link_every_artifact_holds_to_its_type_never_waits(store):
    land(store, put("schema/schema", {"title": "Schema"}), put("schema/note", {"title": "Note"}))
    of_its_type = dataclasses.replace(link("", "", "schema/note", ["schema"]), implicit=True)
    land(store, put("note/a", {"title": "A"}, links=[of_its_type]))
    assert store.waiting() == []


def test_inbound_counts_by_source_kind_and_field_each_source_counted_once(store):
    land(store, put("decision/d", {}, parts=["options/a"]))
    about = lambda place, part="": link("about", place, "decision/d", ["decision"], part)
    land(store,
         put("note/one", {}, links=[about("about/0"), about("about/1", "options/a")]),
         put("note/two", {}, links=[about("about/0")]),
         put("work/w", {}, links=[link("uses", "uses", "decision/d", ["decision"])]))
    assert store.inbound(name("decision/d")) == {(type_iri("note"), "about"): 2, (type_iri("work"), "uses"): 1}


def test_search_candidates_per_section_and_per_field_keeping_the_section_title(store):
    land(store,
         put("note/a", {"title": "Prices", "summary": "Reviewed weekly", "sections": [
             {"title": "Purpose", "body": "Keep prices in step.\n",
              "sections": [{"title": "When", "body": "Weekly, on Mondays.\n"}]}]}),
         put("note/b", {"title": "Done✅", "body_note": "foo_bar"}),
         put("work/c", {"summary": "weekly too"}))
    weekly = search.terms("WEEKLY")
    assert store.search(weekly) == [
        port_values.Candidate(name("note/a"), "When", ""), port_values.Candidate(name("note/a"), "", "summary"),
        port_values.Candidate(name("work/c"), "", "summary"),
    ]
    assert store.search(weekly, kind=kind("note"), fields=False) == [port_values.Candidate(name("note/a"), "When", "")]
    assert store.search(weekly, sections=False, kind=kind("work")) == [port_values.Candidate(name("work/c"), "", "summary")]
    assert store.search(search.terms("done")) == [port_values.Candidate(name("note/b"), "", "title")]
    assert store.search(search.terms("foo_bar")) == [port_values.Candidate(name("note/b"), "", "body_note")]
    assert store.search(search.terms("foo")) == []



def test_search_finds_an_artifact_by_what_it_holds_now_and_nothing_once_it_is_removed(store):
    land(store, put("note/a", {"summary": "zebra"}))
    land(store, put("note/a", {"summary": "okapi"}, read=1))
    found = [port_values.Candidate(name("note/a"), "", "summary")]
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
    store.land([], [entry("late", at=later, artifact=str(name("note/a")), role="writer")])
    store.land([], [entry("first", seq=1, batch="pair", artifact=str(name("note/a")), execution="run-1"),
                    entry("second", seq=2, batch="pair", artifact=str(name("note/b")), execution="run-1")])
    store.land([], [entry("half", at=half, role="writer")])
    ids = lambda **filters: [record["id"] for record in store.history(**filters)]
    assert ids() == ["first", "second", "half", "late"]
    assert ids(artifact=name("note/a")) == ["late", "first"]  # one artifact's entries come in the order they landed
    assert ids(role="writer") == ["half", "late"]
    assert ids(execution="run-1") == ["first", "second"]
    assert ids(since=half) == ["half", "late"]
    assert ids(since=T0 + timedelta(milliseconds=1)) == ["half", "late"]
    assert ids(batch="pair") == ["first", "second"]
    assert sorted(store.entry_ids(T0)) == ["first", "second"]


def test_a_read_narrowed_to_one_artifact_keeps_landing_order_whatever_else_it_carries(store):
    store.land([], [entry("late", at=T0 + timedelta(hours=2), artifact=str(name("note/a")), role="writer")])
    store.land([], [entry("early", at=T0, artifact=str(name("note/a")), role="writer")])
    ids = lambda **filters: [record["id"] for record in store.history(artifact=name("note/a"), **filters)]
    assert ids(since=T0) == ["late", "early"]
    assert ids(role="writer") == ["late", "early"]


def test_the_entry_landed_last_is_the_last_by_landing_whatever_its_moment(store):
    assert store.landed_last() == ""
    store.land([], [entry("late", at=T0 + timedelta(hours=2))])
    assert store.landed_last() == "late"
    store.land([], [entry("first", seq=1, batch="pair"), entry("second", seq=2, batch="pair")])
    assert store.landed_last() == "second"  # stamped before "late", landed after it


def test_the_entry_landed_last_read_at_one_moment_is_that_moments(opener, store):
    store.land([], [entry("before")])
    with store.at_one_moment():
        assert store.landed_last() == "before"
        with opener() as other:
            other.land([], [entry("meanwhile")])
        assert store.landed_last() == "before"
    assert store.landed_last() == "meanwhile"


def test_an_entry_id_already_held_is_refused(store):
    store.land([put("note/a", {})], [entry("once")])
    before = written(store)
    with pytest.raises(port.Conflict):
        store.land([put("note/b", {})], [entry("once")])
    assert written(store) == before


def test_reads_at_one_moment_see_the_store_as_it_stood_whatever_lands_meanwhile(opener, store):
    land(store, put("note/a", {"title": "A"}))
    with store.at_one_moment():
        first = store.ids()
        with opener() as other:
            land(other, put("note/a", {"title": "A", "v": 2}, read=1), put("note/b", {"title": "B"}))
        assert (store.ids(), store.artifact(name("note/a"))) == (first, {"title": "A"})
    assert [short(each) for each in store.ids()] == ["note/a", "note/b"]


def test_reads_at_one_moment_inside_a_block_holding_the_write_lock_run_within_it(opener, store):
    with store.exclusive():
        land(store, put("note/a", {"title": "A"}))
        with store.at_one_moment():
            assert [short(each) for each in store.ids()] == ["note/a"]
        land(store, put("note/b", {"title": "B"}))
        with opener() as other:
            assert other.ids() == []
    with opener() as other:
        assert [short(each) for each in other.ids()] == ["note/a", "note/b"]


def test_a_block_holding_the_write_lock_is_never_opened_inside_reads_at_one_moment(store):
    land(store, put("note/a", {"title": "A"}))
    with store.at_one_moment():
        store.ids()
        with pytest.raises(RuntimeError):
            with store.exclusive():
                pass
        assert [short(each) for each in store.ids()] == ["note/a"]


def note_type(number, read=0, **content):
    """A change to the type of notes that leaves it standing at the version numbered, and that version."""
    version = Version(kind("note"), number)
    held = {"title": f"Note {number}", "version": number, **content}
    change = put("schema/note", held, read=read)
    return dataclasses.replace(change, version=port_values.Versioned(version, held["title"])), version


def test_a_type_version_reads_back_by_its_iri_with_the_content_revision_and_title_it_was_made_with(store):
    made, first = note_type(1, schema={"n": 123456789012345678901234567890, 1: "a number for a key"})
    land(store, made)
    read = store.type_version(first)
    assert read == port_values.TypeVersion(first, made.content, 1, "Note 1")
    assert typed(read.content) == typed(made.content)
    with pytest.raises(KeyError):
        store.type_version(Version(kind("note"), 2))
    with pytest.raises(KeyError):
        store.type_version(Version(kind("tag"), 1))


def test_ids_do_not_list_type_versions_and_a_version_is_not_held_as_an_artifact(store):
    made, first = note_type(1)
    land(store, made, put("note/a", {"title": "A"}))
    assert [short(each) for each in store.ids()] == ["note/a", "schema/note"]
    assert [short(each) for each in store.ids(kind("schema"))] == ["schema/note"]
    assert not store.holds(ArtifactId(str(first)))


def test_a_type_changed_stands_at_the_later_version_and_the_earlier_still_reads_as_it_was_made(store):
    made, first = note_type(1)
    land(store, made)
    changed, second = note_type(2, read=1)
    land(store, changed)
    assert store.type_version(second) == port_values.TypeVersion(second, changed.content, 2, "Note 2")
    assert store.artifact(name("schema/note")) == changed.content
    assert store.type_version(first) == port_values.TypeVersion(first, made.content, 1, "Note 1")


def test_a_type_version_lands_with_its_set_or_not_at_all(store):
    made, first = note_type(1)
    with pytest.raises(port.Conflict):
        land(store, made, put("note/b", {"title": "B"}, read=4))
    with pytest.raises(KeyError):
        store.type_version(first)


def test_a_type_version_is_read_at_the_moment_the_block_holds_and_still_reads_once_the_type_stands_at_a_later(
        opener, store):
    land(store, note_type(1)[0])
    first = Version(kind("note"), 1)
    changed, second = note_type(2, read=1)
    with store.at_one_moment():
        before = store.type_version(first)
        with opener() as other:
            land(other, changed)
        assert store.type_version(first) == before
    assert store.type_version(first) == before
    assert store.artifact(name("schema/note")) == changed.content
    assert store.type_version(second) == port_values.TypeVersion(second, changed.content, 2, "Note 2")


def test_the_type_that_describes_types_has_its_version_from_the_start_of_a_store(tmp_path):
    kb.init(tmp_path, "tester")
    with stores.opened(tmp_path) as started:
        held = started.artifact(ArtifactId(TYPE_OF_TYPES))
        read = started.type_version(Version(Kind(TYPE_OF_TYPES), 1))
        assert (read.content, read.revision, read.title) == (held, 1, "Schema")
        assert [str(each) for each in started.ids()] == [TYPE_OF_TYPES]


def test_a_type_defined_and_then_changed_through_kb_stands_at_the_later_version_and_the_earlier_still_reads(tmp_path):
    kb.init(tmp_path, "tester")
    client = kb_client.connect(tmp_path)
    calls.define(client, calls.NOTE_TYPE)
    note, first, second = ArtifactId(type_iri("note")), Version(kind("note"), 1), Version(kind("note"), 2)
    with stores.opened(tmp_path) as defined:
        made = port_values.TypeVersion(first, defined.artifact(note), 1, "Note")
        assert defined.type_version(first) == made
    changed = calls.replace_many(client, [calls.replaced(str(note), {"version": 2, "schema": calls.NOTE_TYPE["schema"]})])
    assert not changed.faults, changed.faults
    with stores.opened(tmp_path) as moved:
        assert moved.type_version(second) == port_values.TypeVersion(second, moved.artifact(note), 2, "Note")
        assert moved.type_version(first) == made
        assert [str(each) for each in moved.ids()] == [TYPE_OF_TYPES, str(note)]


def test_two_versions_of_a_type_landed_in_turn_both_read_back_as_each_was_made(store):
    made, first = note_type(1, schema={"n": 1})
    land(store, made)
    changed, second = note_type(2, read=1, schema={"n": 2, "more": [1.0, True]})
    land(store, changed)
    assert store.type_version(first) == port_values.TypeVersion(first, made.content, 1, "Note 1")
    assert store.type_version(second) == port_values.TypeVersion(second, changed.content, 2, "Note 2")
    assert typed(store.type_version(first).content) == typed(made.content)
    assert store.artifact(name("schema/note")) == changed.content
    with pytest.raises(KeyError):
        store.type_version(Version(kind("note"), 3))


def test_two_versions_of_a_type_landed_in_one_set_are_both_held(store):
    made, first = note_type(1)
    changed, second = note_type(2, read=1)
    land(store, made, changed)
    assert store.type_version(first) == port_values.TypeVersion(first, made.content, 1, "Note 1")
    assert store.type_version(second) == port_values.TypeVersion(second, changed.content, 2, "Note 2")


def test_ids_list_a_type_once_however_many_versions_of_it_are_held(store):
    land(store, note_type(1)[0], put("note/a", {"title": "A"}))
    land(store, note_type(2, read=1)[0])
    assert [short(each) for each in store.ids()] == ["note/a", "schema/note"]
    assert [short(each) for each in store.ids(kind("schema"))] == ["schema/note"]
    assert not any(store.holds(ArtifactId(str(Version(kind("note"), number)))) for number in (1, 2))


def test_a_set_refused_for_a_moved_revision_lands_no_version_and_leaves_the_earlier_as_it_was_made(store):
    made, first = note_type(1)
    land(store, made, put("note/a", {"title": "A"}))
    before = written(store), store.type_version(first)
    with pytest.raises(port.Conflict):
        land(store, note_type(2, read=1)[0], put("note/a", {"title": "A", "v": 2}, read=4))
    assert (written(store), store.type_version(first)) == before
    with pytest.raises(KeyError):
        store.type_version(Version(kind("note"), 2))


def test_a_set_refused_for_a_link_that_does_not_land_lands_no_version_and_leaves_the_earlier_as_it_was_made(store):
    made, first = note_type(1)
    land(store, made)
    before = written(store), store.type_version(first)
    astray = put("note/wrong", {}, links=[link("about", "about", "decision/gone", ["decision"])])
    with pytest.raises(port.Unlanded):
        land(store, note_type(2, read=1)[0], astray)
    assert (written(store), store.type_version(first)) == before
    with pytest.raises(KeyError):
        store.type_version(Version(kind("note"), 2))


def test_a_set_taken_back_inside_a_block_holding_the_write_lock_takes_its_version_back_alone(store):
    with store.exclusive():
        made, first = note_type(1)
        land(store, made)
        with pytest.raises(port.Conflict):
            land(store, note_type(2, read=1)[0], put("note/b", {"title": "B"}, read=4))
        kept, third = note_type(3, read=1)
        land(store, kept)
    assert store.type_version(first) == port_values.TypeVersion(first, made.content, 1, "Note 1")
    assert store.type_version(third) == port_values.TypeVersion(third, kept.content, 2, "Note 3")
    with pytest.raises(KeyError):
        store.type_version(Version(kind("note"), 2))


def test_a_type_removed_and_held_again_at_a_number_it_had_lands_with_the_version_it_is_then_made_with(store):
    land(store, note_type(1, schema={"n": 1})[0])
    land(store, removal("schema/note", 1))
    again, first = note_type(1, schema={"n": 2})
    land(store, again)
    assert store.artifact(name("schema/note")) == again.content
    assert store.type_version(first) == port_values.TypeVersion(first, again.content, 1, "Note 1")


def test_the_numbers_of_the_versions_held_of_a_type_are_given_lowest_first_and_none_once_it_is_removed(store):
    land(store, note_type(1)[0], put("schema/tag", {"title": "Tag"}))
    assert store.versions(name("schema/note")) == [1]
    land(store, note_type(2, read=1)[0], note_type(3, read=2)[0])
    assert store.versions(name("schema/note")) == [1, 2, 3]
    assert store.versions(name("schema/tag")) == []
    assert store.versions(name("schema/nothing")) == []
    with pytest.raises(port.Conflict):
        land(store, note_type(4, read=1)[0])
    assert store.versions(name("schema/note")) == [1, 2, 3]
    land(store, removal("schema/note", 3))
    assert store.versions(name("schema/note")) == []
    land(store, note_type(7)[0])
    assert store.versions(name("schema/note")) == [7]


def test_a_type_removed_has_none_of_its_versions_read_by_its_iri(store):
    land(store, note_type(1)[0], put("schema/tag", {"title": "Tag"}))
    land(store, note_type(2, read=1)[0])
    tag = dataclasses.replace(note_type(1)[0], artifact=name("schema/tag"), read=1, revision=2,
                              version=port_values.Versioned(Version(kind("tag"), 1), "Tag"))
    land(store, tag)
    land(store, removal("schema/note", 2))
    for number in (1, 2):
        with pytest.raises(KeyError):
            store.type_version(Version(kind("note"), number))
    assert store.type_version(Version(kind("tag"), 1)).title == "Tag"
    assert [short(each) for each in store.ids()] == ["schema/tag"]


def test_a_set_that_removes_a_type_and_is_refused_leaves_every_version_of_it_held(store):
    made, first = note_type(1)
    land(store, made, put("note/a", {"title": "A"}))
    changed, second = note_type(2, read=1)
    land(store, changed)
    before = written(store), store.type_version(first), store.type_version(second)
    with pytest.raises(port.Conflict):
        land(store, removal("schema/note", 2), put("note/a", {"title": "A", "v": 2}, read=4))
    assert (written(store), store.type_version(first), store.type_version(second)) == before
    assert before[1:] == (port_values.TypeVersion(first, made.content, 1, "Note 1"),
                          port_values.TypeVersion(second, changed.content, 2, "Note 2"))


def test_a_type_removed_inside_a_block_that_is_taken_back_keeps_every_version_of_it(opener, store):
    made, first = note_type(1)
    land(store, made)
    with pytest.raises(ZeroDivisionError):
        with store.exclusive():
            land(store, removal("schema/note", 1))
            with pytest.raises(KeyError):
                store.type_version(first)
            1 / 0
    with opener() as other:
        assert other.type_version(first) == port_values.TypeVersion(first, made.content, 1, "Note 1")


def test_a_type_defined_again_where_one_was_removed_stands_at_its_first_version_and_only_that_is_held(store):
    land(store, note_type(1, schema={"n": 1})[0])
    land(store, note_type(2, read=1, schema={"n": 2})[0])
    land(store, removal("schema/note", 2))
    again, first = note_type(1, schema={"n": 3})
    land(store, again)
    assert store.artifact(name("schema/note")) == again.content
    assert store.type_version(first) == port_values.TypeVersion(first, again.content, 1, "Note 1")
    with pytest.raises(KeyError):
        store.type_version(Version(kind("note"), 2))


def versions_as_files_give_them(*made):
    """Changes landing versions of the type of notes in one set, as an import hands them: each `(number, revision)`
    the version its file names at the revision its file gives, read at the revision the one before it left the type
    at, 0 for the first."""
    changes, read = [], 0
    for number, revision in made:
        change, version = note_type(number, read=read, schema={"n": number})
        changes.append((dataclasses.replace(change, revision=revision), version))
        read = revision
    return changes


def test_two_versions_of_a_type_landed_in_one_set_at_revisions_of_their_own_read_back_as_made_the_type_at_the_higher(
        store):
    (made, first), (changed, second) = versions_as_files_give_them((1, 3), (2, 7))
    land(store, made, changed)
    assert store.type_version(first) == port_values.TypeVersion(first, made.content, 3, "Note 1")
    assert store.type_version(second) == port_values.TypeVersion(second, changed.content, 7, "Note 2")
    assert store.versions(name("schema/note")) == [1, 2]
    assert store.artifact(name("schema/note")) == changed.content
    assert [short(each) for each in store.ids()] == ["schema/note"]
    land(store, note_type(3, read=7)[0])
    assert store.versions(name("schema/note")) == [1, 2, 3]


def test_a_set_landing_two_versions_of_a_type_and_an_artifact_linked_to_that_type_does_not_conflict_with_itself(store):
    land(store, dataclasses.replace(put("schema/tag", {"title": "Tag"}), version=port_values.Versioned(Version(kind("tag"), 1), "Tag")))
    (made, first), (changed, second) = versions_as_files_give_them((1, 1), (2, 2))
    of_its_type = dataclasses.replace(link("type", "", "schema/note", ["schema"]), implicit=True)
    note = dataclasses.replace(
        put("note/a", {"title": "A"}, links=[of_its_type]), through=((name("schema/tag"), 1),),
    )
    land(store, made, changed, note)
    assert store.versions(name("schema/note")) == [1, 2]
    assert store.type_version(first).content == made.content
    assert store.type_version(second).content == changed.content
    assert store.artifact(name("note/a")) == {"title": "A"}
    with pytest.raises(port.Linked):
        land(store, removal("schema/note", 2))


def test_a_set_landing_two_versions_of_a_type_that_is_refused_leaves_neither(store):
    before = written(store)
    (made, first), (changed, second) = versions_as_files_give_them((1, 1), (2, 2))
    with pytest.raises(port.Conflict):
        land(store, made, changed, put("note/b", {"title": "B"}, read=4))
    assert written(store) == before
    assert store.versions(name("schema/note")) == []
    for version in (first, second):
        with pytest.raises(KeyError):
            store.type_version(version)


def test_a_reader_holding_one_moment_sees_neither_of_two_versions_a_set_lands_meanwhile_and_then_both(opener, store):
    (made, first), (changed, second) = versions_as_files_give_them((1, 1), (2, 2))
    with store.at_one_moment():
        assert store.versions(name("schema/note")) == []
        with opener() as other:
            land(other, made, changed)
        assert store.versions(name("schema/note")) == []
        assert not store.holds(name("schema/note"))
    assert store.versions(name("schema/note")) == [1, 2]
    assert store.type_version(first).content == made.content
    assert store.artifact(name("schema/note")) == changed.content
