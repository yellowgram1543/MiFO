# MiFO Ground Rules

Working agreement between the human and the agents. v1.1 — 2026-09-08.
These are enforceable habits, not aspirations. If a rule gets broken, we log the break and fix it — we don't delete the evidence.

## 1. Session ritual (every work session, no exceptions)

1. **Rehydrate:** if the sandbox env was reset, `pip install --break-system-packages -r requirements.txt` and `python3 scripts/fetch_data.py`.
2. **Work.**
3. **Log:** append a `LOG.md` entry — *What we did → Why → What we found → Decisions → Next*.
4. **Commit:** all work of the session (code + log) in one commit, message format `step N[.M]: <what happened>`.
5. **Push:** `git push origin arena/01a080cf-mifo` — unpublished work doesn't exist (v1.1: added after the "why is everything still the same" incident).
6. **Explain:** plain-language explanation to the human in chat; human asks questions until it clicks.

A session that ends without 3–6 is not a closed session.

## 2. Reproducibility

- **Raw data is immutable.** `data/raw/` is never edited, never deleted. All transformations write to `data/processed/` and exist only as output of a committed script in `scripts/`.
- **No manual edits to data files. Ever.** If a fix is needed, fix the script and regenerate.
- **Every number quoted in `LOG.md` is the output of a committed script** — never hand-typed, never from memory.
- **Colab handoffs are self-contained:** notebooks live in `notebooks/`, run top-to-bottom without hidden state, and write their outputs to files that return to `data/`.

## 3. Truth & verification

- **Agents propose, the repo verifies.** Any external claim (from Gemini, the web, or an agent's memory) enters `LOG.md` as fact only after being checked against data, code, or primary source. Until then it is marked *unverified*.
- **Mistakes and negative results are logged with the same detail as wins.** The log is append-only; nothing is erased or rewritten.
- **Every dataset gets a `data/README.md` provenance entry the day it arrives:** source URL, retrieval date, counts, checksums, license/usage notes.

## 4. Human-in-the-loop

- **Agents may write 100% of the code; the human must be able to explain every line that ships.**
- **Understanding gate:** a step is only "done" when the human can answer, in their own words: what we did, why, what we found, what's next.
- **Decisions belong to the human.** Real choices get decision IDs (D1, D2, …) with rationale in the log.
- **External agents (Gemini, etc.) are teachers and red teams, not sources of truth.** Paste them our log/code and ask "what's wrong with this?" — then verify their answers here.

## 5. Scope & safety

- **No secrets in code, logs, or notebooks.** Keys live in Colab secrets / env vars only.
- **Respect dataset licenses**; research-use data stays inside `data/`.
- **Timebox every step.** At the end of a step: explicit continue / adjust / stop decision.
- **All work stays on this session's branch. Never force-push, never rewrite history.**
- Product work (backend, frontend, deployment) stays deferred until the ML core is validated by data.
