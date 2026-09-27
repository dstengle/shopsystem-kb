# 0014 A change's role and message are checked before its operations

2026-09-27. A Create, Write, Append, Delete, Apply or Snapshot with no role, no message, or neither is refused with those faults alone, the role's first, then the message's, then (for a snapshot) the piece of work's; its operations or names are not checked, as slice 93 already refuses a snapshot for its actor.
