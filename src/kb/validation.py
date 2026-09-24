"""Schema validation: JSON Schema 2020-12 over an artifact's content. The kb keywords are checked in later slices."""
from jsonschema import Draft202012Validator

from kb.contract import kb_pb2


def validate(artifact_id: str, content: dict, schema: dict) -> list[kb_pb2.Fault]:
    """Every violation, as artifact, path, rule, message."""
    return [
        kb_pb2.Fault(
            artifact=artifact_id,
            path="/".join(str(step) for step in error.absolute_path),
            rule=error.validator,
            message=error.message,
        )
        for error in Draft202012Validator(schema).iter_errors(content)
    ]
