"""What a locator may say: a kind and a plain name, and a plain place inside it. Checked before any file is resolved."""
import re

from kb.contract import kb_pb2

PLAIN = r"[a-z0-9]+(?:-[a-z0-9]+)*"
ID = re.compile(rf"^{PLAIN}/{PLAIN}$")
PLACE = re.compile(rf"^(?:{PLAIN}(?:/{PLAIN})*)?$")


def faults(locator) -> list[kb_pb2.Fault]:
    """Every way the locator fails the grammar; empty when it is plain."""
    found = []
    if not ID.fullmatch(locator.id):
        found.append(kb_pb2.Fault(
            artifact=locator.id, rule="locator",
            message=f"a name is a kind and a plain name of lower-case letters, digits and single hyphens, never a path; {locator.id!r} is not",
        ))
    if not PLACE.fullmatch(locator.path):
        found.append(kb_pb2.Fault(
            artifact=locator.id, path=locator.path, rule="locator",
            message=f"a place inside an artifact is named by parts of the same plain alphabet, or a collection and an item in it; {locator.path!r} is not",
        ))
    return found
