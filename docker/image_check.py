"""Whether kb's image serves a store beside its callers, as the README's "Running kb in Docker" says it does:
`make image-check`, run with the checkout's virtualenv. Exits 0 only when every check holds, each named on its own
line as it passes; a release that fails it does not ship (spec/index.md, Testing).

It builds the image from this checkout, under a tag of its own, and runs a throwaway compose project, under a project
name of its own, written in a temporary directory. Nothing reaches the daemon by a path on this machine: the daemon may
not see this machine's files (a development environment that is itself a container), so the seed and the caller's
program reach the containers as compose configs, whose content compose copies in. However the run ends, the project
is brought down with its volumes, and the image removed.
"""
import json
import secrets
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import kb
from kb.client import connect
from kb.content import dumps
from kb.contract import kb_pb2

CHECKOUT = Path(__file__).resolve().parent.parent
CALLER = Path(__file__).resolve().parent / "caller.py"
KB = Path(sys.executable).parent / "kb"
ROLE_LINE = "kb serve: refused: actor: a store can only be started under a role, named through KB_ACTOR"
PATIENCE = 180
DECISION_TYPE = {
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {"title": {"type": "string"}},
        "required": ["title"],
        "sections": [{"title": "Purpose"}, {"title": "Rationale"}],
    },
}
DECISION = {"sections": [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]}
LOST = "id: widget/lost\ntype: widget\nschema_version: 1\nrevision: 1\ntitle: Lost\n"


class Failed(Exception):
    """A check that did not hold, with what was seen."""


def main() -> int:
    began = time.monotonic()
    project = f"kb-image-check-{secrets.token_hex(4)}"
    image = f"shopsystem-kb:check-{project[-8:]}"
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    with tempfile.TemporaryDirectory(prefix="kb-image-check-") as scratch:
        compose = Compose(project, Path(scratch) / "compose.yaml")
        try:
            build(image)
            compose.write(project_file(image, seeds(Path(scratch))))
            checks(compose)
        except Failed as failed:
            print(f"FAILED\t{failed}", file=sys.stderr)
            return 1
        finally:
            compose.down()
            subprocess.run(["docker", "image", "rm", "-f", image], capture_output=True)
    print(f"image check passed in {time.monotonic() - began:.0f} s")
    return 0


def build(image: str) -> None:
    """The image built from this checkout, whose context the client sends to the daemon."""
    built = subprocess.run(["docker", "build", "-q", "-t", image, str(CHECKOUT)], capture_output=True, text=True)
    holds(built.returncode == 0, "the image builds", built.stderr)
    passed(f"the image builds from the checkout ({image})")


def seeds(scratch: Path) -> dict[str, dict[str, str]]:
    """Two seeds, each a map of its files' places to their text: one exported from a store holding a type and an
    artifact of it, and the same with a file whose kind has no type, which checks unclean."""
    source, exported = scratch / "source", scratch / "seed"
    source.mkdir()
    kb.init(source, "operator")
    client = connect(source)
    signed = kb_pb2.Signature(role="operator", message="Seed the image check")
    for kind, title, content in (("schema", "Decision", DECISION_TYPE),
                                 ("decision", "Price reviews happen weekly", DECISION)):
        created = client.Create(kb_pb2.CreateRequest(kind=kind, title=title, content=dumps(content), signature=signed))
        holds(created.WhichOneof("outcome") == "result", "the seed is made", str(created))
    ran = subprocess.run([str(KB), "export", str(exported)], cwd=source, capture_output=True, text=True)
    holds(ran.returncode == 0, "the seed is exported", ran.stderr)
    clean = {str(f.relative_to(exported)): f.read_text() for f in sorted(exported.rglob("*.yaml"))}
    return {"seed": clean, "refused-seed": {**clean, "widget/lost.yaml": LOST}}


def project_file(image: str, seeded: dict[str, dict[str, str]]) -> dict:
    """The compose project: `kb` as the README's example has it, but on the image built from the checkout; `agent`, the same image
    running the caller's program with the connection given by a compose config; a service for each seed; `bare`, an
    empty volume with no role named; `locked`, a store its user cannot write."""
    configs = {"kb-connection": {"content": "address: kb:50051\n"}, "caller": {"content": CALLER.read_text()}}
    services = {
        "kb": {"image": image, "environment": {"KB_ACTOR": "operator"}, "volumes": ["kb-store:/data"]},
        "agent": {
            "image": image, "entrypoint": ["python", "/caller/caller.py"], "environment": {"KB_ROOT": "/kb-connection"},
            "configs": [{"source": "kb-connection", "target": "/kb-connection/kb/server.yaml"},
                        {"source": "caller", "target": "/caller/caller.py"}],
            "depends_on": {"kb": {"condition": "service_healthy"}},
        },
        "bare": {"image": image, "volumes": ["bare-store:/data"]},
        "locked": {"image": image, "environment": {"KB_ACTOR": "operator"}, "volumes": ["locked-store:/data"]},
    }
    for seed, files in seeded.items():
        services[seed] = {"image": image, "environment": {"KB_ACTOR": "operator"}, "volumes": ["kb-store:/data"],
                          "configs": []}
        for n, (place, text) in enumerate(files.items()):
            configs[f"{seed}-{n}"] = {"content": text}
            services[seed]["configs"].append({"source": f"{seed}-{n}", "target": f"/seed/{place}"})
    escaped = {name: {"content": c["content"].replace("$", "$$")} for name, c in configs.items()}
    return {"services": services, "configs": escaped,
            "volumes": {"kb-store": {}, "bare-store": {}, "locked-store": {}}}


def checks(compose: "Compose") -> None:
    refused_seed_leaves_no_store(compose)
    seed_lands(compose)
    up_becomes_healthy(compose)
    created = a_caller_reads_and_changes(compose)
    validate_answers(compose)
    a_stop_and_a_start_keep_the_store(compose, created)
    no_role_on_an_empty_volume(compose)
    a_store_its_user_cannot_write(compose)


def refused_seed_leaves_no_store(compose: "Compose") -> None:
    ran = compose.run("refused-seed", "init", "/data", "--seed", "/seed")
    holds(ran.returncode == 2, "a refused seed exits 2", ran)
    holds(any(line.startswith("error\twidget/lost") for line in ran.stdout.splitlines()),
          "a refused seed's report is shown", ran)
    holds("kb init: refused: " in ran.stderr, "a refused seed is refused", ran)
    listed = compose.run("kb", "-A", "/data", entrypoint="ls")
    holds((listed.returncode, listed.stdout) == (0, ""), "a refused seed leaves the volume empty", listed)
    passed("kb init --seed with a seed that checks unclean is refused, its report shown, the volume holding no store")


def seed_lands(compose: "Compose") -> None:
    ran = compose.run("seed", "init", "/data", "--seed", "/seed")
    holds(ran.returncode == 0, "kb init --seed lands the seed", ran)
    listed = compose.run("kb", "-A", "/data", "/data/kb", entrypoint="ls")
    holds(".kb-starting" not in listed.stdout and "store.yaml" in listed.stdout, "the volume holds the store", listed)
    passed("kb init --seed lands a small seed in the volume")


def up_becomes_healthy(compose: "Compose") -> None:
    ran = compose.call("up", "-d", "--wait", "--wait-timeout", "60", "kb")
    holds(ran.returncode == 0, "up becomes healthy", ran)
    logs = compose.call("logs", "--no-log-prefix", "kb")
    holds("serving\t0.0.0.0:50051" in logs.stdout, "the log says where it serves", logs)
    passed("docker compose up serves the store and becomes healthy, saying serving\t0.0.0.0:50051")


def a_caller_reads_and_changes(compose: "Compose") -> str:
    ran = compose.run("agent", "change")
    holds(ran.returncode == 0, "a caller reads and changes through kb:50051", ran)
    created = ran.stdout.strip()
    holds(created.startswith("note/"), "the caller's change is named", ran)
    passed(f"a second container reaches kb:50051 through a compose config, reads the seed and creates {created}")
    return created


def validate_answers(compose: "Compose") -> None:
    ran = compose.run("kb", "validate")
    holds((ran.returncode, ran.stdout) == (0, ""), "docker compose run --rm kb validate answers clean", ran)
    passed("docker compose run --rm kb validate answers, while the store is served")
    ran = compose.call("exec", "-T", "kb", "kb", "validate")
    holds((ran.returncode, ran.stdout) == (0, ""), "docker compose exec kb kb validate answers clean", ran)
    passed("docker compose exec kb kb validate answers")


def a_stop_and_a_start_keep_the_store(compose: "Compose", created: str) -> None:
    ran = compose.call("stop", "kb")
    holds(ran.returncode == 0, "docker compose stop stops kb", ran)
    stopped = compose.call("ps", "-a", "--format", "{{.ExitCode}}", "kb")
    holds(stopped.stdout.strip() == "0", "kb exits 0 when stopped", stopped)
    ran = compose.call("up", "-d", "--wait", "--wait-timeout", "60", "--no-recreate", "kb")
    holds(ran.returncode == 0, "kb is healthy again after a start", ran)
    ran = compose.run("agent", "read", created)
    holds(ran.returncode == 0 and ran.stdout.startswith(f"{created}\t"), "the store keeps the change", ran)
    passed("a stop (exit 0) and a start keep the store, the caller's change read back through the server")


def no_role_on_an_empty_volume(compose: "Compose") -> None:
    ran = compose.run("bare")
    holds(ran.returncode == 2, "an empty volume with no KB_ACTOR exits 2", ran)
    holds(ROLE_LINE in ran.stderr.splitlines() and "Traceback" not in ran.stderr, "the role's line is said", ran)
    listed = compose.run("bare", "-A", "/data", entrypoint="ls")
    holds((listed.returncode, listed.stdout) == (0, ""), "the empty volume still holds no store", listed)
    passed("an empty volume with no KB_ACTOR exits 2 with the role's line, holding no store")


def a_store_its_user_cannot_write(compose: "Compose") -> None:
    ran = compose.run("locked", "init", "/data")
    holds(ran.returncode == 0, "a store is started in the volume", ran)
    ran = compose.run("locked", "-R", "root:root", "/data", entrypoint="chown", user="root")
    holds(ran.returncode == 0, "the volume is made root's", ran)
    ran = compose.run("locked")
    refusal = [line for line in ran.stderr.splitlines() if line.startswith("kb serve: refused: unreadable: ")]
    holds(ran.returncode == 2 and refusal and "/data/kb/store.sqlite3" in refusal[0], "unreadable, naming it", ran)
    holds("Traceback" not in ran.stderr, "no traceback", ran)
    passed("a store its user cannot write exits 2 with unreadable, naming the database, and no traceback")


class Compose:
    """The throwaway project, called through `docker compose` under its own name."""

    def __init__(self, project: str, file: Path):
        self.project, self.file = project, file

    def write(self, content: dict) -> None:
        self.file.write_text(json.dumps(content, indent=2))

    def call(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["docker", "compose", "-p", self.project, "-f", str(self.file), *args],
                              capture_output=True, text=True, timeout=PATIENCE)

    def run(self, service: str, *args: str, entrypoint: str = "", user: str = "") -> subprocess.CompletedProcess:
        """`docker compose run --rm` of the service, with its entry point or user overridden when asked."""
        options = (["--entrypoint", entrypoint] if entrypoint else []) + (["--user", user] if user else [])
        return self.call("run", "--rm", "-T", *options, service, *args)

    def down(self) -> None:
        """The project brought down with its volumes, and anything of it left running removed."""
        if not self.file.exists():
            return
        subprocess.run(["docker", "compose", "-p", self.project, "-f", str(self.file), "down", "-v",
                        "--remove-orphans", "--timeout", "5"], capture_output=True)
        label = f"label=com.docker.compose.project={self.project}"
        for kind in ("container", "volume", "network"):
            left = subprocess.run(["docker", kind, "ls", "-q", *(["-a"] if kind == "container" else []),
                                   "--filter", label], capture_output=True, text=True).stdout.split()
            if left:
                subprocess.run(["docker", kind, "rm", *(["-f"] if kind != "network" else []), *left],
                               capture_output=True)


def holds(condition, what: str, seen) -> None:
    if not condition:
        if isinstance(seen, subprocess.CompletedProcess):
            seen = f"exit {seen.returncode}\nstdout:\n{seen.stdout}\nstderr:\n{seen.stderr}"
        raise Failed(f"{what}\n{seen}")


def passed(what: str) -> None:
    print(f"ok\t{what}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
