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
