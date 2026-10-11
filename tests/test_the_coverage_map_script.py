"""The script that asks the coverage map (tools/coverage_map.py): its function lookup, its ranges and its refusal of a
map that is missing or older than the code, on small inputs, without the real map."""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import coverage_map  # noqa: E402

SOURCE = "import x\n\n\ndef top():\n    return 1\n\n\nclass Holder:\n    def method(self):\n        a = 1\n        return a\n"


def test_lines_are_given_as_ranges():
    assert coverage_map.ranges([7, 1, 2, 3, 3, 9, 10]) == ["1-3", "7", "9-10"]
    assert coverage_map.ranges([]) == []


def test_a_function_and_a_method_resolve_to_their_lines():
    assert list(coverage_map.function_lines(SOURCE, "top")) == [4, 5]
    assert list(coverage_map.function_lines(SOURCE, "Holder.method")) == [9, 10, 11]
    assert list(coverage_map.function_lines(SOURCE, "Holder"))[0] == 8


def test_a_function_that_is_not_there_is_refused():
    with pytest.raises(SystemExit, match="no function"):
        coverage_map.function_lines(SOURCE, "missing")


def test_a_missing_or_older_map_is_refused(tmp_path):
    (tmp_path / "src" / "kb").mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    code = tmp_path / "src" / "kb" / "a.py"
    code.write_text("")
    with pytest.raises(SystemExit, match="make coverage-map"):
        coverage_map.check_fresh(tmp_path)
    for name in (coverage_map.DATA, coverage_map.PASSED):
        (tmp_path / name).write_text("")
        os.utime(tmp_path / name, (1, 1))
    with pytest.raises(SystemExit, match="older"):
        coverage_map.check_fresh(tmp_path)
    for name in (coverage_map.DATA, coverage_map.PASSED):
        os.utime(tmp_path / name, None)
    coverage_map.check_fresh(tmp_path)


def _tree(tmp_path):
    """A checkout in little: one module of src/kb, and a file outside it."""
    (tmp_path / "src" / "kb").mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "kb" / "a.py").write_text(SOURCE)
    (tmp_path / "tests" / "test_a.py").write_text(SOURCE)
    return tmp_path


def test_a_file_a_line_and_a_function_are_located(tmp_path):
    root = _tree(tmp_path)
    assert coverage_map.locate(root, "src/kb/a.py") == (root / "src/kb/a.py", None)
    assert coverage_map.locate(root, "src/kb/a.py:10") == (root / "src/kb/a.py", range(10, 11))
    assert coverage_map.locate(root, "kb.a.Holder.method") == (root / "src/kb/a.py", range(9, 12))


@pytest.mark.parametrize("target, said", [
    ("src/kb/nope.py", "src/kb/nope.py is not a file under src/kb"),
    ("tests/test_a.py", "tests/test_a.py is not a file under src/kb"),
    ("src/kb/../../tests/test_a.py", "is not a file under src/kb"),
])
def test_a_path_that_is_not_a_file_of_the_source_is_refused(tmp_path, target, said):
    with pytest.raises(SystemExit, match=said):
        coverage_map.locate(_tree(tmp_path), target)


@pytest.mark.parametrize("line, why", [
    ("9999", "past the end"), ("1", "the module's top level"), ("4", "a def line"), ("6", "a blank line"),
    ("0", "no line"), ("ten", "not a number"),
])
def test_a_line_that_is_not_a_statement_inside_a_function_is_refused(tmp_path, line, why):
    with pytest.raises(SystemExit, match=f"src/kb/a.py:{line} is not a statement inside a function"):
        coverage_map.locate(_tree(tmp_path), f"src/kb/a.py:{line}")


def test_a_map_older_than_a_feature_is_refused(tmp_path):
    root = _tree(tmp_path)
    (root / "features").mkdir()
    for name in (coverage_map.DATA, coverage_map.PASSED):
        (root / name).write_text("")
    coverage_map.check_fresh(root)
    feature = root / "features" / "a.feature"
    feature.write_text("")
    later = (root / coverage_map.DATA).stat().st_mtime + 10
    os.utime(feature, (later, later))
    with pytest.raises(SystemExit, match="older than src/kb, tests or features: run make coverage-map"):
        coverage_map.check_fresh(root)


def test_the_unexecuted_lines_are_given_with_a_total_for_each_file_and_for_all():
    assert coverage_map.report([("src/kb/a.py", [3, 4, 9], 10), ("src/kb/b.py", [], 5), ("src/kb/c.py", [2], 4)]) == [
        "src/kb/a.py: 3-4, 9 (3 of 10)",
        "src/kb/c.py: 2 (1 of 4)",
        "total: 4 of 19 lines inside functions, in 2 of 3 files",
    ]
