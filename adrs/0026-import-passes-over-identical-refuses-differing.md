# 0026 Import goes into any store, passing over what it holds identically

2026-10-10. Import is no longer only into a freshly started store. An artifact the store already holds at the same IRI, with the same content and type version, is passed over; one that differs refuses the whole import, naming each IRI, and nothing lands. Replacing content stays a change through the contract. The user's decision.
