"""`kb serve` on a root that holds no store this kb can serve is refused before it listens, with the fault discovery
or opening the store gives; and the operator's commands over a store's own files, run where the search finds the
connection to a server, are refused rather than sent through it (the plan's decisions 6 and 11)."""
import socket

import pytest

from calls import start_a_store
from conftest import OPERATOR, _kb
import held
import serving
from kb import server
from kb.addresses import Address


def _free_port():
    """A port nothing listens on, the system's choice, bound and let go."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def _answers(port):
    """Whether anything listens on 127.0.0.1 at the port."""
    with socket.socket() as probe:
        return probe.connect_ex(("127.0.0.1", port)) == 0


NOT_SERVABLE = {
    "no store": (lambda root: None, "store"),
    "an earlier kb's store": (lambda root: (start_a_store(root), held.made_by_an_earlier_kb(root)), "unreadable"),
    "a later kb's store": (lambda root: (start_a_store(root), held.made_by_a_later_kb(root)), "unreadable"),
    "a damaged database": (lambda root: (start_a_store(root), held.damage_the_database(root)), "unreadable"),
}


@pytest.mark.parametrize("what", NOT_SERVABLE)
def test_kb_serve_on_what_is_not_a_store_it_can_serve_is_refused_before_it_listens(root, what):
    made, rule = NOT_SERVABLE[what]
    made(root)
    before = held.apart_from_the_store(root), held.bytes_held(root)
    port = _free_port()
    ran = _kb("serve", str(root), "--listen", f"127.0.0.1:{port}", cwd=root)
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr.startswith(f"kb serve: refused: {rule}: "), ran.stderr
    assert not _answers(port)
    assert (held.apart_from_the_store(root), held.bytes_held(root)) == before


FILE_COMMANDS = {
    "export": lambda out: ("export", str(out)),
    "import --check": lambda out: ("import", "--check", str(out)),
    "import": lambda out: ("import", str(out)),
}


@pytest.mark.parametrize("command", FILE_COMMANDS)
def test_the_operators_file_commands_where_the_search_finds_a_connection_are_refused(root, tmp_path, command):
    start_a_store(root)
    before = held.holds(root)
    arranged = tmp_path / "arranged"
    serving.connection(arranged, "127.0.0.1:1")
    files = tmp_path / "files"
    files.mkdir()
    ran = _kb(*FILE_COMMANDS[command](files), cwd=arranged, env={"KB_ACTOR": "operator"})
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr.startswith(f"kb {command.split()[0]}: refused: store: these commands run where the store is, "
                                 f"not through a server"), ran.stderr
    assert list(files.iterdir()) == []
    assert held.holds(root) == before


def test_a_server_that_cannot_bind_its_address_leaves_nothing_open(root):
    """A start that fails at binding, the port already another's, lets the store go and closes what it made, so a
    server started on the store next owns it (Task 1's review, M6)."""
    start_a_store(root)
    with socket.create_server(("127.0.0.1", 0)) as taken:
        with pytest.raises(ValueError, match="nothing can listen there"):
            server.started(root, Address("127.0.0.1", taken.getsockname()[1]))
    after = server.started(root, Address("127.0.0.1", 0))
    after.stop()


def test_kb_serve_with_start_on_a_root_that_does_not_exist_is_refused_as_kb_init_refuses_it(tmp_path):
    """An operator's typo, or a store directory missing from a container: refused with kb.init's own fault, nothing
    served and nothing made."""
    missing, port = tmp_path / "missing", _free_port()
    ran = _kb("serve", str(missing), "--listen", f"127.0.0.1:{port}", "--start", cwd=tmp_path,
              env={"KB_ACTOR": OPERATOR})
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr.startswith("kb serve: refused: root: a store is started in a directory that exists"), ran.stderr
    assert ran.stderr.count("\n") == 1, ran.stderr
    assert not missing.exists()
    assert not _answers(port)
