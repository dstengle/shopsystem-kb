# kb: how this code is shaped

Read before changing anything under `src/kb/`. These are rules, not preferences;
a change that breaks one is refactored into place first, then made.

## Module map

| module | owns | never holds |
|---|---|---|
| `contract/` | `kb.proto` and generated code | hand-written logic |
| `servicer.py` | the rpc adapter: request in, one call into the domain, response out, inside the one fail-closed wrapper | domain logic, file paths, git |
| `values.py` | conversion of single request fields into validated values: ids, locators, kinds, roots, content trees; the one reading of a moment in UTC, "UTC unless it says otherwise", which `in_utc` provides for both `since` and the clock | anything that touches the store or the filesystem |
| `signatures.py` | who makes a change and why: the actor, the signature, and the conversions of a writer's, a reader's and a starter's; refuses one that does not sign | I/O, other request values |
| `requests.py` | each rpc's request as the values its one domain call takes, built from `values.py`; refuses a request that does not convert | domain logic, I/O |
| `names.py` | the grammar of artifact and item names; how an artifact's name, a link's place inside one and a type's `kb:` reference are written and read; minting, uniqueness and reuse of item names | I/O |
| `validation.py` | the composed effective schema and the checks JSON Schema cannot express | file access |
| `check.py` | the check of the whole store: every artifact against the current version of its type, the stale listed beside the violations, a file that cannot be read or an artifact of a kind with no type reported and passed over | checks of its own, writes |
| `composition.py` | a type read through what it is built on: its composition, base first, and the type a `kb:` reference names | checks, file access |
| `links.py` | the one reading of links: every link an artifact carries, wherever it sits, and whether a link points at an artifact | checks, file access |
| `definitions.py` | a type checked as it is written: what it refers to is held, it is not built on itself, its link fields say what they may point at | file access, checking artifacts against a type |
| `refusals.py` | the faults the domain makes of what a store holds, each with its rule and message | conversions, type checks |
| `rules.py` | the name of every rule a fault of kb's own carries, which kb publishes (adrs/0018) | faults, messages |
| `write.py` | the write pipeline: draft, apply every operation, validate the whole draft, then write, journal and commit; starting a store, recording a snapshot | rpc types |
| `edits.py` | what each operation of a set does to the draft, checked against the draft as the operations before it left it | rpc types, writes |
| `places.py` | resolving a place inside an artifact to where its node stands, or the refusal saying why nothing does; whether a link's place names a part | I/O, what an operation does there |
| `read.py` | reads at every level, resolution and stubs | writes |
| `query.py` | list, refs, search, journal, snapshot gathering over the loaded corpus | writes |
| `search.py` | ranking prose and fields for the words searched | store access |
| `store.py` | files, the git repository, discovery of a store from the process's working directory and `KB_ROOT` | validation, domain rules |
| `canonical.py` | the one canonical YAML checker, dump and load; YAML 1.2 | domain rules |
| `settled.py` | what the store settles for every artifact whatever its type: the keys naming it and what each must be, its content without them, an artifact given them, and the order its entries are written in as its type declares | I/O, checks against a type |
| `content.py` | artifact content crossing the contract as canonical text, and `NotCanonical`, the refusal of text kb cannot keep: what kb publishes about content (adrs/0018) | anything else |
| `journal.py` | journal entries, their ids, files and fingerprints | anything else |
| `metaschema.py` | the one type a new store holds | logic |
| `client.py`, `cli.py` | the in-process transport; the operator's init and validate commands | domain logic |

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
3. **Loading returns a value.** `store` never raises for an unreadable or
   malformed stored file; it returns the artifact or a fault naming the file,
   and every reader handles both.
4. **Draft, validate, write.** A set of operations applies to an in-memory
   draft, the whole draft validates, and only then is anything written or
   committed. Nothing reads from disk after the first write of a set.
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
