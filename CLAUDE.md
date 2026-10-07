# kb: how this code is shaped

Read before changing anything under `src/kb/`. These are rules, not preferences;
a change that breaks one is refactored into place first, then made.

## Module map

| module | owns | never holds |
|---|---|---|
| `contract/` | `kb.proto` and generated code | hand-written logic |
| `servicer.py` | the rpc adapter: request in, one call into the domain, response out, inside the one fail-closed wrapper; the client's clock read so that its failure is `ClockFailed`; an rpc that writes refused while a server owns the store (`served.py`), unless the servicer is the one that server hosts; which rpcs write (`writes`) | domain logic, file paths, git |
| `escapes.py` | the fault an exception escaping the domain becomes inside `servicer.py`'s one wrapper: the clock's failure (`ClockFailed`), `Busy`, an earlier or a later kb's store, a database that cannot be read, anything else | catching exceptions, messages (`refusals.py` makes each fault from plain values) |
| `responses.py` | an rpc's or an operator's command's response made from what its call gave, or from the faults it was refused for: an rpc's result or refusal, never both; an operator's command's, or `kb.init`'s, faults; a change's result and a set's, made from what the set landed | domain logic, conversions, I/O |
| `starting.py` | `kb.init`, a store started in the client's own process, off the wire, which the operator's `kb init` calls too: who starts it and where, converted, then one call into the domain inside `servicer.py`'s one wrapper; `kb.NotStarted`, raised with the faults when it refuses; `kb` publishes both; and the faults it would refuse a root for, asked before anything is made (`refused`); a step a start takes on the filesystem first, inside that wrapper (`prepared`) | domain logic, finding a store, rpcs |
| `operating.py` | the operator's commands that are not rpcs (export, the import check, the import), each one call into the domain inside `servicer.py`'s one wrapper | domain logic, finding the store |
| `values.py` | conversion of single request fields into validated values: ids, locators, kinds, a create's key, the revision a change says it read (0 for none), roots, the directory an export is written to or an import read from, content trees; the one reading of a moment in UTC, "UTC unless it says otherwise", which `in_utc` provides for both `since` and the clock | anything that touches the store or the filesystem |
| `signatures.py` | who makes a change and why: the actor, the signature, and the conversions of a writer's and a reader's `Signature` and a starter's role and piece of work; refuses one that does not sign | I/O, other request values |
| `requests.py` | each rpc's request but the changes as the values its one domain call takes, built from `values.py`; refuses a request that does not convert | domain logic, I/O |
| `changes.py` | each change's request, alone or in a set of one kind (`BatchCreate`, `BatchReplace`, `BatchAdd`, `BatchRemove`), as the values its one domain call takes, built from `values.py` and `signatures.py`; refuses a request that does not convert, an empty set, and a set two of whose creates carry one key (beside every other fault of the set), each change of a set that does not convert standing in its place as its refusal | domain logic, I/O |
| `names.py` | the grammar of artifact and item names; how an artifact's name, a link's place inside one, a link to a key (`@<key>`) and a type's `kb:` reference are written and read; the export layout's place for an artifact (`place`) and the name a file's place gives (`filed`); the one order names are given in (`order`); minting, uniqueness and reuse of item names | I/O |
| `validation.py` | the composed effective schema, the 2020-12 metaschemas it resolves through, and the checks JSON Schema cannot express | file access |
| `check.py` | the check of the whole store, read through the port: every artifact against the current version of its type, each artifact's violations in order (`fault_order.py`), the stale listed beside the violations | checks of its own, writes |
| `composition.py` | a type read through what it is built on: its composition, base first, the type a `kb:` reference names, which kinds' types read a given type, and the types an artifact of a kind is read through | checks, file access |
| `links.py` | the one reading of links: every link an artifact carries, wherever it sits, those links as the port takes them, and an artifact with each of its links rewritten | checks, store access |
| `keys.py` | a set's keys: each key a create carries standing for the name that create was given, every link to a key in what the set's creates made holding that name, put in the draft once every create has acted and before anything is checked | checks, writes, rpc types |
| `definitions.py` | a type checked as it is written: what it refers to is held, it is not built on itself, kb's keywords stand only where kb reads them (`keywords.py`), each link field kb reads states its whole shape | file access, checking artifacts against a type |
| `keywords.py` | where kb reads its keywords in a type, and every place one of them stands | checks, faults or file access |
| `fault_order.py` | the order an artifact's faults are given in: its places as it reads back (`settled.py`'s order), a place before what is inside it, then at one place by the names of the rules broken; used by `drafting.py` for each change and by `check.py` for each artifact | making or checking faults |
| `refusals.py` | the faults the domain makes of what a store holds (but a type as it is written), of a store that cannot be read, and of a store or server that cannot be reached (`served`, `connection`, `unreachable`), each with its rule and message, from plain values | conversions, type checks, exceptions |
| `type_refusals.py` | the faults of a type as it is written, each with its rule and message, from plain values: a shape no held type has, a type built on itself, a keyword of kb's where kb does not read it, a link field that leaves out part of its shape or says what kb does not know, a version kept while the type changed | conversions, the checks that find them, exceptions |
| `rules.py` | the name of every rule a fault of kb's own carries, which kb publishes (decision/published-contract-v1) | faults, messages |
| `write.py` | the write pipeline: the set drafted (`drafting.py`), each entry's stamp settled, then the set and its entries landed through the port in one call; when the port finds an artifact it changes, a type it was read through or an artifact whose links it reads anew has moved since, drafted, stamped and landed again inside the port's `exclusive` block, which nothing else lands during, so a change that says the revision it read is compared again there and refused if its artifact moved; starting a store, recording a snapshot | rpc types, SQL, checks of a draft |
| `drafting.py` | a set drafted against the store as it stands: every operation applied, each link to a key given the name its create was given (`keys.py`), every change checked against the state the whole set leaves, an import keeping the revision and type version its file gives; each change's faults put in order (`fault_order.py`); each change as the port takes it, with the revisions of the types it was read through and the rows it is found by | rpc types, writes, SQL |
| `edits.py` | what each operation of a set does to the draft, acting on the draft as the operations before it left it: what it names, the revision a change says it read against the one its artifact stands at, the revisions it makes, a type's version moved on from the one it acted on, the names of its items; an import's artifact put whole, as its file gives it; never what its content or links come to, which `drafting.py` checks for every change against the state the whole set leaves | rpc types, writes |
| `draft.py` | the store as a set's changes would leave it, read like the store: what it holds, each artifact, the links into one, and which kinds, and which held artifacts of them, a changed type has their links read anew, over the port; each type as first read, and the revision it was read at | writes, checks |
| `places.py` | resolving a place inside an artifact to where its node stands, or the refusal saying why nothing does; whether a link's place names a part | I/O, what an operation does there |
| `read.py` | reads at every level, resolution and stubs | writes |
| `query.py` | list, follow, search, history, snapshot gathering, asked of the store through the port | writes, SQL |
| `search.py` | ranking prose and fields for the words searched, and the rows an artifact is found by, those sections and fields with their words folded (`searchable`) | store access |
| `port.py` | the storage port, kb-internal and unpublished: the interface every adapter answers, a block holding the write lock (`exclusive`), the change (with the revisions of the types it was read through and the search rows kb gives it), relink, link, entry and read values it takes and gives, the kinds whose links a set reads anew, and its refusals (`Conflict`, `Linked`, `Unlanded`, `Busy`, `Unreadable`) | an adapter, kb's rules, the store's marker |
| `sqlite_store.py` | the SQLite adapter: whether this SQLite can keep a store, making and opening the database (refused as `Unreadable` when it or its directory cannot be written), its schema (each entry numbered in the order it landed), the write lock held for a block, and landing a set and its restated links in one `BEGIN IMMEDIATE` transaction, or under a savepoint inside a held block; a lock waited on too long raised as `Busy`, any other database error as `Unreadable` | types, composition, kb's rules |
| `sqlite_checks.py` | the SQLite adapter's checks of a set inside its landing transaction: revisions of what it changes and the types it was read through, every artifact of a kind it reads anew restated, links landing, links into what it removes or drops, entry ids held once | writes, types, kb's rules |
| `sqlite_search.py` | the SQLite adapter's search rows of an artifact, as a change hands them, written under row ids it gives and taken out | reads, types, content's shape, kb's rules |
| `sqlite_reads.py` | the SQLite adapter's reads over one connection, a block of them held at one moment in one read transaction (or within the transaction already open), and content as the database keeps it (JSON text that reads back every value kb accepts) | writes, types, composition, kb's rules |
| `store.py` | where a store is and what marks it, and what marks the connection to a server serving one (`kb/server.yaml`, whose `address` it reads into a value, or refuses with `connection` when the file cannot be read or names no address): discovery from the process's working directory and `KB_ROOT`, stopping at a directory holding either and saying which it found (`Found`), or refusing one holding both with `store`, whether a root given outright holds a store, the fault for an operator's command over the store's files that found a connection (`directly`), `vacant`, the marker and its value, telling a store an earlier kb made (`EarlierKb`) or a later one (`LaterKb`, a marker of a form this kb does not know or that cannot be read) apart before anything is opened, and where the database lies beside the marker, which it hands to the adapter; starting a store in that order, marker last | validation, domain rules, SQL, git, writing a connection |
| `canonical.py` | the one canonical YAML checker, dump and load; YAML 1.2 | domain rules |
| `settled.py` | what the store settles for every artifact whatever its type: the keys naming it and what each must be, its content without them, an artifact given them, and the order its entries are written in as its type declares | I/O, checks against a type |
| `content.py` | artifact content crossing the contract as canonical text, and `NotCanonical`, the refusal of text kb cannot keep: what kb publishes about content (decision/published-contract-v1) | anything else |
| `journal.py` | history entries, their ids and stamps, and fingerprints of canonical text; it writes nothing, its entries ride with the set handed to the port | anything else |
| `metaschema.py` | the one type a new store holds | logic |
| `export.py` | the store written out as canonical files at one moment, never over anything: `<dir>/<kind>/<slug>.yaml`, every artifact read in one view of the store before the directory is touched, its entries in the order its type's current version declares; refuses what is not a directory, or a directory that holds anything | checks, rpc types, the store's own files |
| `offers.py` | a directory's files as offered for import: which are read (a store's history and the files that mark and keep it, at the top, passed over: `.git/`, `journal/`, `store.py`'s marker and database, and `served.py`'s lock), each read as YAML 1.2 and as an artifact at its place in the export layout; a name that is not a directory refused | checks against a type, writes |
| `importing.py` | a directory read as a set for import: each file's errors (not in canonical form, a kind with no type, content and links against its type, a differing type of types), and the files that would be skipped because they lead to one by a link, by their type, or, for a type, by a `kb:` reference, with their chains; files drafted over the store; the import: into a freshly started store only, found fresh, drafted and landed while it holds the write lock, refused with the report when the check finds errors, or, with errors skipped, all but what is broken or leads to it, landed as one set through `write.land`, types first, each after those it is read through | reading files, SQL, rpc types |
| `client.py`, `cli.py` | the client, which on each call chooses its transport from what discovery finds, the servicer in process for a store, `network.py` for the connection to a server, and beside it, never on it nor through a server, the operator's export, import check and import over the store they find, not part of the contract; the operator's commands, which set a store up (through `kb.init`), check one, export one, import into a freshly started store (`import`, `import --check`, `import --skip-errors`), set one up seeded from a directory of files (`init <root> --seed <dir>`, through `staging.py`, the import's report shown as `import` shows it, and, interrupted, ended by SIGINT as an interrupt ends a program once the staging is gone, with no traceback), and serve one (`serve <root> --listen <host:port> [--start]`, through `server.py`, refused with no address given; with `--start`, a root holding no store has one started first, under the role `KB_ACTOR` names, through `staging.py`, and a store already there served as it stands, no role read), and nothing else | domain logic |
| `staging.py` | a store started out of sight under its root, for `kb init --seed` seeded (`seeded`) and for `kb serve --start` holding nothing yet (`started`), in `.kb-starting/` (cleared first of what a stopped run left, removed however the start ends), put in place whole by one rename, and taken back whole: the root checked as `kb.init` checks it before anything is made, the store started through `kb.init`, the seed landed through `operating.py`'s import | finding a store, checks, rpcs |
| `addresses.py` | a server's address, `host:port`, read once into a value from the operator's `--listen` or a connection's `address` | I/O, what a connection is |
| `server.py` | the store hosted by `grpc.server`: the one servicer for a root, with the server's clock, bound at an address (the system's port when 0 is asked), started, saying where it serves, stopped, a start that fails partway leaving nothing it made open; the store owned for the server's life through `served.py`, its lock taken before anything is bound and let go when it stops, refused with `served` when another server owns it; the rpcs that write (those `servicer.py` marks as writing) taken one at a time under the server's lock (`taking`, an `InOrder`, which lets them in in the order they arrive), reads answered as they come; a root that holds nothing this kb can serve refused before anything listens, through `servicer.py`'s one wrapper; `kb serve` waiting until SIGINT or SIGTERM | domain logic, finding a store, the connection |
| `served.py` | whether a store is served and at what address: the lock of the operating system (`flock`) a server holds for its life on `kb/served.yaml`, the store's own file naming that address, taken (`owned`), marked with the address (`mark`), and asked after by a change asked directly (`unserved`, refusing with `served`); a file left with no lock held, or none, is a store nobody serves | finding a store, the connection, rpcs |
| `network.py` | the network transport: an rpc called, with its request as asked, on the server at a connection's address, over a channel made for that call, which gives up connecting after a few seconds, and the server's response; a `grpc.RpcError` becomes the rpc's own response refused with `unreachable`, naming the address | domain logic, discovery |
| `testing.py` | `served`, published: the double a client's tests serve a store with, `server.py`'s server for a root in the test's own process on 127.0.0.1 at the system's port, with the clock it is given, the connection written under the directory it is named, `kb/` made for it when missing; on exit, however the block ended, the server stopped and the store let go, the connection removed, and `kb/` too when it made it and it is left empty | domain logic, finding a store, checking what it is given |

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

- `make dev` once; `make test` runs the suite in this checkout's virtualenv, in parallel (`-n auto`), the operator's commands run in-process (one test runs the installed `kb`); during red-green run the slice's marker (`-m slice-N`), and the whole suite once per slice;
  `make contract` regenerates the stubs after `kb.proto` changes.
- Behaviour comes from `features/`; code is written red-green against a
  scenario, one at a time, and never adds behaviour no scenario asks for.
- A refactor is an enabling slice: its check is the suite still green and
  the structural target met.
