import re

from pytest_bdd import given, parsers, scenario, then, when

from calls import CLIENT, DECISION_TYPE, create, define, read, request
import held
from kb import content, client as kb_client
from kb.contract import kb_pb2


@scenario("change-the-store.feature", "The client creates an artifact")
def test_the_client_creates_an_artifact():
    pass


@scenario("change-the-store.feature", "An artifact created without a title is refused")
def test_an_artifact_created_without_a_title_is_refused():
    pass


@scenario("check-a-change.feature", "An artifact missing a required section is refused")
def test_an_artifact_missing_a_required_section_is_refused():
    pass


@scenario("check-a-change.feature", "An artifact pointing at something that is not there is refused")
def test_an_artifact_pointing_at_something_that_is_not_there_is_refused():
    pass


@scenario("check-a-change.feature", "An artifact with several faults reports them all")
def test_an_artifact_with_several_faults_reports_them_all():
    pass


@scenario("check-a-change.feature", "Faults found by different rules all come back together")
def test_faults_found_by_different_rules_all_come_back_together():
    pass


@scenario("check-a-change.feature", "A section carrying anything besides its title, its body and its own sections is refused")
def test_a_section_carrying_anything_besides_its_title_its_body_and_its_own_sections_is_refused():
    pass


@scenario("check-a-change.feature", "A section with no title is refused")
def test_a_section_with_no_title_is_refused():
    pass


@scenario("check-a-change.feature", "A section with no body is refused")
def test_a_section_with_no_body_is_refused():
    pass


@scenario("check-a-change.feature", "A section whose body is empty is kept as it is")
def test_a_section_whose_body_is_empty_is_kept_as_it_is():
    pass


@scenario("hand-over-content.feature", "Content that settles what only the store settles is refused")
def test_content_that_settles_what_only_the_store_settles_is_refused():
    pass


@scenario("hand-over-content.feature", "Content carrying a title of its own is refused")
def test_content_carrying_a_title_of_its_own_is_refused():
    pass


@scenario("hand-over-content.feature", "Content telling the store how to build a value is refused")
def test_content_telling_the_store_how_to_build_a_value_is_refused():
    pass


@scenario("hand-over-content.feature", "Content holding more than one document is refused")
def test_content_holding_more_than_one_document_is_refused():
    pass


@scenario("hand-over-content.feature", "A value that reads as a switch or as a clock time is still the text that was written")
def test_a_value_that_reads_as_a_switch_or_as_a_clock_time_is_still_the_text_that_was_written():
    pass


@scenario("hand-over-content.feature", "Content that writes a value once and points back at it elsewhere is refused")
def test_content_that_writes_a_value_once_and_points_back_at_it_elsewhere_is_refused():
    pass


@scenario("hand-over-content.feature", "Content that opens by declaring the format it is written in is refused")
def test_content_that_opens_by_declaring_the_format_it_is_written_in_is_refused():
    pass


@scenario("hand-over-content.feature", "Content naming the same entry twice is refused")
def test_content_naming_the_same_entry_twice_is_refused():
    pass


@scenario("hand-over-content.feature", "Values written as a yes-or-no, as nothing and as a number keep those meanings")
def test_values_written_as_a_yes_or_no_as_nothing_and_as_a_number_keep_those_meanings():
    pass


@scenario("hand-over-content.feature", "Content the store cannot make sense of is refused")
def test_content_the_store_cannot_make_sense_of_is_refused():
    pass


@scenario("hand-over-content.feature", "A field written as a bare date is the text that was written")
def test_a_field_written_as_a_bare_date_is_the_text_that_was_written():
    pass


@scenario("hand-over-content.feature", "Prose the store could not write back in its one form is refused")
def test_prose_the_store_could_not_write_back_in_its_one_form_is_refused():
    pass


@scenario("name-artifacts-and-items.feature", "The name of a new artifact is made from its title, not asked for")
def test_the_name_of_a_new_artifact_is_made_from_its_title_not_asked_for():
    pass


@scenario("name-artifacts-and-items.feature", "A second artifact with a title already used gets a name of its own")
def test_a_second_artifact_with_a_title_already_used_gets_a_name_of_its_own():
    pass


@scenario("name-artifacts-and-items.feature", "Two parts with the same title are given names of their own")
def test_two_parts_with_the_same_title_are_given_names_of_their_own():
    pass


@scenario("name-artifacts-and-items.feature", "A title with capitals and punctuation gives a plain name")
def test_a_title_with_capitals_and_punctuation_gives_a_plain_name():
    pass


@scenario("name-artifacts-and-items.feature", "A title that leaves nothing to make a name from is refused")
def test_a_title_that_leaves_nothing_to_make_a_name_from_is_refused():
    pass


@scenario("name-artifacts-and-items.feature", "A title that reads as a date is still a title")
def test_a_title_that_reads_as_a_date_is_still_a_title():
    pass


@scenario("name-artifacts-and-items.feature", "A title that reads as yes is still a title")
def test_a_title_that_reads_as_yes_is_still_a_title():
    pass


@scenario("name-artifacts-and-items.feature", "A title given as a yes-or-no is still a title")
def test_a_title_given_as_a_yes_or_no_is_still_a_title():
    pass


@scenario("name-artifacts-and-items.feature", "A title given as a number is still a title")
def test_a_title_given_as_a_number_is_still_a_title():
    pass


@scenario("name-what-is-asked-for.feature", "A kind that is not a plain name is refused")
def test_a_kind_that_is_not_a_plain_name_is_refused():
    pass


@scenario("name-what-is-asked-for.feature", "A kind the store holds no type for is refused")
def test_a_kind_the_store_holds_no_type_for_is_refused():
    pass


SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly, so a monthly review lags them.\n"},
]
OPTIONS = [
    {"title": "Keep weekly", "body": "Review every Monday."},
    {"title": "Go monthly", "body": "Review on the first of the month."},
]


@given(
    "a store holding a decision type whose artifacts require a purpose then a rationale, "
    "may link to the decision they supersede, and may carry a collection of options",
    target_fixture="client",
)
def _store_with_decision_type(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    return client


@when(
    "the client creates a decision with a title, both required sections and two options, saying which role and why",
    target_fixture="created",
)
def _create_decision(client):
    return create(client, "decision", {
        "title": "Price reviews happen weekly",
        "sections": SECTIONS,
        "options": OPTIONS,
    }, message="Move price reviews to weekly")


@then("the client is given the name the artifact keeps for life and its first version")
def _given_name_and_first_version(created):
    assert created.id == "decision/price-reviews-happen-weekly"
    assert created.revision == 1


@then("the artifact records the version of the type it was checked against")
def _records_schema_version(client, created):
    assert read(client, created.id).schema_version == 1


@then("reading it back gives what was written, in the order the type declares")
def _read_back_in_declared_order(root, client, created):
    stubs = read(client, created.id).parts
    assert [(stub.collection, stub.id, stub.title) for stub in stubs] == [
        ("options", "keep-weekly", "Keep weekly"),
        ("options", "go-monthly", "Go monthly"),
    ]
    on_disk = held.artifact(root, "decision/price-reviews-happen-weekly")
    assert list(on_disk) == ["id", "type", "schema_version", "revision", "title", "sections", "options"]
    assert on_disk["sections"] == SECTIONS
    assert on_disk["options"] == [
        {"id": "keep-weekly", **OPTIONS[0]},
        {"id": "go-monthly", **OPTIONS[1]},
    ]


@when(
    "the client creates a decision whose content carries a title as well as the title given alongside it, "
    "saying which role and why",
    target_fixture="refused",
)
def _create_with_a_title_inside(client):
    return request(client, "decision", "Price reviews happen weekly", {
        "title": "Price reviews, weekly",
        "sections": SECTIONS,
    }, message="Move price reviews to weekly")


@then(
    "the artifact is rejected because a title is given alongside the content, never inside it, "
    "and the title the content carried is named back"
)
def _rejected_for_a_title_inside(refused):
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.path, fault.rule) for fault in refused.faults] == [("title", "identity")]
    assert "Price reviews, weekly" in refused.faults[0].message


@when(parsers.parse('the client creates a decision titled "{title}", saying which role and why'), target_fixture="created")
def _create_titled(client, title):
    return request(client, "decision", title, {"sections": SECTIONS}, message="Record it")


@then("the title reads back as the text that was written, not as a date")
def _title_is_text_not_a_date(root, client, created):
    assert read(client, created.id).title == "2026-09-24"
    on_disk = held.artifact(root, created.id)
    assert on_disk["title"] == "2026-09-24"


@then("the name the client is given is made from that text")
def _name_from_that_text(client, created):
    assert created.id == f"decision/{read(client, created.id).title}"


@when(
    "the client creates a decision with both required sections and no title, saying which role and why",
    target_fixture="refused",
)
def _create_without_a_title(client):
    return request(client, "decision", "", {"sections": SECTIONS}, message="Record it")


@then("the artifact is rejected because an artifact cannot be created without a title")
def _rejected_without_a_title(refused):
    assert [(fault.path, fault.rule, fault.message) for fault in refused.faults] == [
        ("title", "title", "an artifact cannot be created without a title"),
    ]


@when(
    "the client creates a decision whose content carries a name and a version for the artifact itself, "
    "saying which role and why",
    target_fixture="refused",
)
def _create_with_identity_inside(client):
    return request(client, "decision", "Price reviews happen weekly", {
        "id": "decision/a-name-of-my-own",
        "revision": 7,
        "sections": SECTIONS,
    }, message="Record it")


@then(
    "the artifact is rejected because content holds only what the type declares, "
    "and each thing it carried that only the store settles is named back"
)
def _rejected_for_identity_inside(refused):
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.path, fault.rule) for fault in refused.faults] == [("id", "identity"), ("revision", "identity")]
    assert all(fault.path in fault.message for fault in refused.faults)


@then(
    "the name the client is given is that title in lower case, with each run of anything that is not "
    "a letter or a digit turned into a single hyphen, and no hyphen at either end"
)
def _plain_name(created):
    assert not created.faults, created.faults
    assert created.id == "decision/price-reviews-weekly-from-now-on"


@then("the artifact is rejected because a title must leave something to make a name from")
def _rejected_for_an_empty_name(created):
    assert (created.id, created.revision) == ("", 0)
    assert [(fault.path, fault.rule) for fault in created.faults] == [("title", "title")]
    assert "leave something to make a name from" in created.faults[0].message


@then("the title reads back as the text that was written, not as a yes or a no")
def _title_is_text_not_a_bool(root, client, created):
    assert read(client, created.id).title == "yes"
    on_disk = held.artifact(root, created.id)
    assert on_disk["title"] == "yes"


def _raw(client, text):
    """A Create whose content is sent as written, so the text can carry what dumps never writes."""
    return client.Create(kb_pb2.CreateRequest(
        type="decision", title="Price reviews happen weekly", content=text, actor=CLIENT, message="Record it",
    ))


@when("the client creates a decision whose content carries a tag on one of its values, saying which role and why", target_fixture="refused")
def _create_with_a_tag(client):
    return _raw(client, "sections:\n  - title: Purpose\n    body: !!binary aGVsbG8=\n  - title: Rationale\n    body: Why.\n")


@then("the artifact is rejected because content is read plainly as written and carries no tags")
def _rejected_for_a_tag(refused):
    assert [(fault.rule, fault.message) for fault in refused.faults] == [
        ("content", "content is read plainly as written and carries no tags"),
    ]


@when(
    "the client creates a decision from content holding two documents one after the other, saying which role and why",
    target_fixture="refused",
)
def _create_from_two_documents(client):
    one = "sections:\n  - title: Purpose\n    body: Why.\n  - title: Rationale\n    body: Because.\n"
    return _raw(client, one + "---\n" + one)


@then("the artifact is rejected because content holds exactly one document")
def _rejected_for_two_documents(refused):
    assert [(fault.rule, fault.message) for fault in refused.faults] == [
        ("content", "content holds exactly one document"),
    ]


@when(
    "the client creates a decision whose purpose carries an extra entry of its own besides its title, its body "
    "and the sections inside it, saying which role and why",
    target_fixture="refused",
)
def _create_with_an_extra_entry_in_a_section(client):
    return request(client, "decision", "Price reviews happen weekly", {
        "sections": [{**SECTIONS[0], "author": "shopkeeper"}, SECTIONS[1]],
    }, message="Record it")


@then(
    "the artifact is rejected because a section holds exactly its title, its body and the sections inside it, "
    "and the extra entry is named"
)
def _rejected_for_an_extra_entry(refused):
    assert [(fault.path, fault.rule) for fault in refused.faults] == [("sections/0", "additionalProperties")]
    assert "'author'" in refused.faults[0].message


@when(
    'the client creates a decision carrying one field written "on" and another written "1:20", saying which role and why',
    target_fixture="created",
)
def _create_with_values_yaml_1_1_would_convert(client):
    return _raw(client, (
        "switch: on\n"
        "time: 1:20\n"
        "sections:\n"
        "  - title: Purpose\n    body: Why.\n"
        "  - title: Rationale\n    body: Because.\n"
    ))


@then(
    "both fields read back as the text that was written, the first not as a yes or a no "
    "and the second not as a number"
)
def _both_fields_are_text(root, created):
    assert not created.faults, created.faults
    on_disk = held.artifact(root, created.id)
    assert (on_disk["switch"], on_disk["time"]) == ("on", "1:20")


@when(
    "the client creates a decision whose content writes a value once and points back at it from another place "
    "instead of writing it again, saying which role and why",
    target_fixture="refused",
)
def _create_with_an_alias(client):
    return _raw(client, (
        "reviewed: &day Monday\n"
        "decided: *day\n"
        "sections:\n"
        "  - title: Purpose\n    body: Why.\n"
        "  - title: Rationale\n    body: Because.\n"
    ))


@then(
    "the artifact is rejected because content is read exactly as written and nothing in it stands in "
    "for a value written somewhere else"
)
def _rejected_for_an_alias(refused):
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.rule, fault.message) for fault in refused.faults] == [
        ("content", "content is read exactly as written and nothing in it stands in for a value written somewhere else"),
    ]


@when(
    "the client creates a decision whose first section carries a body and no title, saying which role and why",
    target_fixture="refused",
)
def _create_with_a_section_without_a_title(client):
    return request(client, "decision", "Price reviews happen weekly", {
        "sections": [{"body": SECTIONS[0]["body"]}, SECTIONS[1]],
    }, message="Record it")


@when(
    "the client creates a decision whose purpose carries a title and no body, saying which role and why",
    target_fixture="refused",
)
def _create_with_a_section_without_a_body(client):
    return request(client, "decision", "Price reviews happen weekly", {
        "sections": [{"title": "Purpose"}, SECTIONS[1]],
    }, message="Record it")


@then(
    "the artifact is rejected because a section carries both a title and a body, and a section without one "
    "does not fit its type like anything else that does not"
)
def _rejected_for_a_section_missing_a_key(refused):
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.path, fault.rule) for fault in refused.faults] == [("sections/0", "required")]


@when(
    parsers.parse(
        'the client creates an artifact of the kind "{kind}", with a title and both required sections, '
        "saying which role and why"
    ),
    target_fixture="attempt",
)
def _create_of_a_kind(client, tmp_path, kind):
    before = held.everything_in(tmp_path)
    response = request(client, kind, "Price reviews happen weekly", {"sections": SECTIONS}, message="Record it")
    return {"response": response, "before": before, "after": held.everything_in(tmp_path)}


@then("the artifact is rejected because a kind is a plain name of lower-case letters, digits and single hyphens, never a path")
def _rejected_as_not_a_plain_kind(attempt):
    refused = attempt["response"]
    assert (refused.id, refused.revision) == ("", 0)
    assert [fault.rule for fault in refused.faults] == ["kind"]
    assert "never a path" in refused.faults[0].message
    assert "../schema/decision" in refused.faults[0].message


@then("nothing is looked up or written anywhere, inside the store or outside it")
def _nothing_written_anywhere(attempt):
    assert attempt["after"] == attempt["before"]


@given("a title for a new decision that is the yes-or-no true rather than text", target_fixture="title")
def _a_title_that_is_a_yes_or_no():
    return True


@when("the client creates a decision with that title, saying which role and why", target_fixture="created")
def _create_with_that_title(client, title):
    return request(client, "decision", content.text(title), {"sections": SECTIONS}, message="Record it")


@then(parsers.parse('the title reads back as the text "{text}"'))
def _title_reads_back_as(root, client, created, text):
    assert not created.faults, created.faults
    assert read(client, created.id).title == text
    on_disk = held.artifact(root, created.id)
    assert on_disk["title"] == text


@given("content for a decision that names the same entry twice in the same place", target_fixture="written")
def _content_naming_an_entry_twice():
    return (
        "sections:\n"
        "  - title: Purpose\n"
        "    body: Keep prices in step with costs.\n"
        "    body: Keep prices low.\n"
        "  - title: Rationale\n"
        "    body: Because.\n"
    )


@when("the client creates a decision from that content, saying which role and why", target_fixture="created")
def _create_from_that_content(client, written):
    return _raw(client, written)


@then("the artifact is rejected because an entry is named once and only once, and the place the second one stands is named")
def _rejected_for_an_entry_named_twice(created):
    assert (created.id, created.revision) == ("", 0)
    assert [(fault.path, fault.rule) for fault in created.faults] == [("sections/0/body", "content")]
    assert created.faults[0].message.startswith("an entry is named once and only once")
    assert "line 4" in created.faults[0].message


@given(
    "content for a decision that opens with a line declaring which version of the writing format the rest is in",
    target_fixture="written",
)
def _content_opening_with_a_directive():
    return (
        "%YAML 1.1\n"
        "---\n"
        "switch: on\n"
        "sections:\n"
        "  - title: Purpose\n    body: Why.\n"
        "  - title: Rationale\n    body: Because.\n"
    )


@then(
    "the artifact is rejected because content is read plainly as written and opens with no declaration of its format, "
    "and the place the declaration stands is named"
)
def _rejected_for_a_directive(created):
    assert (created.id, created.revision) == ("", 0)
    assert [fault.rule for fault in created.faults] == ["content"]
    assert created.faults[0].message == (
        "content is read plainly as written and opens with no declaration of its format; "
        "line 1 declares %YAML 1.1"
    )


@given(parsers.parse('a store that holds no type called "{kind}"'))
def _no_type_called(client, kind):
    assert read(client, f"schema/{kind}").faults


@then("the artifact is rejected because a kind must name a type the store holds, and the kind asked for is given back")
def _rejected_as_an_unknown_kind(attempt):
    refused = attempt["response"]
    assert (refused.id, refused.revision) == ("", 0)
    assert refused.faults[0].rule == "kind"
    assert refused.faults[0].message == "a kind must name a type the store holds; the store holds no type called 'invoice'"


@then("that fault stands on its own, apart from anything wrong with the content")
def _the_kind_fault_alone(attempt):
    assert [(fault.path, fault.rule) for fault in attempt["response"].faults] == [("", "kind")]


@then("nothing is written anywhere in the store")
def _nothing_written_in_the_store(attempt):
    assert attempt["after"] == attempt["before"]


@given(
    'content for a decision carrying one field written "true", one field left as nothing, and one field written "12.5"',
    target_fixture="written",
)
def _content_with_typed_values():
    return (
        "urgent: true\n"
        "owner:\n"
        "weight: 12.5\n"
        "sections:\n"
        "  - title: Purpose\n    body: Why.\n"
        "  - title: Rationale\n    body: Because.\n"
    )


@then("the first field reads back as a yes-or-no, the second as nothing at all, and the third as a number")
def _typed_values_read_back(root, created):
    assert not created.faults, created.faults
    on_disk = held.artifact(root, created.id)
    assert (on_disk["urgent"], on_disk["owner"], on_disk["weight"]) == (True, None, 12.5)


@then("none of the three reads back as text")
def _none_of_them_text(root, created):
    on_disk = held.artifact(root, created.id)
    assert not any(isinstance(on_disk[name], str) for name in ("urgent", "owner", "weight"))


@given("a title for a new decision that is the number 12 rather than text", target_fixture="title")
def _a_title_that_is_a_number():
    return 12


@when(
    "the client creates a decision that is missing its purpose and supersedes a decision the store does not hold, "
    "saying which role and why",
    target_fixture="attempt",
)
def _create_with_two_faults(client, tmp_path):
    before = held.everything_in(tmp_path)
    response = request(client, "decision", "Price reviews happen weekly", {
        "supersedes": "decision/prices-are-reviewed-monthly",
        "sections": [SECTIONS[1]],
    }, message="Record it")
    return {
        "response": response, "before": before, "after": held.everything_in(tmp_path),
        "faults": [("sections", "sections"), ("supersedes", "ref")],
    }


@then("the artifact is rejected with both faults, each naming the artifact, the place in it and the rule broken")
def _rejected_with_both_faults(attempt):
    refused = attempt["response"]
    assert (refused.id, refused.revision) == ("", 0)
    assert sorted((fault.artifact, fault.path, fault.rule) for fault in refused.faults) == [
        ("decision/price-reviews-happen-weekly", path, rule) for path, rule in attempt["faults"]
    ]


@then("the store is unchanged")
def _store_unchanged(attempt):
    assert attempt["after"] == attempt["before"]


@given(parsers.parse('a decision the store already holds, titled "{title}"'), target_fixture="first")
def _a_decision_already_held(root, client, title):
    created = request(client, "decision", title, {"sections": SECTIONS}, message="Record it")
    assert not created.faults, created.faults
    return {"id": created.id, "title": title, "bytes": held.text(root, created.id)}


@when("the client creates another decision with that same title, saying which role and why", target_fixture="created")
def _create_another_with_that_title(client, first):
    return request(client, "decision", first["title"], {"sections": [
        {"title": "Purpose", "body": "Keep the shelf prices honest.\n"},
        {"title": "Rationale", "body": "Suppliers change their lists every week.\n"},
    ]}, message="Record it again")


@then("the client is given a name of its own for the new decision, the name already taken with a number added")
def _a_numbered_name(client, first, created):
    assert not created.faults, created.faults
    assert (created.id, created.revision) == (f"{first['id']}-2", 1)
    assert read(client, created.id).title == first["title"]


@then("the decision created first keeps the name it had")
def _the_first_keeps_its_name(root, client, first):
    kept = read(client, first["id"])
    assert (kept.id, kept.revision) == (first["id"], 1)
    assert held.text(root, first['id']) == first["bytes"]


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
    on_disk = held.artifact(root, created.id)
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


@when(
    "the client creates a decision whose options are of a shape the type does not allow and which is also missing its "
    "purpose, saying which role and why",
    target_fixture="attempt",
)
def _create_with_two_kinds_of_fault(root, client):
    before = held.holds(root)
    response = request(client, "decision", "Price reviews happen weekly", {"sections": SECTIONS[1:], "options": "Keep weekly"})
    return {
        "response": response, "before": before, "after": held.holds(root),
        "faults": [("options", "type"), ("sections", "sections")],
    }


WHOLE = "sections:\n  - title: Purpose\n    body: Why.\n  - title: Rationale\n    body: Because.\n"
SENSELESS = {
    "content that cannot be read as written at all": (WHOLE + "options: [Keep weekly\n", ""),
    "content that is a list rather than a set of named entries": ("- Purpose\n- Rationale\n", ""),
    "content that is a single bare value": ("Keep prices in step with costs.\n", ""),
    "content with nothing in it at all": ("", ""),
    "content whose sections are one line of text rather than sections":
        ("sections: Keep prices in step with costs.\n", "sections"),
    "content whose options are a single value rather than a collection": (WHOLE + "options: Keep weekly\n", "options"),
    "content one of whose options is a bare value": (WHOLE + "options:\n  - Keep weekly\n", "options/0"),
}


@when(
    parsers.re(f"the client creates a decision from (?P<senseless>{'|'.join(map(re.escape, SENSELESS))}), "
               "saying which role and why"),
    target_fixture="attempt",
)
def _create_from_senseless_content(root, client, senseless):
    before = held.holds(root)
    text, place = SENSELESS[senseless]
    response = _raw(client, text)
    return {"response": response, "before": before, "after": held.holds(root), "place": place}


REASONS = {
    "content cannot be read as written": ("content", "it is not YAML that can be read"),
    "content is a set of named entries": ("content", "content is a set of named entries"),
    "the content does not fit the type": ("type", ""),
}


@then(parsers.re(
    f"the artifact is rejected because (?P<reason>{'|'.join(map(re.escape, REASONS))}), "
    "and the place it went wrong is named"
))
def _rejected_for_senseless_content(attempt, reason):
    refused, (rule, words) = attempt["response"], REASONS[reason]
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.path, fault.rule) for fault in refused.faults] == [(attempt["place"], rule)]
    assert words in refused.faults[0].message


@then("the call comes back with its answer rather than breaking off")
def _the_call_answers(attempt):
    assert isinstance(attempt["response"], kb_pb2.CreateResponse)
    assert attempt["response"].faults


@when('the client creates a decision carrying a field written "2026-09-24", saying which role and why', target_fixture="created")
def _create_with_a_bare_date(client):
    text = content.dumps({"sections": SECTIONS}) + "options:\n  - title: Revisit\n    body: 2026-09-24\n"
    return client.Create(kb_pb2.CreateRequest(
        type="decision", title="Review prices again", content=text, actor=CLIENT, message="Say when to revisit",
    ))


@then("that field reads back as the text that was written, not as a date")
def _field_is_text_not_a_date(root, client, created):
    assert not created.faults, created.faults
    assert content.loads(read(client, created.id, whole=True).content)["options"][0]["body"] == "2026-09-24"
    on_disk = held.artifact(root, created.id)
    assert on_disk["options"][0]["body"] == "2026-09-24"


@when(
    "the client creates a decision whose rationale carries a title and an empty body, saying which role and why",
    target_fixture="created",
)
def _create_with_an_empty_rationale(client):
    return create(client, "decision", {
        "title": "Price reviews happen weekly",
        "sections": [SECTIONS[0], {"title": "Rationale", "body": ""}],
    }, message="Say why later")


@then("the rationale reads back with an empty body")
def _rationale_reads_back_empty(root, client, created):
    rationale = read(client, created.id, section="Rationale")
    assert not rationale.faults, rationale.faults
    assert content.loads(rationale.content) == {"title": "Rationale", "body": ""}
    on_disk = held.artifact(root, created.id)
    assert on_disk["sections"][1] == {"title": "Rationale", "body": ""}


@when(
    "the client creates a decision one of whose lines of prose ends in a space, saying which role and why",
    target_fixture="attempt",
)
def _create_with_a_line_ending_in_a_space(root, client):
    before = held.holds(root)
    text = (
        "sections:\n  - title: Purpose\n    body: |\n      Keep prices in step with costs.\n"
        "  - title: Rationale\n    body: |\n      Costs move weekly. \n      So we review weekly.\n"
    )
    response = _raw(client, text)
    return {"response": response, "before": before, "after": held.holds(root)}


@then(
    "the artifact is rejected because every piece of prose is written as a block, and this prose could not be "
    "written back as one"
)
def _rejected_as_prose_that_is_no_block(attempt):
    refused = attempt["response"]
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.artifact, fault.rule) for fault in refused.faults] == [
        ("decision/price-reviews-happen-weekly", "content"),
    ]
    assert refused.faults[0].message.startswith(
        "every piece of prose is written as a block, and this prose could not be written back as one"
    )
