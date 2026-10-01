"""Pins the whole of kb.v1: every message field's name, number, type and label, every enum's values and numbers, and
the service's methods with their input and output types, against tests/contract_v1.golden. A change to any of them
is a change to the published contract, and is made by changing the golden file with it."""
from pathlib import Path

from google.protobuf import descriptor_pb2

from kb.contract import kb_pb2

GOLDEN = Path(__file__).with_name("contract_v1.golden")
TYPES = {number: name[len("TYPE_"):].lower() for name, number in descriptor_pb2.FieldDescriptorProto.Type.items()}


def _enum(enum, indent):
    yield f"{indent}enum {enum.name}"
    for value in enum.values:
        yield f"{indent}  {value.name} = {value.number}"


def _message(message, indent=""):
    yield f"{indent}message {message.name}"
    for field in message.fields:
        kind = field.message_type.full_name if field.message_type else field.enum_type.full_name if field.enum_type \
            else TYPES[field.type]
        label = "repeated" if field.is_repeated else "singular"
        oneof = f" oneof {field.containing_oneof.name}" if field.containing_oneof else ""
        yield f"{indent}  {field.name} = {field.number} {label} {kind}{oneof}"
    for nested in message.nested_types:
        yield from _message(nested, indent + "  ")
    for enum in message.enum_types:
        yield from _enum(enum, indent + "  ")


def _service(service):
    yield f"service {service.name}"
    for method in service.methods:
        yield f"  rpc {method.name}({method.input_type.full_name}) returns ({method.output_type.full_name})"


def render():
    descriptor = kb_pb2.DESCRIPTOR
    lines = [f"package {descriptor.package}"]
    for enum in descriptor.enum_types_by_name.values():
        lines.extend(_enum(enum, ""))
    for message in descriptor.message_types_by_name.values():
        lines.extend(_message(message))
    for service in descriptor.services_by_name.values():
        lines.extend(_service(service))
    return "\n".join(lines) + "\n"


def test_the_whole_of_the_v1_descriptor_is_the_golden_file():
    assert render() == GOLDEN.read_text()
