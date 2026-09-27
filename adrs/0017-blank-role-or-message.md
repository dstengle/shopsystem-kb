# 0017 A role or a message of blank space alone is none, and one with text is kept as given

2026-09-27. A role or a message counts as none when nothing is left of it once the blank space at either end is taken away, blank space being every character Python's `str.isspace` counts (spaces, tabs, line breaks, a no-break space); it is then refused as decisions 0012, 0014 and 0015 refuse a missing one. A role or message with anything else in it is taken and kept exactly as given, its blank space included.
