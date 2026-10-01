# kb contract v1

Date: 2026-10-01. Note 2 of three (storage, the contract, the type language). Decided by the person across this
session: starting a store leaves the wire; one method per action, each with its own request and response; no
`Apply`, and batches one per kind of change, never different methods combined in one call; references inside a set
for creating artifacts that link to each other; everything as clean as possible, shop-knowledge fixed to match. The
rest was left to the controller's recommendations, which this note records as decisions. It rests on the writeup
"kb's protocol: what we should and should not have done" (2026-09-30).

## What changes for a client

kb's contract is published again as one breaking release. Every rpc is renamed or reshaped; what a call does is
unchanged except where a section below says otherwise.

### Starting a store leaves the wire

A store is started by the operator's `kb init`, or by a client in its own process calling `kb.init(root, role)`, a
function of the published package, which starts a store at the root under the role and raises `kb.NotStarted`,
carrying the faults, when it refuses. There is no `Init` rpc, and a served store cannot be started through its
server: the line saying a start through a server is refused goes with the rpc. Starting a store keeps every
behaviour it has (start-a-store); only the way it is asked for changes.

### One method per action, in the spec's words

The changes are `Create`, `Replace`, `Add` and `Remove` (today `Create`, `Write`, `Append`, `Delete`). The reads
are `Read`, `List`, `Follow` (today `Refs`), `Search` and `History` (today `Journal`). A piece of work records what
it read with `Snapshot`, and the whole store is checked with `Check` (today `Validate`). Every rpc has a request
message and a response message of its own, named after it, and no message is shared between two requests except
the small values every call names things with (a locator, a signature, a fault, a stub). A kind is called a kind,
never a type, wherever a request or a response names one; a place inside an artifact is a place, never a path.

### Sets are one kind of change at a time

`Apply` and its four operation messages go. Each change has a batch form that takes several of the same change as
one set: `CreateMany`, `ReplaceMany`, `AddMany` and `RemoveMany`. A set lands whole or not at all, is checked
against the state the whole set leaves, names itself, and gives each change's own result, as a set does today. A
set never mixes kinds of change: a client that needs a create and a replacement makes two calls.

### References inside a set

A create in `CreateMany` may carry a key of the client's choosing, unique in the set. Anywhere in the set, a link
written as `@` followed by a key names the artifact that create makes, and kb puts the name it mints in its place
before anything is checked, so new artifacts in one set can point at each other. A key that no create in the set
carries is refused as a link landing on nothing, naming the key. A reference names a whole artifact; a part of an
artifact made in the same set is not reached by a reference. The result of each create gives the name it was given,
in the order of the set.

### An expected revision on a change

`Replace`, `Add` and `Remove`, alone or in a set, may say the revision the client read the artifact at. When they
do, and the artifact stands at another revision when the change lands, the change is refused because the artifact
moved since it was read, naming the revision it stands at, and nothing of the set is written. When they do not,
the change acts on the artifact as it stands, as today. The refusal carries a rule of its own, `revision`, which
joins the published rule names.

### One signature

Every request that changes the store, and `Snapshot`, carries one `Signature`: the role, the piece of work and
the message. The rules of signing do not change (sign-a-change); only the shape they arrive in does. A snapshot's
piece of work is its signature's.

### Result or refusal

Every response is either the call's result or a refusal holding every fault, never both: a refusal carries no
half-filled result, and a result carries no faults. `Check`'s result is the violations and the stale; the
violations are what the store holds, not a refusal.

### Read asks for one level

A `Read` asks for a summary, the whole artifact with its links followed to a depth, or one section by its title,
and the request carries only what that level takes.

### A versioned package

The contract's package is `kb.v1`, so a client of one version calling a server of another is refused by the
transport rather than answered wrongly.

## What does not change

Content crosses as canonical YAML text; identity fields stay typed fields beside it; every fault at once; one
fail-closed wrapper; the in-process client from `kb.client.connect`, with its clock; `kb.content`; the connection
file. What is published is still versioned by the release tag, and the published surface gains `kb.init` and
`kb.NotStarted`.

## shop-knowledge

shop-knowledge moves to v1 when it bumps its pin: its calls renamed, its one set split by kind with references
where it creates linked artifacts, its result checks made on the outcome, and its stores moved by
`kb import` (note 1).
