# H41

**Human Observation Probe H41** launches **2 September 2026** and makes one observation per day for 365 days.

It alternates between the human present and past. Each day inherits something from the preceding day. H41 knows its observation period is finite.

## Stack
GitHub Actions · Gemini API · Google Search grounding · static GitHub Pages · repository-based memory.

## Launch checklist
1. Push these files to a GitHub repository.
2. Add repository secret `GEMINI_API_KEY`.
3. Settings → Pages → deploy from `/docs` on the default branch.
4. Keep Actions enabled. H41 runs daily at **06:41 Europe/Madrid**; manual dispatch is also enabled.

Published observations should be treated as append-only historical artifacts: do not silently rewrite them.
