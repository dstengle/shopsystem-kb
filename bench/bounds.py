"""Whether a store of N artifacts (30,000 by default) answers within the performance bounds the spec states:
`python bench/bounds.py [N]`. Exits 0 only when every bound holds.

The store is built in a fresh directory under the system's temp, removed after, and reached only through
`kb.client.connect`, as a client reaches it. The graph has about three links per artifact: a few hundred tags;
decisions, each linking to two tags and most to the decision before; work items, each linking to two decisions. It
is landed through Apply in sets of 100, and what a set cost to land is printed as the store grows. Every figure is
the median of 20 calls."""
import statistics
import sys
import tempfile
import time

from kb.client import connect
from kb.content import dumps
from kb.contract import kb_pb2

# spec/index.md, Bounds: "Performance bounds, at 30,000 artifacts: a summary read and a three-step traversal under
# 100 ms each; a single change under 50 ms; a set of 100 changes under 1 s." In milliseconds.
BOUNDS = {
    "summary read": 100,
    "three-step traversal": 100,
    "single change": 50,
    "set of 100 changes": 1000,
}
RUNS = 20
SET = 100
ACTOR = kb_pb2.Actor(role="bench")
WORDS = "restocking shelves pricing weekly review supplier till opening closing inventory".split()

TAG = {"title": "Tag", "version": 1,
       "schema": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]}}


def _links(targets: str, many: bool) -> dict:
    ref = {"targets": [targets], "cardinality": "many" if many else "one", "parts": False, "on_delete": "refuse"}
    if many:
        return {"type": "array", "items": {"type": "string"}, "ref": ref}
    return {"type": "string", "ref": ref}


DECISION = {"title": "Decision", "version": 1, "schema": {
    "type": "object",
    "properties": {"title": {"type": "string"}, "tags": _links("tag", True), "supersedes": _links("decision", False)},
    "required": ["title"],
    "sections": [{"title": "Purpose"}, {"title": "Rationale"}],
    "summary": ["supersedes", "tags"],
}}
WORK_ITEM = {"title": "Work item", "version": 1, "schema": {
    "type": "object",
    "properties": {"title": {"type": "string"}, "decisions": _links("decision", True)},
    "required": ["title"],
    "summary": ["decisions"],
}}


def answered(response):
    """The response, which must carry no fault: a figure over a refusal measures nothing."""
    if response.faults:
        raise SystemExit(f"refused: {list(response.faults)}")
    return response


def creation(kind: str, title: str, content: dict) -> kb_pb2.Operation:
    return kb_pb2.Operation(create=kb_pb2.Creation(type=kind, title=title, content=dumps(content)))


def applied(client, operations) -> kb_pb2.ApplyResponse:
    return answered(client.Apply(kb_pb2.ApplyRequest(operations=operations, actor=ACTOR, message="bench")))


def timed(call, runs: int = RUNS) -> float:
    """The median of the calls, in milliseconds."""
    samples = []
    for _ in range(runs):
        started = time.perf_counter()
        call()
        samples.append((time.perf_counter() - started) * 1000)
    return statistics.median(samples)


def shape(n: int) -> tuple[int, int, int]:
    """How many tags, decisions and work items a store of n artifacts holds."""
    tags = max(10, n // 100)
    decisions = n * 2 // 3 - tags
    return tags, decisions, n - tags - decisions


def operations(n: int):
    """Every creation that builds the store, in an order in which each link lands on something already made."""
    tags, decisions, items = shape(n)
    for i in range(tags):
        yield creation("tag", f"T {i}", {})
    for i in range(decisions):
        yield creation("decision", f"D {i}", {
            "sections": [{"title": "Purpose", "body": f"{WORDS[i % 10]} {WORDS[i * 7 % 10]}\n"},
                         {"title": "Rationale", "body": f"Because {i}.\n"}],
            "tags": [f"tag/t-{i % tags}", f"tag/t-{(i * 3 + 1) % tags}"],
            **({"supersedes": f"decision/d-{i - 1}"} if i % 10 else {}),
        })
    for i in range(items):
        yield creation("work-item", f"W {i}", {"decisions": [f"decision/d-{i % decisions}",
                                                             f"decision/d-{(i * 5 + 2) % decisions}"]})


def build(client, n: int) -> None:
    """The store landed in sets of 100, printing at every tenth of n the cost of the set that reached it."""
    pending, held, mark = [], 0, n // 10
    for operation in operations(n):
        pending.append(operation)
        if len(pending) == SET:
            started = time.perf_counter()
            applied(client, pending)
            cost = (time.perf_counter() - started) * 1000
            held += len(pending)
            pending = []
            if held % mark < SET or held == n:
                print(f"  building: a set of {SET} landing at {held} artifacts: {cost:.1f} ms", flush=True)
    if pending:
        applied(client, pending)


def figures(client, n: int) -> list[tuple[str, str, float]]:
    """Each figure measured: its bound (empty for one logged only), what it is, and its median in ms."""
    tags, decisions, items = shape(n)
    decision, tag, item = f"decision/d-{decisions // 2}", f"tag/t-{tags // 2}", f"work-item/w-{items // 2}"

    def summary(name):
        return lambda: answered(client.Read(kb_pb2.ReadRequest(locator=kb_pb2.Locator(id=name))))

    def walk(name, direction):
        return lambda: answered(client.Refs(kb_pb2.RefsRequest(
            locator=kb_pb2.Locator(id=name), depth=3, direction=direction)))

    made = iter(range(10**6))
    created = []

    def create():
        response = answered(client.Create(kb_pb2.CreateRequest(
            type="tag", title=f"Loose {next(made)}", content=dumps({}), actor=ACTOR, message="bench")))
        created.append(response.id)

    written = iter(created)
    removed = iter(created)
    sets = iter(range(10**6))
    measured = [
        ("summary read", f"summary read of {decision}", timed(summary(decision))),
        ("summary read", f"summary read of {tag}", timed(summary(tag))),
        ("three-step traversal", f"three steps out from {item}", timed(walk(item, kb_pb2.RefsRequest.OUT))),
        ("three-step traversal", f"three steps in from {decision}", timed(walk(decision, kb_pb2.RefsRequest.IN))),
        ("", f"three steps in from {tag} (logged only)", timed(walk(tag, kb_pb2.RefsRequest.IN))),
        ("single change", "Create of a tag nothing points at", timed(create)),
        ("single change", "Write of a tag nothing points at", timed(lambda: answered(client.Write(kb_pb2.WriteRequest(
            locator=kb_pb2.Locator(id=next(written)), content=dumps({}), actor=ACTOR, message="bench"))))),
        ("single change", "Delete of a tag nothing points at", timed(lambda: answered(client.Delete(
            kb_pb2.DeleteRequest(locator=kb_pb2.Locator(id=next(removed)), actor=ACTOR, message="bench"))))),
    ]

    def a_set():
        start = next(sets) * SET
        applied(client, [creation("tag", f"Batch {start + i}", {}) for i in range(SET)])
    measured.append(("set of 100 changes", f"Apply of {SET} creates", timed(a_set)))
    return measured


def main(n: int) -> int:
    with tempfile.TemporaryDirectory(prefix="kb-bench-") as root:
        client = connect(root)
        answered(client.Init(kb_pb2.InitRequest(root=root, actor=ACTOR)))
        for definition in (TAG, DECISION, WORK_ITEM):
            answered(client.Create(kb_pb2.CreateRequest(
                type="schema", title=definition["title"], actor=ACTOR, message="bench",
                content=dumps({key: value for key, value in definition.items() if key != "title"}))))
        started = time.perf_counter()
        build(client, n)
        print(f"built {n} artifacts in {time.perf_counter() - started:.1f} s; each figure the median of {RUNS} calls")
        missed = 0
        for bound, what, ms in figures(client, n):
            if not bound:
                print(f"  {what}: {ms:.2f} ms (no bound)")
                continue
            held = ms < BOUNDS[bound]
            missed += not held
            print(f"  {what}: {ms:.2f} ms, {bound} under {BOUNDS[bound]} ms: {'held' if held else 'MISSED'}")
    print("every bound held" if not missed else f"{missed} figure(s) missed a bound")
    return 1 if missed else 0


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 30_000))
