---
description: Resume from the most recent handoff. Reads the latest doc in docs/handoffs/, loads the wikilinked files it references, and reports understanding before doing any work.
allowed-tools: Bash, Read
---

You are resuming a session on the Hedonism Harness project. Behave as follows:

1. **Find the latest handoff.** Run:
   ```
   ls -1 docs/handoffs/ 2>/dev/null | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}-.*\.md$' | sort | tail -1
   ```
   The most recent handoff is the last filename in lexical order (filenames are `YYYY-MM-DD-<slug>.md`). If the directory is empty or missing, tell the user there is no handoff to resume from and stop.

2. **Read the latest handoff.** Use the Read tool on the file from step 1.

3. **Read every wikilinked file.** Inside the handoff, references appear as `[[path/to/file.md]]` or `[[path/to/file.py]]`. For each unique wikilink, read that file with the Read tool. Treat the path inside the brackets as a repo-relative path. If a file does not exist, note it in your summary but do not block.

4. **Confirm working state.** Run:
   ```
   git status && git log --oneline -3 && git branch --show-current
   ```
   Verify the branch and tip commit match what the handoff says, and surface any divergence.

5. **Summarize what you learned**, in 5–10 lines, in this exact shape:

   ```
   ### Resumed: <topic from handoff>

   Where we left off: <one sentence>
   What shipped last session: <one sentence>
   Open questions / blockers: <bullets, or "none">
   Next concrete step: <one sentence verbatim from handoff>
   Watch-outs I noted: <bullets, or "none">

   Branch: <name> (tip: <short sha>)
   Working tree: <clean|dirty>
   ```

6. **Stop and wait for direction.** Do not start any work. Do not modify any files. The user will tell you whether to proceed with the documented next step, take a different direction, or discuss first.

This protocol is the start-of-session counterpart to `/handoff`. Treat the handoff doc as ground truth for state and intent — your task is to internalize it, not to second-guess it.
