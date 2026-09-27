# 0003 Init refuses inside an existing store

2026-09-23. Starting a store where one already exists, above or below, is refused. Store discovery follows git's search semantics: `kb/store.yaml` upward from the working directory, or KB_ROOT; when KB_ROOT and discovery disagree, the call is refused rather than reads and writes going somewhere unexpected.
