"""Content as a request carries it, converted: a whole artifact's content read as a tree holding only what a type
declares, a node's, an item's with its title as text and no name of its own; every problem found, each to be said of
whichever artifact the content turns out to be for."""
from dataclasses import dataclass

from kb import canonical, item_names, rules, settled
from kb.content import loads
from kb.contract import kb_pb2


def _leaves_nothing(title: str) -> str:
    return f"a title must leave something to make a name from; {title!r} leaves nothing"


@dataclass(frozen=True)
class Content:
    """Content as a request carries it: the tree read from it, and, when it cannot be taken, what is wrong with it,
    each as a place, a rule and a message, to be said of whichever artifact the content turns out to be for."""
    tree: object
    problems: tuple[tuple[str, str, str], ...] = ()

    def refusal(self, artifact: str) -> list[kb_pb2.Fault]:
        return [kb_pb2.Fault(artifact=artifact, place=path, rule=rule, message=message)
                for path, rule, message in self.problems]


def content(text: str, at_root: bool = True) -> Content:
    """Content read plainly, and, for a whole artifact, holding only what a type declares. The identity keys belong
    to an artifact's root, so a node inside it, a section with its title, is not held to them. Every problem found."""
    try:
        tree = canonical.entries(text) if at_root else loads(text)
    except canonical.NotCanonical as fault:
        return Content(None, ((fault.path, rules.CONTENT, str(fault)),))
    if not at_root:
        return Content(tree)
    problems = []
    for key in settled.IDENTITY:
        if key not in tree:
            continue
        if key == "title":
            message = f"a title is given alongside the content, never inside it; the content carried the title {tree[key]!r}"
        else:
            message = f"content holds only what the type declares; {key} is settled by the store, and the content carried {key}: {tree[key]!r}"
        problems.append((key, rules.IDENTITY, message))
    return Content(tree, tuple(problems))


def item(text: str) -> Content:
    """An item read plainly, never carrying its own name, which kb gives, and with its title, which its name is made
    from, as text. Only a set of named entries can carry a name or a title; an item of any other shape is left for
    its type to refuse."""
    read = content(text, at_root=False)
    if read.problems or not isinstance(read.tree, dict):
        return read
    if "id" in read.tree:
        return Content(read.tree, (("id", rules.IDENTITY,
            f"content holds only what the type declares; an item's id is settled by the store, and the content carried id: {read.tree['id']!r}"),))
    return _titled(read.tree)


def _titled(tree: dict) -> Content:
    """An item whose title, when it has one, is text whatever it was written as, as an artifact's is, and leaves a
    name to be made from it."""
    title = item_names.title(tree.get("title"))
    if title is None:
        return Content(tree)
    if not item_names.slug(title):
        return Content(tree, (("title", rules.TITLE, _leaves_nothing(title)),))
    return Content({**tree, "title": title})
