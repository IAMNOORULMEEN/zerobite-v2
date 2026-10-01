#!/usr/bin/env python3
"""Turn an AI reply into files (tolerant version).

Accepted header styles (all followed by a fenced code block):
  ### FILE: backend/app.py
  **FILE: backend/app.py**
  File: `backend/app.py`
  #### backend/app.py        (a header line that is just a path with an extension)

Usage (run from your project root):
  python apply.py reply.md
  wl-paste | python apply.py
"""
import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text() if len(sys.argv) > 1 else sys.stdin.read()
text = text.replace("\r\n", "\n")

header = re.compile(
    r"^[ \t]*(?:#{1,6}[ \t]*|\*\*|-[ \t]+)?[ \t]*(?:FILE|File|file)?[ \t]*:?[ \t]*[`*]*"
    r"([\w./\\-]+\.[\w]+|[\w./-]*(?:Dockerfile|Makefile|\.gitignore|\.env\.example))"
    r"[`*]*[ \t]*\*{0,2}[ \t]*:?[ \t]*$"
)
fence = re.compile(r"^[ \t]*(`{3,}|~{3,})")

lines = text.split("\n")
root = Path.cwd().resolve()
count = 0
i = 0
while i < len(lines):
    m = header.match(lines[i])
    # require the next non-empty line to be a code fence
    j = i + 1
    while m and j < len(lines) and lines[j].strip() == "":
        j += 1
    if m and j < len(lines) and fence.match(lines[j]):
        marker = fence.match(lines[j]).group(1)
        k = j + 1
        body = []
        while k < len(lines) and not re.match(r"^[ \t]*" + re.escape(marker[0]) + "{" + str(len(marker)) + r",}[ \t]*$", lines[k]):
            body.append(lines[k])
            k += 1
        rel = m.group(1).strip().replace("\\", "/")
        target = (root / rel).resolve()
        if not str(target).startswith(str(root) + "/"):
            print(f"SKIPPED (outside project): {rel}")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            existed = target.exists()
            target.write_text("\n".join(body) + "\n")
            print(("UPDATED " if existed else "CREATED ") + rel)
            count += 1
        i = k + 1
    else:
        i += 1

if count:
    print(f"\n{count} file(s) written.")
else:
    print("No files found. Run:  grep -n 'FILE' reply.md   and  head -n 20 reply.md  and show me the output.")
