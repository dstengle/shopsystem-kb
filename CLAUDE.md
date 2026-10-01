# kb: how this code is shaped

Read before changing anything under `src/kb/`. These are rules, not preferences;
a change that breaks one is refactored into place first, then made.

## Module map

| module | owns | never holds |
|---|---|---|
| `contract/` | `kb.proto` and generated code | hand-written logic |
| `servicer.py` | the rpc adapter: request in, one call into the domain, response out, inside the one fail-closed wrapper | domain logic, file paths, git |
| `values.py` | conversion of single request fields into validated values: ids, locators, kinds, roots, the directory an export is written to, content trees; the one reading of a moment in UTC, "UTC unless it says otherwise", which `in_utc` provides for both `since` and the clock | anything that touches the store or the filesystem |
| `signatures.py` | who makes a change and why: the actor, the signature, and the conversions of a writer's, a reader's and a starter's; refuses one that does not sign | I/O, other request values |
| `requests.py` | each rpc's request as the values its one domain call takes, built from `values.py`; refuses a request that does not convert | domain logic, I/O |
| `names.py` | the grammar of artifact and item names; how an artifact's name, a link's place inside one and a type's `kb:` reference are written and read; the one order names are given in (`order`); minting, uniqueness and reuse of item names | I/O |
| `validation.py` | the composed effective schema and the checks JSON Schema cannot express | file access |
| `check.py` | the check of the whole store, read through the port: every artifact against the current version of its type, the stale listed beside the violations | checks of its own, writes |
| `composition.py` | a type read through what it is built on: its composition, base first, the type a `kb:` reference names, and which kinds' types read a given type | checks, file access |
| `links.py` | the one reading of links: every link an artifact carries, wherever it sits, and those links as the port takes them | checks, store access |
| `definitions.py` | a type checked as it is written: what it refers to is held, it is not built on itself, its link fields say what they may point at | file access, checking artifacts against a type |
| `refusals.py` | the faults the domain makes of what a store holds, each with its rule and message | conversions, type checks |
| `rules.py` | the name of every rule a fault of kb's own carries, which kb publishes (adrs/0018) | faults, messages |
| `write.py` | the write pipeline: draft, apply every operation, validate the whole draft, settle each entry's stamp, then land the set and its entries through the port in one call; starting a store, recording a snapshot | rpc types, SQL |
| `edits.py` | what each operation of a set does to the draft, acting on the draft as the operations before it left it: what it names, the revisions it makes, a type's version moved on from the one it acted on, the names of its items; never what its content or links come to, which `write.py` checks for every change against the state the whole set leaves | rpc types, writes |
| `draft.py` | the store as a set's changes would leave it, read like the store: what it holds, each artifact, the links into one, and which held artifacts' links a changed type reads anew, over the port | writes, checks |
| `places.py` | resolving a place inside an artifact to where its node stands, or the refusal saying why nothing does; whether a link's place names a part | I/O, what an operation does there |
| `read.py` | reads at every level, resolution and stubs | writes |
| `query.py` | list, refs, search, journal, snapshot gathering, asked of the store through the port | writes, SQL |
| `search.py` | ranking prose and fields for the words searched | store access |
| `port.py` | the storage port, kb-internal and unpublished: the interface every adapter answers, the change, relink, link, entry and read values it takes and gives, and its refusals (`Conflict`, `Linked`, `Unlanded`, `Unreadable`) | an adapter, kb's rules |
| `sqlite_store.py` | the SQLite adapter: whether this SQLite can keep a store, making and opening the database, its schema, and landing a set and its restated links in one `BEGIN IMMEDIATE` transaction with its revision, landing and linked checks | types, composition, kb's rules |
| `sqlite_reads.py` | the SQLite adapter's reads over one connection, a block of them held at one moment in one read transaction, and content as the database keeps it (JSON text that reads back every value kb accepts) | writes, types, composition, kb's rules |
| `store.py` | where a store is and what marks it: discovery from the process's working directory and `KB_ROOT`, `vacant`, the marker and its value, and where the database lies beside the marker, which it hands to the adapter; starting a store in that order, marker last | validation, domain rules, SQL, git |
| `canonical.py` | the one canonical YAML checker, dump and load; YAML 1.2 | domain rules |
| `settled.py` | what the store settles for every artifact whatever its type: the keys naming it and what each must be, its content without them, an artifact given them, and the order its entries are written in as its type declares | I/O, checks against a type |
| `content.py` | artifact content crossing the contract as canonical text, and `NotCanonical`, the refusal of text kb cannot keep: what kb publishes about content (adrs/0018) | anything else |
| `journal.py` | history entries, their ids and stamps, and fingerprints of canonical text; it writes nothing, its entries ride with the set handed to the port | anything else |
| `metaschema.py` | the one type a new store holds | logic |
| `export.py` | the store written out as canonical files at one moment, never over anything: `<dir>/<kind>/<slug>.yaml`, every artifact read in one view of the store before the directory is touched; refuses a directory that holds anything | checks, rpc types, the store's own files |
| `client.py`, `cli.py` | the in-process transport, and the operator's export through it, not part of the contract; the operator's init, validate and export commands | domain logic |

A new concern gets a new module. Nothing is added "beside" existing code in a
module that does not own it.

## Rules that make whole classes of defect unreachable

1. **Fail-closed boundary.** Every rpc runs inside one wrapper in `servicer.py`
   that converts the request, runs the domain call, and turns any exception
   that still escapes into a fault with nothing written. No other module
   catches broad exceptions.
2. **Parse, don't validate.** A request field becomes a validated value in
   `values.py` before anything else sees it. Domain and store functions take
   only those values, never a string that came from a request.
3. **A database that cannot be read is one fault.** A database that cannot
   be opened or read refuses every call and every command with one fault,
   rule `unreadable`, naming the database, and writes nothing; damage to
   files is found by the import check, not by the store.
4. **Draft, validate, land.** A set of operations applies to an in-memory
   draft, the whole draft validates, and only then is the set handed to the
   port, which lands every change with its history in one transaction or
   nothing. Nothing reads the store between handing the set over and its
   landing.
5. **One canonical checker**, applied to content after parsing and to bytes
   before writing. All YAML is 1.2.
6. **Names live in one place.** No module other than `names.py` decides what
   an artifact's or an item's name looks like or whether it is free;
   `journal.py` alone decides a journal entry's id.

## Size and shape

- No module over 250 lines; `servicer.py` under 150. When a change would
  cross a limit, split first.
- A function does one thing at one level of abstraction; if it needs a
  comment to separate its phases, it is two functions.
- Tests use the contract or the module's public functions, never private
  helpers.

## Working here

- `make dev` once; `make test` runs the suite in this checkout's virtualenv;
  `make contract` regenerates the stubs after `kb.proto` changes.
- Behaviour comes from `features/`; code is written red-green against a
  scenario, one at a time, and never adds behaviour no scenario asks for.
- A refactor is an enabling slice: its check is the suite still green and
  the structural target met.
