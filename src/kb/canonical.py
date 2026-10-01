"""Canonical YAML: the one serialization kb writes, and the one reading of YAML kb does. YAML 1.2 throughout.

kb is the only writer, so loading needs no round-trip preservation.
"""
import io

from ruamel.yaml import YAML, events, nodes, tokens
from ruamel.yaml.constructor import SafeConstructor
from ruamel.yaml.error import YAMLError
from ruamel.yaml.representer import SafeRepresenter

class Prose(str):
    """A prose body. Written as a literal block, however short."""


class _Representer(SafeRepresenter):
    def ignore_aliases(self, data):
        """A value used twice is written out twice, never as an anchor and an alias."""
        return True


def _represent_mapping(representer, mapping):
    """Every value under a `body` key is prose."""
    items = [
        (key, Prose(value) if key == "body" and isinstance(value, str) else value)
        for key, value in mapping.items()
    ]
    return representer.represent_mapping("tag:yaml.org,2002:map", items)


def _represent_prose(representer, value):
    """Prose as a literal block. A line ending in a space is refused rather than written: the store writes every
    piece of prose one way."""
    for number, line in enumerate(value.split("\n"), start=1):
        if line.endswith(" "):
            raise NotCanonical(
                "every piece of prose is written as a block, and this prose could not be written back as one; "
                f"its line {number} ends in a space"
            )
    return representer.represent_scalar("tag:yaml.org,2002:str", str(value), style="|")


def _represent_str(representer, value):
    style = "|" if "\n" in value else None
    return representer.represent_scalar("tag:yaml.org,2002:str", value, style=style)


_Representer.add_representer(dict, _represent_mapping)
_Representer.add_representer(Prose, _represent_prose)
_Representer.add_representer(str, _represent_str)


class _Constructor(SafeConstructor):
    """A value is read as written: one that looks like a date or a time is the text it was written as, and a character
    written as two escapes, one for each half, is that one character, in a key as in a value."""

    def construct_scalar(self, node):
        value = super().construct_scalar(node)
        return _joined(value) if isinstance(value, str) else value


_Constructor.add_constructor("tag:yaml.org,2002:timestamp", SafeConstructor.construct_yaml_str)


def _yaml() -> YAML:
    """The pure-Python safe loader and emitter, YAML 1.2. Never the C one, which is YAML 1.1."""
    yaml = YAML(typ="safe", pure=True)
    yaml.Representer = _Representer
    yaml.Constructor = _Constructor
    yaml.default_flow_style = False
    yaml.allow_unicode = True
    yaml.width = 2**31 - 1
    yaml.indent(mapping=2, sequence=4, offset=2)
    return yaml


class NotCanonical(ValueError):
    """YAML that is not read plainly as written. The message says which rule it breaks; `path` names the place, if any."""

    def __init__(self, message: str, path: str = ""):
        super().__init__(message)
        self.path = path


def check(text: str) -> None:
    """The one check of plain reading, run on content as it arrives and on every file kb is about to write.

    No directive, no tags, no anchors or aliases, exactly one document, every entry named once. Raises NotCanonical naming the
    first rule broken.
    """
    try:
        _no_directive(text)
        parsed = list(_yaml().parse(text))
    except YAMLError as error:
        raise NotCanonical(_unreadable(error)) from None
    if any(getattr(event, "tag", None) is not None for event in parsed):
        raise NotCanonical("content is read plainly as written and carries no tags")
    if any(getattr(event, "anchor", None) is not None for event in parsed):
        raise NotCanonical(
            "content is read exactly as written and nothing in it stands in for a value written somewhere else"
        )
    if sum(isinstance(event, events.DocumentStartEvent) for event in parsed) > 1:
        raise NotCanonical("content holds exactly one document")
    composed = _yaml().compose(text)
    _named_once(composed, ())
    _held_as_text(composed, ())


def _no_directive(text: str) -> None:
    """Content cannot choose the rules it is read by: a %YAML or %TAG line is refused before anything reads past it."""
    for token in _yaml().scan(text):
        if isinstance(token, tokens.DirectiveToken):
            value = ".".join(map(str, token.value)) if token.name == "YAML" else " ".join(token.value)
            raise NotCanonical(
                "content is read plainly as written and opens with no declaration of its format; "
                f"line {token.start_mark.line + 1} declares %{token.name} {value}"
            )
        if not isinstance(token, (tokens.StreamStartToken, tokens.DirectiveToken)):
            return


def _named_once(node, place: tuple) -> None:
    """Every entry of every mapping is named once and only once. Raises NotCanonical at the second of a pair."""
    if isinstance(node, nodes.MappingNode):
        seen = set()
        for key, value in node.value:
            if key.value in seen:
                raise NotCanonical(
                    f"an entry is named once and only once; {_label(key)!r} is named again at line {key.start_mark.line + 1}",
                    "/".join((*place, _label(key))),
                )
            seen.add(key.value)
            _named_once(value, (*place, _label(key)))
    elif isinstance(node, nodes.SequenceNode):
        for index, item in enumerate(node.value):
            _named_once(item, (*place, str(index)))


def _held_as_text(node, place: tuple) -> None:
    """Every scalar is text once each pair of escapes for the two halves of a character is read as that character: an
    escape for half of a character alone (\\ud800) reads as a value no text can hold, and nothing downstream could
    write or fingerprint it. Raises NotCanonical naming the place."""
    if isinstance(node, nodes.ScalarNode):
        try:
            _joined(node.value)
        except UnicodeDecodeError:
            raise NotCanonical(
                "it is not YAML that can be read: it holds an escape for half of a character, which no text can hold",
                "/".join(place),
            ) from None
    elif isinstance(node, nodes.MappingNode):
        for key, value in node.value:
            _held_as_text(key, place)
            _held_as_text(value, (*place, _label(key)))
    elif isinstance(node, nodes.SequenceNode):
        for index, item in enumerate(node.value):
            _held_as_text(item, (*place, str(index)))


def _label(key) -> str:
    """A key as a place names it: its pairs of halves read as one character, and a half standing alone written as its
    escape, so that the place is always text."""
    try:
        return _joined(str(key.value))
    except UnicodeDecodeError:
        return "".join(f"\\u{ord(each):04x}" if 0xD800 <= ord(each) <= 0xDFFF else each for each in str(key.value))


def _joined(value: str) -> str:
    """The text with each pair of halves of a character, as YAML 1.2 reads two escapes, read as that one character.
    Raises UnicodeDecodeError when a half stands alone, in either order."""
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return value.encode("utf-16-le", "surrogatepass").decode("utf-16-le")
    return value


def dump(artifact: dict) -> str:
    """Block style, keys in the order given, prose as literal blocks, sequences indented under their key, no line folded.

    The text is checked before it is handed back, so nothing kb writes can differ from what kb accepts.
    """
    stream = io.StringIO()
    _yaml().dump(artifact, stream)
    text = stream.getvalue()
    check(text)
    return text


def load(text: str):
    """Plain YAML 1.2: checked, then read. Text that cannot be read raises NotCanonical, never the parser's own error."""
    check(text)
    try:
        return _yaml().load(text)
    except YAMLError as error:
        raise NotCanonical(_unreadable(error)) from None


def entries(text: str) -> dict:
    """Plain YAML 1.2 that is a set of named entries, as an artifact always is: read as `load` reads it. Text that is
    anything else, a list, a single value or nothing, raises NotCanonical saying what it is."""
    loaded = load(text)
    if not isinstance(loaded, dict):
        raise NotCanonical(f"content is a set of named entries; this is {_shape(loaded)}")
    return loaded


def _shape(value) -> str:
    if value is None:
        return "nothing at all"
    if isinstance(value, list):
        return "a list"
    return f"the single value {value!r}"


def _unreadable(error: YAMLError) -> str:
    mark = getattr(error, "problem_mark", None)
    where = f" at line {mark.line + 1}" if mark is not None else ""
    return f"it is not YAML that can be read: {getattr(error, 'problem', None) or error}{where}"
