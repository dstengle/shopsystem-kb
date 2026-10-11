"""A pytest plugin for `make coverage-map`: writes the node ids of the tests that passed to `.coverage-map.passed`,
so the map is read for passing tests only (an expected failure ran its code too, and holds nothing)."""
from pathlib import Path

PASSED = ".coverage-map.passed"
_passed = set()


def pytest_runtest_logreport(report):
    if report.when == "call" and report.passed and not hasattr(report, "wasxfail"):
        _passed.add(report.nodeid)


def pytest_sessionfinish(session):
    if not hasattr(session.config, "workerinput"):
        Path(session.config.rootpath, PASSED).write_text("".join(f"{each}\n" for each in sorted(_passed)))
