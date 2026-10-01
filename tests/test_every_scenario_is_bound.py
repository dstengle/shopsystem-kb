"""Every scenario formulated in features/ is run by some test module, and by only one binding.

A scenario nobody binds is run by nothing, so a feature file can grow scenarios the suite never mentions. This reads the
scenario titles from the feature files themselves and the ones bound from the test modules' own bound scenarios (what
`scenarios(...)` and `@scenario(...)` leave on each test function), so a bound title that does not exist is not hiding
a missing one."""
import importlib
from collections import Counter
from pathlib import Path

from pytest_bdd.parser import FeatureParser

TESTS = Path(__file__).resolve().parent
FEATURES = TESTS.parent / "features"


def formulated():
    """Every (feature file, scenario title) in features/, an outline's title once however many Examples it has."""
    titles = []
    for path in sorted(FEATURES.glob("*.feature")):
        feature = FeatureParser(str(FEATURES), path.name).parse()
        titles.extend((path.name, name) for name in feature.scenarios)
    return titles


def bound():
    """Every (feature file, scenario title) a test module binds, once for each binding."""
    found = []
    for path in sorted(TESTS.glob("test_*.py")):
        module = importlib.import_module(path.stem)
        for value in vars(module).values():
            scenario = getattr(value, "__scenario__", None)
            if scenario is not None:
                found.append((Path(scenario.feature.filename).name, scenario.name))
    return found


def test_every_scenario_formulated_in_the_features_is_bound_by_a_test_module():
    held = Counter(bound())
    unbound = [title for title in formulated() if title not in held]
    assert not unbound, f"bound by no test module: {unbound}"


def test_no_scenario_formulated_in_the_features_is_bound_twice():
    twice = sorted(title for title, count in Counter(bound()).items() if count > 1)
    assert not twice, f"bound more than once: {twice}"
