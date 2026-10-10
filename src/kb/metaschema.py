"""The one type a new store holds: the type that describes what a type is, written at `names.TYPES`
(https://missingmass.io/kb/type) at its first version.

A type carries its human name as its title, an integer version, and under
`schema` a JSON Schema 2020-12 document plus the kb keywords (`ref`,
`parts`, `sections`, `summary`), which the JSON Schema metaschema lets
through as annotations.
"""

METASCHEMA = {
    "title": "Schema",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "version": {"type": "integer"},
            "schema": {"$ref": "https://json-schema.org/draft/2020-12/schema"},
        },
        "required": ["title", "version", "schema"],
    },
}
