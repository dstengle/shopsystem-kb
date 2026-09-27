# 0001 YAML 1.2 on disk, git canonical, one file per artifact

2026-09-23. Every artifact is one YAML 1.2 file under `<root>/kb/`, which is itself the git repository, with `kb/store.yaml` as the store marker. kb writes one canonical form (literal blocks, indented sequences, no folding, deterministic bytes) and is the only writer. All YAML kb reads or writes is 1.2, through a pure-Python loader.
