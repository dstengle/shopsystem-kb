# kb: how this code is shaped

Read before changing anything under `src/kb/`. These are rules, not preferences;
a change that breaks one is refactored into place first, then made.

## Module map

| module | owns | never holds |
|---|---|---|
| `contract/` | `kb.proto` and generated code | hand-written logic |
| `servicer.py` | the rpc adapter: request in, validated values, one call into the domain, response out | domain logic, file paths, git |
| `values.py` | conversion of every request field into validated values: ids, locators, kinds, roots, content trees | anything that touches the store |
| `names.py` | minting, uniqueness, reuse and grammar of artifact and item ids | I/O |
| `validation.py` | the composed effective schema and the checks JSON Schema cannot express | file access |
| `write.py` | the write pipeline: draft, apply every operation, validate the whole draft, then write and commit | rpc types |
| `read.py` | reads at every level, resolution and stubs | writes |
| `query.py` | list, refs, search, journal, snapshot over the loaded corpus | writes |
| `store.py` | files, canonical serialization, the git repository, discovery | validation, domain rules |
| `journal.py` | journal entries and their files | anything else |

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
   an id looks like or whether it is free.

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
