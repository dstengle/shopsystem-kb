"""Asks the map `make coverage-map` made (.coverage-map, one context per test) two things:

    coverage_map.py tests-for TARGET   the passing tests that execute TARGET: a file (src/kb/examining.py), a line
                                       (src/kb/examining.py:40) or a function (kb.drafting.Draft.waited)
    coverage_map.py unexecuted         the lines of src/kb no passing test executes, per file, as ranges, with a total
                                       for each file and one for all

A TARGET that is not a file under src/kb, or a line of one that is not a statement inside a function, is refused:
an empty answer always means no passing test executes it. Plain text, one item per line."""
import ast
import sys
from pathlib import Path

DATA = ".coverage-map"
PASSED = ".coverage-map.passed"
SOURCE = "src/kb"
WATCHED = (SOURCE, "tests", "features")
STALE = "run make coverage-map"


def ranges(lines) -> list[str]:
    """Line numbers as ranges: [1, 2, 3, 7] -> ['1-3', '7']."""
    out, run = [], []
    for line in sorted(set(lines)):
        if run and line != run[-1] + 1:
            out.append(_range(run))
            run = []
        run.append(line)
    return out + ([_range(run)] if run else [])


def _range(run: list[int]) -> str:
    return str(run[0]) if len(run) == 1 else f"{run[0]}-{run[-1]}"


def function_lines(source: str, qualified: str) -> range:
    """The lines of the function (or class) a dotted name inside a module's source names, `Class.method` included."""
    node = ast.parse(source)
    for part in qualified.split("."):
        node = next((each for each in ast.iter_child_nodes(node)
                     if isinstance(each, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and each.name == part), None)
        if node is None:
            raise SystemExit(f"no function {qualified!r} there")
    return range(node.lineno, node.end_lineno + 1)


def locate(root: Path, target: str) -> tuple[Path, range | None]:
    """The file a target names, and the lines of it (None for all): `path`, `path:line` or `module.function`."""
    path, lined, line = target.partition(":")
    if path.endswith(".py"):
        file = _source_file(root, path)
        return file, (_statement(root, file, f"{path}:{line}", line) if lined else None)
    parts = path.split(".")
    for cut in range(len(parts), 0, -1):
        file = root / SOURCE / Path(*parts[1:cut]).with_suffix(".py") if parts[0] == "kb" and cut > 1 else None
        if file is not None and file.is_file():
            if cut == len(parts):
                return file, None
            return file, function_lines(file.read_text(), ".".join(parts[cut:]))
    raise SystemExit(f"{target!r} names no file or function of {SOURCE}")


def _source_file(root: Path, path: str) -> Path:
    """The file under src/kb a path from the checkout's top names, or the refusal saying it names none."""
    file = root / path
    if not file.is_file() or (root / SOURCE).resolve() not in file.resolve().parents:
        raise SystemExit(f"{path} is not a file under {SOURCE}")
    return file


def _statement(root: Path, file: Path, target: str, line: str) -> range:
    """That one line of the file, or the refusal saying it is not a statement inside a function."""
    if not line.isdecimal() or int(line) not in statements(root, file):
        raise SystemExit(f"{target} is not a statement inside a function, so no test can be said to execute it")
    return range(int(line), int(line) + 1)


def statements(root: Path, file: Path) -> set[int]:
    """The lines of a file the map can hold: its statements, as coverage counts them, inside a function's body."""
    import coverage
    config = root / "pyproject.toml"
    cov = coverage.Coverage(data_file=None, config_file=str(config) if config.is_file() else False)  # sources only
    return set(cov.analysis2(str(file.resolve()))[1]) & body_lines(file.read_text())


def newest(root: Path) -> float:
    """When the newest file under src/kb, tests/ or features/ was last written: a row added to a feature's
    Examples table adds a test without touching either of the others."""
    return max(f.stat().st_mtime for top in WATCHED for f in (root / top).rglob("*")
               if f.is_file() and "__pycache__" not in f.parts)


def check_fresh(root: Path) -> None:
    for name in (DATA, PASSED):
        if not (root / name).is_file():
            raise SystemExit(f"{name} is missing: {STALE}")
    if (root / DATA).stat().st_mtime < newest(root):
        raise SystemExit(f"{DATA} is older than {SOURCE}, tests or features: {STALE}")


def passing(root: Path) -> set[str]:
    return set((root / PASSED).read_text().split("\n")) - {""}


def executed(root: Path):
    """Each measured file's {line: passing tests that executed it}, by absolute path."""
    import coverage
    data = coverage.CoverageData(str(root / DATA))
    data.read()
    ok = passing(root)
    return {file: {line: {c.rpartition("|")[0] for c in contexts} & ok
                   for line, contexts in data.contexts_by_lineno(file).items()}
            for file in data.measured_files()}


def body_lines(source: str) -> set[int]:
    """The lines inside any function's body. The others run when the module is imported, before a test's context
    begins (and under xdist before coverage does), so no map holds them and they are not asked after."""
    lines = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            lines.update(range(node.body[0].lineno, node.end_lineno + 1))
    return lines


def tests_for(root: Path, target: str) -> list[str]:
    file, wanted = locate(root, target)
    lines = executed(root).get(str(file.resolve()), {})
    return sorted({t for line, tests in lines.items() if wanted is None or line in wanted for t in tests})


def unexecuted(root: Path) -> list[str]:
    reached = executed(root)
    files = [file for file in sorted((root / SOURCE).rglob("*.py")) if "_pb2" not in file.name]
    return report([(str(file.relative_to(root)), *_left(root, file, reached.get(str(file.resolve()), {})))
                   for file in files])


def _left(root: Path, file: Path, reached: dict) -> tuple[list[int], int]:
    """A file's statements no passing test executed, and how many statements it has."""
    held = statements(root, file)
    return sorted(line for line in held if not reached.get(line)), len(held)


def report(files: list[tuple[str, list[int], int]]) -> list[str]:
    """Each file with lines left unexecuted, as ranges, with how many of its lines they are; then the total."""
    out = [f"{name}: {', '.join(ranges(left))} ({len(left)} of {count})" for name, left, count in files if left]
    lines, held = sum(len(left) for _, left, _ in files), sum(count for _, _, count in files)
    return out + [f"total: {lines} of {held} lines inside functions, in {len(out)} of {len(files)} files"]


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    if argv[:1] == ["tests-for"] and len(argv) == 2:
        check_fresh(root)
        print("\n".join(tests_for(root, argv[1])))
    elif argv == ["unexecuted"]:
        check_fresh(root)
        print("\n".join(unexecuted(root)))
    else:
        raise SystemExit(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
