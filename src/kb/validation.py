"""Schema validation: the type's JSON Schema composed with kb's own structural rules, checked in one pass.

The other kb keywords (references, required sections in order, id uniqueness) are checked in code in later slices.
"""
from jsonschema import Draft202012Validator

from kb.contract import kb_pb2

SECTION = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "body": {"type": "string"},
        "sections": {"type": "array", "items": {"$ref": "#/$defs/kb-section"}},
    },
    "required": ["title", "body"],
    "additionalProperties": False,
}

STRUCTURE = {"properties": {"sections": {"type": "array", "items": {"$ref": "#/$defs/kb-section"}}}}


def compose(schema: dict) -> dict:
    """One effective schema: the type's, with kb's structural rules beside it under allOf.

    The type stays the root, so its own `#` references still resolve; kb's shapes sit under `$defs/kb-*`.
    """
    return {
        **schema,
        "allOf": [*schema.get("allOf", []), STRUCTURE],
        "$defs": {**schema.get("$defs", {}), "kb-section": SECTION},
    }


def validate(artifact_id: str, content: dict, schema: dict) -> list[kb_pb2.Fault]:
    """Every violation, as artifact, path, rule, message."""
    return [
        kb_pb2.Fault(
            artifact=artifact_id,
            path="/".join(str(step) for step in error.absolute_path),
            rule=error.validator,
            message=error.message,
        )
        for error in Draft202012Validator(compose(schema)).iter_errors(content)
    ]
