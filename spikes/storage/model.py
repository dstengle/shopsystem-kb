"""THROWAWAY. Neutral kinds for the conformance suite, shaped like shop-knowledge's real types."""

SIG = {"role": "client", "execution": "", "message": "a change"}


def link(*targets, many=False, parts=False, required=False):
    return {"type": "link", "targets": list(targets), "many": many, "parts": parts, "required": required}


def plain(kind="string", required=False, many=False):
    return {"type": kind, "required": required, "many": many}


TAG = {"name": "tag", "version": 1, "base": None, "fields": {}, "collections": {}, "sections": []}

SHOP_ARTIFACT = {
    "name": "shop-artifact", "version": 1, "base": None,
    "fields": {"owner": plain(), "status": plain(), "tags": link("tag", many=True)},
    "collections": {}, "sections": [],
}

DECISION = {
    "name": "decision", "version": 1, "base": "shop-artifact",
    "fields": {"supersedes": link("decision")},
    "collections": {"options": {"fields": {"title": plain(required=True), "body": plain("text")}, "collections": {}}},
    "sections": ["Purpose", "Rationale"],
}

WORK_ITEM = {
    "name": "work-item", "version": 1, "base": "shop-artifact",
    "fields": {"decisions": link("decision", many=True), "estimate": plain("number")},
    "collections": {}, "sections": [],
}

STEP = {"name": "step", "version": 1, "base": None, "fields": {"body": plain("text")}, "collections": {}, "sections": []}

PROCESS = {
    "name": "process", "version": 1, "base": None, "fields": {},
    "collections": {"steps": {"fields": {"title": plain(required=True), "body": plain("text"), "uses": link("step")},
                              "collections": {}}},
    "sections": [],
}

NOTE = {"name": "note", "version": 1, "base": None,
        "fields": {"about": link("process", parts=True), "body": plain("text")}, "collections": {}, "sections": []}

PAIR = {"name": "pair", "version": 1, "base": None,
        "fields": {"partner": link("pair", required=True)}, "collections": {}, "sections": []}

ALL = [TAG, SHOP_ARTIFACT, DECISION, WORK_ITEM, STEP, PROCESS, NOTE, PAIR]


def sections(purpose="Why we decided.", rationale="Because it holds up."):
    return [{"title": "Purpose", "body": purpose, "sections": []},
            {"title": "Rationale", "body": rationale, "sections": []}]


def create(kind, slug, title, content, key=None):
    change = {"op": "create", "kind": kind, "slug": slug, "title": title, "content": content}
    if key:
        change["key"] = key
    return change


def replace(id, content):
    return {"op": "replace", "id": id, "content": content}


def remove(id):
    return {"op": "remove", "id": id}
