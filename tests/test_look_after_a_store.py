import grpc
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from calls import DECISION_TYPE, define, start_a_store
from conftest import OPERATOR, _kb, _store_needing_attention
import held
import serving
from kb import served
from kb import client as kb_client
from kb.contract import kb_pb2, kb_pb2_grpc

scenarios("operate-a-store.feature")

@given("a directory that has no store inside it", target_fixture="root")
@given("a directory that has no store inside it, and nothing names which role the operator is", target_fixture="root")
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


@given("a directory holding a store", target_fixture="root")
def _directory_holding_a_store(root):
    start_a_store(root)
    return root


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
    with grpc.insecure_channel(f"{REACHED_THROUGH[reached]}:{port}") as channel:
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


@then("serving the store is rejected because the store cannot be served at that address, and the address is named back")
def _serve_rejected_at_that_address(ran):
    assert (ran["ran"].returncode, ran["ran"].stdout) == (2, "")
    assert ran["ran"].stderr.startswith(f"kb serve: refused: the store cannot be served at {ran['listen']!r}"), \
        ran["ran"].stderr


@then("nothing is served")
def _nothing_is_served(root):
    """No server owns the store: its lock is there to be taken."""
    served.owned(root).close()
