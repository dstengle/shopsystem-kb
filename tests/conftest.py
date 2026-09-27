"""Suite wiring. Step definitions live beside the scenarios they serve; shared Givens are added here by slice 1."""
import re
import tempfile
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, then, when

from calls import CLIENT, DECISION_TYPE, MANGLED, create, define, everything_under, journal, listing, moment
from kb import canonical, client as kb_client, store
from kb.contract import kb_pb2
from repositories import git, hooked, made, standing


def pytest_configure(config):
    """Register every @slice-<n> tag in the feature files as a marker, so -m slice-<n> selects a slice."""
    tags = set()
    for feature in Path(config.rootpath, "features").glob("*.feature"):
        tags.update(re.findall(r"@(slice-\d+(?:\.\d+)?)", feature.read_text()))
    for tag in sorted(tags):
        config.addinivalue_line("markers", f"{tag}: scenario of that slice in the plan")


def _guard_starts(config):
    """Where the guard looks for a store, upward from each: the checkout, the system's temporary directory, and
    pytest's own base temp root, wherever `--basetemp` or `TMPDIR` puts it. A seam a demonstration can point
    elsewhere without touching where the real ones sit."""
    return (config.rootpath, Path(tempfile.gettempdir()), config._tmp_path_factory.getbasetemp())


def pytest_sessionstart(session):
    """Refuse to run rather than reach a store outside the suite's own temporary directories: one is never found by
    looking upward, discovery's own way, from any of `_guard_starts`."""
    for start in _guard_starts(session.config):
        found = store.find_above(start)
        if found is not None:
            pytest.exit(
                f"refusing to run: a store was found at {found!s}, above {start!s}; "
                f"no test may reach a store outside its own temporary directory",
                returncode=1,
            )


@pytest.fixture(autouse=True)
def _works_under_its_own_tmp_path(tmp_path, monkeypatch):
    """Every test starts working in a directory under its own tmp_path, restored after, with KB_ROOT cleared unless
    the test sets it, so discovery from the working directory never reaches outside it. A Given that finds or names
    a store of its own chdirs, or sets KB_ROOT, afterward and keeps working."""
    working = tmp_path / "working"
    working.mkdir()
    monkeypatch.chdir(working)
    monkeypatch.delenv("KB_ROOT", raising=False)


@pytest.fixture
def root(tmp_path):
    """The directory a store is started in; the store is its kb/ subdirectory."""
    root = tmp_path / "store"
    root.mkdir()
    return root


@given("a store", target_fixture="client")
def _a_store(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    return client


@given(parsers.parse("the client was readied with a clock that reads {reading}"), target_fixture="client")
def _readied_with_a_clock(root, reading):
    """A client over the store at root whose clock stands still at that moment, given in the zone the step names."""
    stood = moment(reading)
    return kb_client.connect(root, clock=lambda: stood)


@pytest.fixture
def before():
    """What a store held before a scenario's When, filled in by the Given that made it: the store's root, and every
    file below it with its bytes."""
    return {}


def _store_with_content(root):
    """A store started in root, holding the decision type and a decision."""
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    create(client, "decision", {
        "title": "Price reviews happen weekly",
        "sections": [
            {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
            {"title": "Rationale", "body": "Costs move weekly.\n"},
        ],
    })


@given("a directory that already has a store inside it, with content in that store", target_fixture="root")
def _directory_with_a_store_inside(root, before):
    _store_with_content(root)
    before.update(store=root, held=everything_under(root))
    return root


@given("a directory that sits inside a store", target_fixture="root")
def _directory_inside_a_store(root, before):
    _store_with_content(root)
    inside = root / "notes" / "drafts"
    inside.mkdir(parents=True)
    before.update(store=root, held=everything_under(root))
    return inside


@then("the store that is there holds what it held before")
@then("the store it sits inside holds what it held before")
def _store_holds_what_it_held(before):
    assert everything_under(before["store"]) == before["held"]


@given("someone edited the decision's file by hand and left it in a shape the store cannot read")
def _decision_file_mangled_by_hand(root, monkeypatch):
    """The decision a feature's Background holds, decision/price-reviews-happen-weekly, left unreadable, with the
    client working in the store and nothing naming it."""
    (root / "kb" / "decision" / "price-reviews-happen-weekly.yaml").write_text(MANGLED)
    monkeypatch.chdir(root)
    monkeypatch.delenv("KB_ROOT", raising=False)


@when("the client checks the store", target_fixture="checked")
def _check_the_store(client):
    return client.Validate(kb_pb2.ValidateRequest())


@then("that file is reported as a violation, naming the file")
def _reported_as_unreadable(checked):
    unreadable = [fault for fault in checked.violations if fault.rule == "unreadable"]
    assert [fault.artifact for fault in unreadable] == ["decision/price-reviews-happen-weekly"]
    assert "decision/price-reviews-happen-weekly.yaml cannot be read" in unreadable[0].message


@then("the check comes back with its answer rather than breaking off")
def _answers(checked):
    assert isinstance(checked, kb_pb2.ValidateResponse)
    assert not checked.faults, checked.faults


@then("the store holds no artifact it did not hold before")
def _no_new_artifact(root, client, attempt):
    assert [stub.id for stub in listing(client, "decision", ids_only=True).stubs] == attempt["names"]
    assert everything_under(root / "kb") == attempt["files"]


@then("the store's history holds no entry for it")
def _no_entry_in_history(client, attempt):
    assert len(journal(client).entries) == attempt["entries"]


@pytest.fixture
def starter():
    """The role a scenario's store was started under."""
    return CLIENT.role


@then(
    parsers.parse('the store\'s history holds one entry, under that role, with the message "{message}"'),
    target_fixture="entry",
)
def _one_entry_under_the_role(root, starter, message):
    """The one entry in the journal's files, and the one commit in the store's own git history, both under the role
    the store was started under."""
    entries = sorted((root / "kb" / "journal").rglob("*.yaml"))
    assert len(entries) == 1, entries
    entry = canonical.load(entries[0].read_text())
    assert (entry["actor"]["role"], entry["message"]) == (starter, message)
    assert git(root / "kb", "log", "--format=%an%x09%s").splitlines() == [f"{starter}\t{message}"]
    return entry


REPOSITORIES = {
    "the git repository the directory the store sits in belongs to": lambda root, tmp_path: made(root),
    "the git repository that directory is": lambda root, tmp_path: root,
    "a git repository elsewhere, which holds no store": lambda root, tmp_path: made(tmp_path / "elsewhere-repository"),
}


@given(
    parsers.re(
        f"the client runs with its environment naming (?P<repository>{'|'.join(REPOSITORIES)}) as the git repository "
        f"to work in, the way git does for a program it runs from a hook"
    ),
    target_fixture="named_repository",
)
def _environment_naming_a_repository(root, tmp_path, monkeypatch, repository):
    """The repository named, under tmp_path, set in this process's environment, restored after, and how it stood."""
    path = REPOSITORIES[repository](root, tmp_path)
    for name, value in hooked(path).items():
        monkeypatch.setenv(name, value)
    return {"path": path, "standing": standing(path)}


@then(
    "that git repository is left as it was, with nothing added to its history and nothing made ready for its next commit"
)
def _repository_left_as_it_was(named_repository):
    assert standing(named_repository["path"]) == named_repository["standing"]
