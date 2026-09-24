"""The one type a new store holds: the type that describes what a type is.

A schema artifact carries the type's human name as its title, an integer
version, and under `schema` a JSON Schema 2020-12 document plus the kb
keywords (`ref`, `parts`, `sections`, `summary`), which the JSON Schema
metaschema lets through as annotations.
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
