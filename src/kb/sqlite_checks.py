"""The SQLite adapter's checks of a set inside its landing transaction, each on the store as the set finds it or
leaves it: each change's revision and that of every type it was read through compared with the one it was read at, every link it hands
landing, on a held artifact or, its target not held, under a held type the link carries and may land on, nothing
outside it linking into what it removes or drops, and each entry's id held once."""
from kb.port import Change, Conflict, Entry, Linked, Linking, Unlanded
from kb.sqlite_reads import Reads


class Checks(Reads):
    """The checks of a landing, over the connection the reads answer from."""

    def _compared(self, artifact, read: int) -> int:
        """The revision the artifact stands at; Conflict when it was read at another."""
        rows = self._rows("SELECT revision FROM artifacts WHERE id = ?", str(artifact))
        held = rows[0][0] if rows else 0
        if held != read:
            raise Conflict(f"{artifact} was read at revision {read} and stands at revision {held}")
        return held

    def _unmoved(self, changes: list[Change]) -> None:
        """Conflict when a type a change was read through stands at another revision than the one it was read at,
        an IRI read as holding nothing, at revision 0, among them."""
        for type_id, read in {each for change in changes for each in change.through}:
            self._compared(type_id, read)

    def _parts(self, artifact) -> list[str]:
        return [place for (place,) in self._rows("SELECT place FROM parts WHERE artifact = ?", str(artifact))]

    def _integral(self, changes: list[Change], before: dict) -> None:
        """Unlanded for every link the set hands that does not land (`_lands`); then
        Linked for every link from outside the set into an artifact the set removes or a part it drops."""
        last = {change.artifact: change for change in changes}
        unlanded = [
            Linking(artifact, link.field, link.place, link.target, link.part)
            for artifact, change in last.items() if change.content is not None
            for link in change.links if not self._lands(link)
        ]
        if unlanded:
            raise Unlanded(unlanded)
        linked = []
        for artifact, (held, parts) in before.items():
            gone = parts - set(self._parts(artifact)) if self.holds(artifact) else None
            if held:
                linked += [
                    each for each in self._links_into(artifact)
                    if each.source not in last and (gone is None or each.part in gone)
                ]
        if linked:
            raise Linked(linked)

    def _lands(self, link) -> bool:
        """Whether a link lands: on a held artifact of a kind it may land on, and on a part that artifact holds when
        it names one; or, its target not held, on an IRI under a type the link vouches for."""
        rows = self._rows("SELECT kind FROM artifacts WHERE id = ?", str(link.target))
        if not rows:
            return self._vouched(link)
        if rows[0][0] not in link.kinds:
            return False
        return not link.part or link.part in self._parts(link.target)

    def _vouched(self, link) -> bool:
        """Whether a link to an IRI not held carries a type that is held and is one it may land on; never an
        implicit link, so no artifact lands under a type not held."""
        if link.implicit or link.under is None or str(link.under) not in link.kinds:
            return False
        return self.holds(link.under)

    def _unheld(self, entries: list[Entry]) -> None:
        """Conflict when an entry's id is already held, or given twice."""
        ids = [entry.id for entry in entries]
        held = self._rows(f"SELECT id FROM entries WHERE id IN ({', '.join('?' * len(ids))})", *ids)
        if held or len(set(ids)) != len(ids):
            raise Conflict(f"an entry's id is held once; {[each for (each,) in held] or ids} already is")
