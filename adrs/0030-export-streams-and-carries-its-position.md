# 0030 Export streams its files and answers its journal position

2026-10-10. The contract's export answers as a stream, one file to a message, selected by the path below each type and by type, and says the journal position it reflects, so that a store larger than one message exports, and an export of what changed since a position can be added later as an optional field without breaking the contract. Incremental export waits until a store needs it. Refines 0029. The user's decision.
