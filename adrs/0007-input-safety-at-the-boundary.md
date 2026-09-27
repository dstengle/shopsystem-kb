# 0007 Parse, don't validate, at the rpc boundary

2026-09-24. Every request field becomes a validated value before the domain sees it. Names follow a plain-name grammar; no `..` or absolute paths. The boundary fails closed: one wrapper turns refusals into faults with nothing written.
