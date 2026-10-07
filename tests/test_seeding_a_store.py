"""A store set up seeded from a directory of files, in the cases no scenario names: what is left behind is either no
store at all or a whole one."""
import signal

from calls import DECISION_TYPE, a_decision_type_and_a_decision, define
from conftest import OPERATOR, _kb, exported
import held
import stopping
from kb import client as kb_client, store


def test_a_seed_directory_that_is_the_directory_set_up_leaves_no_half_store(tmp_path):
    """The operator names one directory twice, as where the store goes and as its seed (a volume mounted twice):
    whatever kb answers, the directory holds no store that is not the whole seed, and nothing kb staged."""
    root = exported(tmp_path, a_decision_type_and_a_decision)
    before = held.everything_in(root)
    ran = _kb("init", str(root), "--seed", str(root), cwd=tmp_path, env={"KB_ACTOR": OPERATOR})
    assert ran.returncode in (0, 2), ran.stderr
    if ran.returncode == 2:
        assert held.everything_in(root) == before
    else:
        assert held.apart_from_the_store(root) == before["apart"]
        assert held.names(root) == ["decision/price-reviews-happen-weekly", "schema/decision", "schema/schema"]


def test_a_seeded_setup_in_a_directory_the_operator_cannot_write_is_refused_and_leaves_it_as_it_was(tmp_path, root):
    """A directory kb cannot write in (a bind mount another user owns) is refused as kb init refuses it, exit 2 and
    one refusal line, never a traceback; nothing is made in it."""
    seed = exported(tmp_path, a_decision_type_and_a_decision)
    root.chmod(0o555)
    try:
        ran = _kb("init", str(root), "--seed", str(seed), cwd=tmp_path, env={"KB_ACTOR": OPERATOR})
        assert ran.returncode == 2
        assert ran.stderr.startswith("kb init: refused: ") and ran.stderr.count("\n") == 1, ran.stderr
        assert list(root.iterdir()) == []
    finally:
        root.chmod(0o755)


def test_a_seeded_setup_interrupted_exits_without_a_traceback_and_leaves_no_store(tmp_path, root):
    """Ctrl-C during `kb init --seed` (an operator's, or `docker compose run`'s): it ends as an interrupt ends a
    program, non-zero, with no traceback, and leaves nothing, what it staged taken away."""
    seed = exported(tmp_path, a_decision_type_and_a_decision)
    ran = stopping.stopped(root, seed, OPERATOR, signal.SIGINT)
    assert ran.returncode == -signal.SIGINT
    assert "Traceback" not in ran.stderr, ran.stderr
    assert held.holds_nothing(root)


def _staged_store(root):
    """Whether a store has been started in the staging place beneath root: its marker is there, written last."""
    return (root / ".kb-starting" / store.MARKER).is_file()


def test_a_plain_setup_after_a_seeded_one_was_killed_starts_a_store_as_if_nothing_were_there(tmp_path, root):
    """What a seeded setup killed once its store was started, and while the seed was landing, left beneath the
    directory, a whole store deeper below it, is no store inside it, nor one it sits inside: kb init starts one there,
    which a client can define its types in."""
    seed = exported(tmp_path, a_decision_type_and_a_decision)
    assert stopping.stopped(root, seed, OPERATOR, ready=_staged_store).returncode == -signal.SIGKILL
    assert _staged_store(root)
    ran = _kb("init", str(root), cwd=tmp_path, env={"KB_ACTOR": OPERATOR})
    assert (ran.returncode, ran.stderr) == (0, "")
    assert held.holds_a_store(root)
    assert define(kb_client.connect(root), DECISION_TYPE).revision == 1


def test_a_seeded_setup_after_one_was_killed_lands_the_seed_and_leaves_nothing_staged(tmp_path, root):
    """The same seeded setup run again clears what the killed one left, a store started deeper below and the seed
    landing in it, before it starts, and leaves nothing but the
    store in the directory."""
    seed = exported(tmp_path, a_decision_type_and_a_decision)
    assert stopping.stopped(root, seed, OPERATOR, ready=_staged_store).returncode == -signal.SIGKILL
    assert _staged_store(root)
    ran = _kb("init", str(root), "--seed", str(seed), cwd=tmp_path, env={"KB_ACTOR": OPERATOR})
    assert (ran.returncode, ran.stderr) == (0, "")
    assert sorted(path.name for path in root.iterdir()) == ["kb"]
    assert held.names(root) == ["decision/price-reviews-happen-weekly", "schema/decision", "schema/schema"]
