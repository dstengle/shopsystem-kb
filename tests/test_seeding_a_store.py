"""A store set up seeded from a directory of files, in the cases no scenario names: what is left behind is either no
store at all or a whole one."""
from calls import a_decision_type_and_a_decision
from conftest import OPERATOR, _kb, exported
import held


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
