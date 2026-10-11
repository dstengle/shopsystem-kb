"""A plain test of what `kb validate` prints for a placeholder a link into a part makes: the IRI, `#` and the part,
as a field holds such a link, so that it prints apart from a link to the whole of that IRI (decision 5 of batch 35's
plan: a link into a part is listed with that part)."""
from calls import DECISION_TYPE, NOTE_TYPE, create, define, iri, start_a_store
from conftest import _kb
from kb import client as kb_client

SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]
MONTHLY, YEARLY = iri("decision", "prices-are-reviewed-monthly"), iri("decision", "prices-are-reviewed-yearly")
INTO_A_PART, TO_THE_WHOLE = iri("note", "why-monthly"), iri("note", "why-not-yearly")


def test_kb_validate_prints_a_link_into_a_part_with_its_part_and_a_link_to_the_whole_without(root):
    """One note is about an option of a decision the store holds, created since without that option; another is
    about a decision the store does not hold."""
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, DECISION_TYPE)
    define(client, NOTE_TYPE)
    create(client, "note", {"title": "Why monthly", "about": f"{MONTHLY}#options/go-monthly"})
    create(client, "note", {"title": "Why not yearly", "about": YEARLY})
    create(client, "decision", {
        "title": "Prices are reviewed monthly", "sections": SECTIONS, "options": [{"title": "Go yearly"}],
    })
    ran = _kb("validate", cwd=root, env={})
    assert (ran.returncode, ran.stderr) == (0, "")
    assert ran.stdout.splitlines() == [
        f"placeholder\t{MONTHLY}#options/go-monthly\t{INTO_A_PART}\tabout",
        f"placeholder\t{YEARLY}\t{TO_THE_WHOLE}\tabout",
    ]
