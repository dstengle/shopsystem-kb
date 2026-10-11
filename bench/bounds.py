"""Whether a store of N artifacts (30,000 by default) answers within the performance bounds the spec states:
`python bench/bounds.py [N]`. Exits 0 only when every bound holds.

The store is built in a fresh directory under the system's temp, removed after, and reached only through
`kb.client.connect`, as a client reaches it. Every artifact is named by an IRI under its type's, the types defined at
IRIs under `https://bench.example/kb/`. The graph has about three links per artifact: a few hundred tags;
decisions, each linking to two tags and most to the decision before; work items, each linking to two decisions. It
is landed through BatchCreate in sets of 100, and what a set cost to land is printed as the store grows. Every figure is
the median of 20 calls."""
import statistics
import sys
import tempfile
import time

import kb
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
SIGNATURE = kb_pb2.Signature(role="bench", message="bench")
WORDS = "restocking shelves pricing weekly review supplier till opening closing inventory".split()

TYPES_AT = "https://bench.example/kb/"
TYPE_OF_TYPES = "https://missingmass.io/kb/type"


def kind(name: str) -> str:
    """The IRI of the type of a kind given by its short name."""
    return TYPES_AT + name


def iri(name: str, path: str) -> str:
    """The IRI of an artifact of a kind, under its type's."""
    return f"{kind(name)}/{path}"


TAG = {"title": "Tag", "version": 1,
       "schema": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]}}


def _links(targets: str, many: bool) -> dict:
    ref = {"targets": [kind(targets)], "cardinality": "many" if many else "one", "parts": False, "on_delete": "refuse"}
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
    """What the call gave, its result, which must be no refusal: a figure over a refusal measures nothing."""
    if response.WhichOneof("outcome") != "result":
        raise SystemExit(f"refused: {list(response.refusal.faults)}")
    return response.result


def creation(name: str, path: str, title: str, content: dict) -> kb_pb2.CreateItem:
    """A create of a kind's first version, at the path given under its type's IRI."""
    return kb_pb2.CreateItem(id=iri(name, path), type=f"{kind(name)}@1", title=title, content=dumps(content))


def applied(client, creates) -> kb_pb2.BatchCreated:
    return answered(client.BatchCreate(kb_pb2.BatchCreateRequest(items=creates, signature=SIGNATURE)))


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
        yield creation("tag", f"t-{i}", f"T {i}", {})
    for i in range(decisions):
        yield creation("decision", f"d-{i}", f"D {i}", {
            "sections": [{"title": "Purpose", "body": f"{WORDS[i % 10]} {WORDS[i * 7 % 10]}\n"},
                         {"title": "Rationale", "body": f"Because {i}.\n"}],
            "tags": [iri("tag", f"t-{i % tags}"), iri("tag", f"t-{(i * 3 + 1) % tags}")],
            **({"supersedes": iri("decision", f"d-{i - 1}")} if i % 10 else {}),
        })
    for i in range(items):
        yield creation("work-item", f"w-{i}", f"W {i}", {"decisions": [
            iri("decision", f"d-{i % decisions}"), iri("decision", f"d-{(i * 5 + 2) % decisions}")]})


def build(client, n: int) -> None:
    """The store landed in sets of 100, printing at every tenth of n the cost of the set that reached it."""
    pending, held, mark = [], 0, max(SET, n // 10)
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
    decision, tag = iri("decision", f"d-{decisions // 2}"), iri("tag", f"t-{tags // 2}")
    item = iri("work-item", f"w-{items // 2}")

    def summary(name):
        return lambda: answered(client.Read(kb_pb2.ReadRequest(locator=kb_pb2.Locator(id=name))))

    def walk(name, direction):
        return lambda: answered(client.Follow(kb_pb2.FollowRequest(
            locator=kb_pb2.Locator(id=name), depth=3, direction=direction)))

    made = iter(range(10**6))
    created = []

    def create():
        created.append(answered(client.Create(kb_pb2.CreateRequest(
            id=iri("tag", f"loose-{next(made)}"), type=f"{kind('tag')}@1", title="Loose", content=dumps({}),
            signature=SIGNATURE))).id)

    written = iter(created)
    removed = iter(created)
    sets = iter(range(10**6))
    measured = [
        ("summary read", f"summary read of {decision}", timed(summary(decision))),
        ("summary read", f"summary read of {tag}", timed(summary(tag))),
        ("three-step traversal", f"three steps out from {item}", timed(walk(item, kb_pb2.FollowRequest.OUT))),
        ("three-step traversal", f"three steps in from {decision}", timed(walk(decision, kb_pb2.FollowRequest.IN))),
        ("", f"three steps in from {tag} (logged only)", timed(walk(tag, kb_pb2.FollowRequest.IN))),
        ("single change", "Create of a tag nothing points at", timed(create)),
        ("single change", "Replace of a tag nothing points at", timed(lambda: answered(client.Replace(
            kb_pb2.ReplaceRequest(locator=kb_pb2.Locator(id=next(written)), content=dumps({}), signature=SIGNATURE))))),
        ("single change", "Remove of a tag nothing points at", timed(lambda: answered(client.Remove(
            kb_pb2.RemoveRequest(locator=kb_pb2.Locator(id=next(removed)), signature=SIGNATURE))))),
    ]

    def a_set():
        start = next(sets) * SET
        applied(client, [creation("tag", f"batch-{start + i}", f"Batch {start + i}", {}) for i in range(SET)])
    measured.append(("set of 100 changes", f"BatchCreate of {SET} creates", timed(a_set)))
    return measured


def main(n: int) -> int:
    if n < SET:
        raise SystemExit(f"a store of at least {SET} artifacts holds the graph measured; {n} is too few")
    with tempfile.TemporaryDirectory(prefix="kb-bench-") as root:
        kb.init(root, "bench")
        client = connect(root)
        for name, definition in (("tag", TAG), ("decision", DECISION), ("work-item", WORK_ITEM)):
            answered(client.Create(kb_pb2.CreateRequest(
                id=kind(name), type=f"{TYPE_OF_TYPES}@1", title=definition["title"], signature=SIGNATURE,
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
