# 0002 Ids are minted by kb from titles, never supplied by a client

2026-09-23. An artifact's id is `kind/name`, the name made from its title by kb's grammar, with -2, -3 on collision. Parts are named from their title or position, once. A client hands existing ids back on a write and never chooses one. kb generates the id and the client looks it up.
