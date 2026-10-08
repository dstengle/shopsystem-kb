import signal
import socket

import grpc
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from calls import DECISION_TYPE, a_decision_type_and_a_decision, define, start_a_store
from conftest import OPERATOR, _kb, _store_needing_attention, _store_with_content, exported
import held
import serving
import stopping
from kb import canonical
from kb import client as kb_client
from kb.contract import kb_pb2, kb_pb2_grpc

scenarios("operate-a-store.feature")

@given("a directory that has no store inside it", target_fixture="root")
@given("a directory holding no store", target_fixture="root")
@given("a directory that has no store inside it, and nothing names which role the operator is", target_fixture="root")
@given("a directory holding no store, and nothing names which role the operator is", target_fixture="root")
def _directory_with_no_store(root):
    return root


@pytest.fixture
def starter():
    """The role the operator starts a store under."""
    return OPERATOR


@when("the operator runs kb init against that directory, saying which role they are", target_fixture="ran")
def _kb_init_with_a_role(root, tmp_path):
    return _kb("init", str(root), cwd=tmp_path, env={"KB_ACTOR": OPERATOR})


@when("the operator runs kb init against that directory", target_fixture="ran")
def _kb_init_without_a_role(root, tmp_path):
    return _kb("init", str(root), cwd=tmp_path)


@then("there is a store inside that directory, in a place of its own")
def _a_store_inside(ran, root):
    """The store is the one thing added to what the directory held."""
    assert (ran.returncode, ran.stderr) == (0, "")
    assert held.holds_a_store(root)
    assert held.apart_from_the_store(root) == {}


@then("a client can begin defining its own types in it straight away")
def _client_defines_a_type(root):
    defined = define(kb_client.connect(root), DECISION_TYPE)
    assert (defined.id, defined.revision) == ("schema/decision", 1)


@then("setting the store up is rejected because the role must be named through KB_ACTOR")
def _rejected_without_kb_actor(ran):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == "kb init: refused: actor: a store can only be started under a role, named through KB_ACTOR\n"


@then("that directory still has no store inside it")
def _still_no_store(root):
    assert list(root.iterdir()) == []


@then("setting the store up is rejected because that directory already has a store inside it")
def _init_rejected_as_already_a_store(ran, root):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == (
        f"kb init: refused: root: a store is never started over another; {str(root)!r} already has a store inside it\n"
    )


@then("setting the store up is rejected because that directory is inside a store")
def _init_rejected_as_inside_a_store(ran, root, before):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == (
        f"kb init: refused: root: stores do not nest; {str(root)!r} is inside the store at {str(before['store'])!r}\n"
    )


REPORT = (
    "violation\tdecision/prices-are-reviewed-monthly\tsections/0\trequired\t<the validator's message>\n"
    "stale\tdecision/price-reviews-happen-weekly\tchecked against version 1 of its type, which is at 2\n"
    "stale\tdecision/prices-are-reviewed-monthly\tchecked against version 1 of its type, which is at 2\n"
)


def _unworded(report):
    """A report with each violation's message, which is the validator's wording, left out; its rule and place stay."""
    return "".join(
        "\t".join(line.split("\t")[:4]) + "\n" if line.startswith("violation\t") else line + "\n"
        for line in report.splitlines()
    )


@given("a store whose content the operator did not write", target_fixture="where")
def _store_the_operator_did_not_write(root):
    return {"cwd": _store_needing_attention(root), "env": {}}


@when("the operator runs kb validate in that store", target_fixture="ran")
@when("the operator runs kb validate there", target_fixture="ran")
def _kb_validate(where):
    return _kb("validate", cwd=where["cwd"], env=where["env"])


@then("the operator is told of everything in the store that does not fit its type, and where")
def _told_of_every_violation(ran):
    assert (ran.returncode, ran.stderr) == (1, "")
    violations = [line for line in _unworded(ran.stdout).splitlines() if line.startswith("violation")]
    assert violations == _unworded(REPORT).splitlines()[:1]


@then("of everything that is behind the type it was last checked against")
def _told_of_everything_stale(ran):
    assert _unworded(ran.stdout) == _unworded(REPORT)


@when("the operator asks what the command line offers", target_fixture="ran")
def _kb_help(root):
    return _kb("--help", cwd=root)


@then("it offers setting a store up, checking and exporting one, and importing into a freshly started store")
def _offers_four_commands(ran):
    assert (ran.returncode, ran.stderr) == (0, "")
    listed = ran.stdout.split("positional arguments:")[1].split("options:")[0]
    assert listed.split("\n", 2)[1].strip() == "{init,validate,export,import,serve}"
    lines = " ".join(listed.split())
    assert "init set up a store in a directory" in lines
    assert "validate check the store" in lines
    assert "export write the store" in lines
    assert "import bring a directory of files into a freshly started store" in lines


@then("nothing else that changes what the store holds")
def _nothing_else(root):
    """Serving a store (operate-a-store's Purpose) hands it to callers, whose changes go through a client; no command
    changes content itself but the import."""
    for command in ("create", "replace", "remove"):
        refused = _kb(command, cwd=root)
        assert refused.returncode == 2
        assert f"invalid choice: '{command}'" in refused.stderr


@then("the store found above where they are working is the one checked")
@then("the store KB_ROOT names is the one checked")
def _that_store_checked(ran):
    assert (ran.returncode, _unworded(ran.stdout), ran.stderr) == (1, _unworded(REPORT), "")


@then("the check is rejected because no store was found, neither above where they are working nor named outright")
def _rejected_as_no_store(ran, where):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == f"kb validate: refused: store: no store was found, neither above {where['cwd']} nor named outright\n"


@then("the check is rejected because KB_ROOT names a directory that holds no store")
def _rejected_as_kb_root_names_no_store(ran, where):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == (
        f"kb validate: refused: store: KB_ROOT names a directory that holds no store: {where['env']['KB_ROOT']}\n"
    )


@then(
    "the check is rejected because KB_ROOT names a store other than the one they are standing in, and neither of the "
    "two is guessed at"
)
def _rejected_as_two_stores(ran, where):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == (
        f"kb validate: refused: store: KB_ROOT names a store other than the one {where['cwd']} is working in: "
        f"KB_ROOT is {where['env']['KB_ROOT']}, the working directory is inside {where['cwd']}; neither is guessed at\n"
    )


@then("the store is checked")
def _the_store_is_checked(ran):
    assert ran.returncode == 1, ran.stderr
    assert _unworded(ran.stdout) == _unworded(REPORT)


@then("kb validate is not refused because the store was busy with another change")
def _validate_not_busy(ran):
    assert (ran.returncode, ran.stderr) == (1, "")


INTERFACES = {"one interface of the machine": "127.0.0.1", "every interface of the machine": "0.0.0.0"}
REACHED_THROUGH = {"that interface": "127.0.0.1", "any one of the machine's interfaces": "127.0.0.2"}


@when(parsers.parse("the operator runs kb serve on that directory, giving an address on {interface}"),
      target_fixture="served")
def _kb_serve_at(root, request, interface):
    host = INTERFACES[interface]
    return {"host": host, "serving": serving.started(root, request, listen=f"{host}:0")}


@then("the store is served at that address", target_fixture="port")
def _served_at_that_address(served):
    said = served["serving"].said()
    host, _, port = said.removeprefix("serving\t").rpartition(":")
    assert said.startswith("serving\t") and host == served["host"] and int(port) > 0, said
    return int(port)


@then(parsers.parse("a caller reaching that address through {reached} is answered from that store"))
def _answered_from_that_store(root, port, reached):
    _answered_at(root, f"{REACHED_THROUGH[reached]}:{port}")


def _answered_at(root, address):
    """A caller at the address is answered the store's history, as a client in this process reads it from root."""
    with grpc.insecure_channel(address) as channel:
        answered = kb_pb2_grpc.KbStub(channel).History(kb_pb2.HistoryRequest())
    assert answered == kb_client.connect(root).History(kb_pb2.HistoryRequest())
    assert answered.WhichOneof("outcome") == "result" and answered.result.entries


@when("the operator runs kb serve on that directory without giving an address", target_fixture="ran")
def _kb_serve_without_an_address(root):
    return _kb("serve", str(root), cwd=root)


@then("serving the store is rejected because no address is assumed")
def _serve_rejected_without_an_address(ran):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == "kb serve: refused: no address is assumed; give the one to serve at with --listen HOST:PORT\n"


def _held_by_another_server(tmp_path, request):
    """The address a kb server for another store is serving at."""
    other = tmp_path / "other"
    other.mkdir()
    start_a_store(other)
    return str(serving.hosted(other, request, clock=None).address)


UNSERVABLE = {
    "an address that names no port": lambda tmp_path, request: "127.0.0.1",
    "an address whose port is beyond the last": lambda tmp_path, request: "127.0.0.1:65536",
    "an address another server already holds": _held_by_another_server,
}


@when(parsers.re(f"the operator runs kb serve on that directory, giving (?P<address>{'|'.join(UNSERVABLE)})"),
      target_fixture="ran")
def _kb_serve_where_it_cannot(root, tmp_path, request, address):
    listen = UNSERVABLE[address](tmp_path, request)
    return {"listen": listen, "ran": _kb("serve", str(root), "--listen", listen, cwd=root)}


@when(parsers.re(f"the operator runs kb serve with --start on that directory, giving (?P<address>{'|'.join(UNSERVABLE)}), "
                 "saying which role they are"), target_fixture="ran")
def _kb_serve_starting_where_it_cannot(root, tmp_path, request, address):
    listen = UNSERVABLE[address](tmp_path, request)
    return {"listen": listen,
            "ran": _kb("serve", str(root), "--listen", listen, "--start", cwd=root, env={"KB_ACTOR": OPERATOR})}


@then("serving the store is rejected because the store cannot be served at that address, and the address is named back")
@then("serving is rejected because the store cannot be served at that address, and the address is named back")
def _serve_rejected_at_that_address(ran):
    assert (ran["ran"].returncode, ran["ran"].stdout) == (2, "")
    assert ran["ran"].stderr.startswith(f"kb serve: refused: the store cannot be served at {ran['listen']!r}"), \
        ran["ran"].stderr


@when("the operator runs kb serve with --start on that directory, giving an address, saying which role they are",
      target_fixture="served")
def _kb_serve_starting(root, request):
    return {"serving": serving.started(root, request, "127.0.0.1:0", "--start", env={"KB_ACTOR": OPERATOR})}


@given("a directory holding a store with content in it, and nothing names which role the operator is",
       target_fixture="root")
def _directory_holding_a_store_with_content(root, before):
    _store_with_content(root)
    before.update(store=root, held=held.everything_but_its_serving_in(root))
    return root


@when("the operator runs kb serve with --start on that directory, giving an address", target_fixture="served")
def _kb_serve_starting_without_a_role(root, request):
    return {"serving": serving.started(root, request, "127.0.0.1:0", "--start")}


@then("it holds what it held before")
def _holds_what_it_held(before):
    assert held.everything_but_its_serving_in(before["store"]) == before["held"]


def _said(served):
    """The line the server said once it was serving, read once and kept."""
    if "said" not in served:
        served["said"] = served["serving"].said()
    return served["said"]


@then("a store is started in that directory")
def _a_store_started(served, root):
    assert _said(served).startswith("serving\t"), _said(served)
    assert held.holds_a_store(root)


@then("that store is served at that address")
def _that_store_served(served, root):
    said = _said(served)
    assert said.startswith("serving\t127.0.0.1:") and int(said.rpartition(":")[2]) > 0, said
    _answered_at(root, said.removeprefix("serving\t"))


@then("serving is rejected because a store can only be started under a role named through KB_ACTOR")
def _serve_rejected_without_kb_actor(served):
    assert _said(served) == "kb serve: refused: actor: a store can only be started under a role, named through KB_ACTOR\n"
    assert served["serving"].process.wait() == 2


@then("that directory still holds no store")
def _still_holds_no_store(root):
    """The directory as it was before: empty, with no store and nothing a start left behind."""
    assert not held.holds_anything_in_the_place(root)
    assert held.apart_from_the_store(root) == {}


@then("serving is rejected because that directory is inside a store")
def _serve_rejected_as_inside_a_store(served, root, before):
    said = _said(served)
    assert said == (f"kb serve: refused: root: stores do not nest; {str(root)!r} is inside the store at "
                    f"{str(before['store'])!r}\n"), said
    assert served["serving"].process.wait() == 2


# Serving with --start where serving without it is refused.

@given("a directory holding a store another server owns", target_fixture="root")
def _directory_holding_a_store_another_server_owns(root, request):
    start_a_store(root)
    serving.hosted(root, request, clock=None)
    return root


@given("a directory holding a store made by an earlier kb", target_fixture="root")
def _directory_holding_an_earlier_kbs_store(root):
    start_a_store(root)
    held.made_by_an_earlier_kb(root)
    return root


@given("a directory holding a store made by a later kb", target_fixture="root")
def _directory_holding_a_later_kbs_store(root):
    start_a_store(root)
    held.made_by_a_later_kb(root)
    return root


@given("a directory holding a connection to a server and no store", target_fixture="root")
def _directory_holding_a_connection_and_no_store(root):
    serving.connection(root, "127.0.0.1:1")
    return root


def _free_address():
    """An address on 127.0.0.1 nothing holds, at a port the system picked and let go."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return f"127.0.0.1:{probe.getsockname()[1]}"


@when("the operator runs kb serve with --start on that directory, giving an address nothing else holds, saying which "
      "role they are", target_fixture="ran")
def _kb_serve_starting_at_a_free_address(root):
    listen = _free_address()
    return {"listen": listen,
            "ran": _kb("serve", str(root), "--listen", listen, "--start", cwd=root, env={"KB_ACTOR": OPERATOR})}


@then("serving is rejected for the same reason kb serve without --start, run there at that address, is rejected")
def _rejected_as_serve_without_start_is(ran, root):
    """Plain kb serve, run after at the same address on the same directory, refuses with the same words and code."""
    plain = _kb("serve", str(root), "--listen", ran["listen"], cwd=root)
    assert plain.returncode == 2 and plain.stderr.startswith("kb serve: refused: "), plain.stderr
    assert (ran["ran"].returncode, ran["ran"].stdout, ran["ran"].stderr) == (plain.returncode, "", plain.stderr)


# A store set up seeded from a directory of files, which an export of another store wrote.

@given("a seed directory that checks clean, holding a type for decisions and a decision", target_fixture="seed")
def _a_clean_seed(tmp_path):
    return exported(tmp_path, a_decision_type_and_a_decision)


@when("the operator runs kb init with that seed directory against the directory, saying which role they are",
      target_fixture="ran")
def _kb_init_with_a_seed(root, seed, tmp_path):
    return _kb("init", str(root), "--seed", str(seed), cwd=tmp_path, env={"KB_ACTOR": OPERATOR})


@then("there is a store inside that directory")
def _a_store_there(ran, root):
    assert (ran.returncode, ran.stderr) == (0, "")
    assert held.holds_a_store(root)
    assert held.apart_from_the_store(root) == {}


@then("it holds the files in the seed directory as kb import lands them into a freshly started store")
def _holds_the_seed_as_imported(root, seed, tmp_path):
    imported = tmp_path / "imported"
    imported.mkdir()
    assert _kb("init", str(imported), cwd=tmp_path, env={"KB_ACTOR": OPERATOR}).returncode == 0
    ran = _kb("import", str(seed), cwd=imported, env={"KB_ACTOR": OPERATOR})
    assert (ran.returncode, ran.stderr) == (0, ""), ran.stderr
    assert held.names(root) == held.names(imported)
    assert [held.text(root, name) for name in held.names(root)] == [held.text(imported, name) for name in held.names(root)]
    assert _signed_and_set(root) == _signed_and_set(imported)


def _signed_and_set(root):
    """The store's history but its moments and ids: each entry as the history gives it, and the sets they landed in,
    each named by where it first stands."""
    entries = held.history(kb_client.connect(root))
    sets = [entry.batch for entry in entries]
    kept = []
    for entry in entries:
        entry.batch = str(sets.index(entry.batch))
        entry.ClearField("id")
        entry.ClearField("at")
        kept.append(entry)
    return kept


@when("the operator's kb init with that seed directory against the directory, saying which role they are, is stopped "
      "before it finishes", target_fixture="stopped")
def _kb_init_with_a_seed_stopped(root, seed):
    """The installed command, killed as SIGKILL kills it the moment the directory holds anything and still no store."""
    return stopping.stopped(root, seed, OPERATOR)


@then("that directory has no store inside it")
def _no_store_inside(stopped, root):
    assert stopped.returncode == -signal.SIGKILL
    assert not held.holds_anything_in_the_place(root)


@when("the operator runs the same kb init again", target_fixture="ran")
def _kb_init_with_a_seed_again(root, seed, tmp_path):
    return _kb_init_with_a_seed(root, seed, tmp_path)


# A seeded setup that is refused leaves the directory as it was.

@given("a seed directory that checks clean", target_fixture="seed")
def _a_seed_that_checks_clean(tmp_path):
    return exported(tmp_path, a_decision_type_and_a_decision)


@given("a seed directory holding one file whose content does not fit its type", target_fixture="seed")
def _a_seed_with_one_unfit_file(tmp_path):
    seed = exported(tmp_path, a_decision_type_and_a_decision)
    unfit = seed / "decision" / "price-reviews-happen-weekly.yaml"
    decision = canonical.entries(unfit.read_text(encoding="utf-8"))
    decision["sections"] = decision["sections"][:1]
    unfit.write_text(canonical.dump(decision), encoding="utf-8")
    return seed


@given("a file where the seed directory should be", target_fixture="seed")
def _a_file_where_the_seed_should_be(tmp_path):
    seed = tmp_path / "seed-file"
    seed.write_text("a file the operator named where a directory was wanted\n")
    return seed


@when("the operator runs kb init with that seed directory against the directory", target_fixture="ran")
def _kb_init_with_a_seed_and_no_role(root, seed, tmp_path):
    return _kb("init", str(root), "--seed", str(seed), cwd=tmp_path)


@when("the operator runs kb init with that file as the seed directory against the directory, saying which role they "
      "are", target_fixture="ran")
def _kb_init_with_a_file_as_the_seed(root, seed, tmp_path):
    return _kb_init_with_a_seed(root, seed, tmp_path)


@then("setting the store up is rejected because the seed directory's files do not check clean")
def _rejected_as_the_seed_does_not_check_clean(ran):
    assert ran.returncode == 2
    assert ran.stderr == ("kb init: refused: content: the check found 1 error(s) in the directory, and nothing was "
                          "written\n"), ran.stderr


@then("the operator is shown the check's report")
def _shown_the_checks_report(ran, seed, tmp_path):
    """The lines kb import --check gives the same directory, in a store freshly started."""
    fresh = tmp_path / "fresh"
    fresh.mkdir()
    assert _kb("init", str(fresh), cwd=tmp_path, env={"KB_ACTOR": OPERATOR}).returncode == 0
    checked = _kb("import", "--check", str(seed), cwd=fresh)
    assert checked.stdout and checked.returncode == 1
    assert ran.stdout == checked.stdout


@then("setting the store up is rejected because files for import are read from a directory")
def _init_rejected_as_read_from_a_directory(ran, seed):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == f"kb init: refused: root: an import is read from a directory; {str(seed)!r} is not one\n"


# A directory kb cannot write is refused, whichever command would start a store in it.

@given("a directory that has no store inside it and that kb cannot write", target_fixture="root")
def _an_unwritable_directory(root, request):
    root.chmod(0o555)
    request.addfinalizer(lambda: root.chmod(0o755))
    return root


UNWRITABLE_STARTS = {
    "kb init": lambda root, tmp_path: ("init", str(root)),
    "kb init with a seed directory": lambda root, tmp_path: (
        "init", str(root), "--seed", str(exported(tmp_path, a_decision_type_and_a_decision))),
    "kb serve with --start, giving an address": lambda root, tmp_path: (
        "serve", str(root), "--listen", serving.closed_port(), "--start"),
}


@when(parsers.re(f"the operator runs (?P<command>{'|'.join(UNWRITABLE_STARTS)}) against that directory, "
                 "saying which role they are"), target_fixture="ran")
def _kb_start_where_kb_cannot_write(root, tmp_path, command):
    arguments = UNWRITABLE_STARTS[command](root, tmp_path)
    return _kb(*arguments, cwd=tmp_path, env={"KB_ACTOR": OPERATOR})


@then("starting the store is rejected because a store can only be started in a directory kb can write, and the "
      "directory is named")
def _start_rejected_as_not_writable(ran, root):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert f"refused: root: a store is started in a directory kb can write, and {str(root)!r} is not one\n" \
        in ran.stderr, ran.stderr


@then("that directory still has nothing made in it")
def _nothing_made_in_it(root):
    assert list(root.iterdir()) == []
