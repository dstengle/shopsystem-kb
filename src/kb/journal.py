"""The history's entries: each stamped by the clock and given its id here, and fingerprinted from the canonical text of
what was written. Nothing here writes: an entry rides with the set handed to the port, and lands with it."""
import hashlib
import re
from datetime import datetime, timezone
from typing import Callable, NamedTuple

from kb import canonical, values
from kb.port import Entry, Port
from kb.signatures import Signed

Clock = Callable[[], datetime]


class Stamp(NamedTuple):
    """An entry's moment, the clock's, in UTC, and its id, free in the history and in the set it belongs to."""
    at: datetime
    id: str


def stamps(store: Port, count: int, clock: Clock | None = None) -> list[Stamp]:
    """The stamps of a set's `count` entries, in order: each moment read from the clock, then given its id. Settled
    before the set lands, so a clock that raises leaves nothing written."""
    return minted(store, moments(count, clock))


def moments(count: int, clock: Clock | None = None) -> list[datetime]:
    """The moments of a set's `count` entries, in order, each read from the clock once."""
    return [_stamp(clock) for _ in range(count)]


def minted(store: Port, moments: list[datetime]) -> list[Stamp]:
    """Each moment given the next id free at it, after every id the history holds there and every one minted before
    it in the set; minted again, from the same moments, when a set is drafted again."""
    last: dict[str, int] = {}
    settled: list[Stamp] = []
    for at in moments:
        moment = _moment(at)
        last[moment] = (last[moment] if moment in last else _last_seq(store, at)) + 1
        settled.append(Stamp(at, _entry_id(at, last[moment])))
    return settled


def first(clock: Clock | None = None) -> Stamp:
    """The stamp of a new store's first entry, which nothing in its history comes before."""
    at = _stamp(clock)
    return Stamp(at, _entry_id(at, 1))


def _stamp(clock: Clock | None) -> datetime:
    """The moment an entry is stamped with: the clock given, read now, or, with none, the machine's clock, read
    here and nowhere else; in UTC, a moment given with no zone read as UTC."""
    return values.in_utc(datetime.now(timezone.utc) if clock is None else clock())


def _moment(at: datetime) -> str:
    """The moment as an id begins with it."""
    return at.strftime("%Y%m%dT%H%M%S%fZ")


def _entry_id(at: datetime, seq: int) -> str:
    """The one place an entry's id is made: its moment, then its seq among the entries stamped with that moment."""
    return f"{_moment(at)}-{seq}"


_ID = re.compile(r"(?P<moment>.+)-(?P<seq>\d+)")


def _parts(entry_id: str) -> tuple[str, int] | None:
    """The one reading of an entry's id: its moment, and its seq among the entries stamped with that moment; None
    for a name that is not an id."""
    found = _ID.fullmatch(entry_id)
    return (found["moment"], int(found["seq"])) if found else None


def _last_seq(store: Port, at: datetime) -> int:
    """The highest seq an entry the history holds at this moment takes, or 0 when none does; asked once per moment
    in a set, whose own ids are counted on from it."""
    moment = _moment(at)
    parts = [_parts(entry_id) for entry_id in store.entry_ids(at)]
    return max((found[1] for found in parts if found and found[0] == moment), default=0)


def digest(artifact: dict) -> str:
    """The fingerprint of an artifact as the store holds it: of its canonical text, as its entry's was."""
    return fingerprint(canonical.dump(artifact))


def fingerprint(text: str) -> str:
    """The fingerprint of canonical text: sha256 of the bytes it is written as."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def change(*, signed: Signed, op: str, artifact: str, path: str, revision: int, schema_version: int,
           text: str | None, stamp: Stamp, batch: str = "") -> Entry:
    """The entry of one change, under its settled stamp. A change made alone names itself as its batch. The
    fingerprint is of the text the change leaves; a removal leaves none, so its entry's fingerprint is empty."""
    record = {
        "id": stamp.id,
        "at": stamp.at.isoformat(),
        "actor": {"role": signed.actor.role, "execution": signed.actor.execution},
        "op": op,
        "artifact": artifact,
        "path": path,
        "revision": revision,
        "schema_version": schema_version,
        "digest": fingerprint(text) if text is not None else "",
        "message": signed.message,
        "batch": batch or stamp.id,
    }
    return _entry(record, stamp, signed, artifact)


def snapshot(*, signed: Signed, read: list[dict], stamp: Stamp) -> Entry:
    """The entry recording what a piece of work read, each artifact as { artifact, revision, digest }, under its
    settled stamp. It names no artifact of its own and is a set of its own."""
    record = {
        "id": stamp.id,
        "at": stamp.at.isoformat(),
        "actor": {"role": signed.actor.role, "execution": signed.actor.execution},
        "op": "snapshot",
        "read": read,
        "message": signed.message,
        "batch": stamp.id,
    }
    return _entry(record, stamp, signed, "")


def _entry(record: dict, stamp: Stamp, signed: Signed, artifact: str) -> Entry:
    return Entry(
        stamp.id, stamp.at, _parts(stamp.id)[1], record, artifact, signed.actor.role, signed.actor.execution,
        record["batch"],
    )
