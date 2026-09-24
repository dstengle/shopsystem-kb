"""Schema validation: JSON Schema 2020-12 over an artifact, then the shape of its sections. The other kb keywords are checked in later slices."""
from jsonschema import Draft202012Validator

from kb.contract import kb_pb2

SECTION_KEYS = ("title", "body", "sections")


def validate(artifact_id: str, content: dict, schema: dict) -> list[kb_pb2.Fault]:
    """Every violation, as artifact, path, rule, message."""
    faults = [
        kb_pb2.Fault(
            artifact=artifact_id,
            path="/".join(str(step) for step in error.absolute_path),
            rule=error.validator,
            message=error.message,
        )
        for error in Draft202012Validator(schema).iter_errors(content)
    ]
    return faults + _section_faults(artifact_id, content.get("sections", []), "sections")


def _section_faults(artifact_id: str, sections: list, at: str) -> list[kb_pb2.Fault]:
    """A section holds exactly its title, its body and the sections inside it."""
    faults = []
    for index, section in enumerate(sections):
        here = f"{at}/{index}"
        for key in section:
            if key not in SECTION_KEYS:
                faults.append(kb_pb2.Fault(
                    artifact=artifact_id, path=f"{here}/{key}", rule="section",
                    message=f"a section holds exactly its title, its body and the sections inside it; {key} is none of these",
                ))
        faults += _section_faults(artifact_id, section.get("sections", []), f"{here}/sections")
    return faults
