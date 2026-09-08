# MiFO — Build Log

Append-only lab journal. One entry per work session.
Format: **What we did → Why → What we found → Decisions → Next.**
Old planning docs live in `archive/` (the v2.1 formula spec is our hypothesis reference for the fitting phase, not a locked design).

**Current step:** 1 — Data acquisition (labeled datasets)
**Next action:** Download + inventory LIAR / FakeNewsNet / NELA-GT into `data/` with provenance

---

## 2026-09-08 — Step 0: Pivot to data-first track

**What we did**
- Scrapped the v2.1 paper-spec planning approach. All 5 planning docs moved to `archive/`.
- Switched to a data-first workflow: ingest → EDA → features → experiments → formula fitting → evaluation. Product work (backend, frontend, deployment) deferred until the ML core is validated against real data.

**Why**
- The v2.1 spec contained ~15 locked formulas and weights that had never touched a real data point. From now on, formulas are hypotheses to be tested, refit, or refuted by data — not decisions made in advance.

**Decisions**
- D1: Archive (not delete) old docs. `MiFO_Formulas.md` is explicitly retained as the hypothesis set for the formula-fitting phase.
- D2: Documentation model = this log. No more big upfront roadmap documents. Each step gets documented here as it happens.
- D3: Datasets to acquire first: LIAR (12.8K labeled claims), FakeNewsNet (fake/real articles + tweet propagation graphs), NELA-GT (source-credibility-labeled articles). Custom event-cluster dataset to be built afterward via scraping.
- D4: Agent division of labor — Arena agent executes in-repo (code, runs, data, this log); Gemini Pro used for explanations and second opinions; human owns decisions and understanding. Rule: agents may write all the code, but every shipped line must be explainable by the human.

**Next**
- Step 1: acquire datasets, record provenance (source URL, date, size, license, SHA) in `data/README.md`, run first inventory.

## 2026-09-08 — Step 1 (partial): FakeNewsNet acquired + inventoried

**What we did**
- Probed sandbox capabilities: PyPI and GitHub (git/gh) reachable; general web egress blocked (UCSB, Harvard Dataverse, GDELT all unreachable via curl). ~20GB disk free. Python 3.11 + pandas 3.0.5 (env is ephemeral — reinstall each session via `requirements.txt`).
- Downloaded all 4 FakeNewsNet metadata CSVs from the source repo (GitHub API). Ran `scripts/step1_inventory.py`.

**Why**
- FakeNewsNet is the only public dataset with BOTH article labels (fake/real) and propagation data (tweet IDs) — it feeds the distortion track and the PAS/graph track simultaneously.

**What we found**
- 23,196 labeled articles: PolitiFact 432 fake / 624 real; GossipCop 5,323 fake / 16,817 real (GossipCop ~24% fake → class imbalance to handle in evaluation).
- Propagation signal is rich: median tweets/article = 79 (politifact fake) vs 8 (politifact real); gossipcop fake median 12 vs real 45. The asymmetry differs by source group — worth a proper EDA question, not an assumption.
- 330 articles have no URL (not crawlable); web.archive.org is a top "domain" in several groups → dead articles survive only via Wayback links (matters for text crawling).
- Domain composition differs sharply by label group (people.com/dailymail dominate gossipcop real; hollywoodlife dominates fake) → a **domain-prior-only baseline** is mandatory in evaluation, or we'd credit MiFO's formulas for what a domain lookup already knows.

**Decisions**
- D5: raw data stays in `data/raw/` (git-ignored); provenance + checksums in `data/README.md`.
- D6: LIAR zip is unfetchable from the sandbox (UCSB blocked) → user attaches the ~6MB zip, or fetches it in Colab with a provided snippet. NELA-GT deferred until we pick year subsets.

**Next**
- Receive LIAR (user attachment) → inventory it.
- Step 2 (EDA): label balance, tweet-count distributions per group, domain overlap analysis, crawlability audit.

## 2026-09-08 — Step 1.5: Ground rules established

**What we did**
- Wrote `GROUND_RULES.md` (v1): session ritual (log → commit → explain), reproducibility (immutable raw data, scripts-only derived data, no hand-typed numbers), verification (agents propose, repo verifies), human-in-the-loop (understanding gate, decision IDs), scope & safety.

**Why**
- The workflow has three specific risks: human is learning while building, multiple agents with conflicting knowledge (one was confidently wrong 3× in one patch this session), and a future research claim that requires reproducibility. The rules target exactly those.

**Decisions**
- D7: Adopt GROUND_RULES.md v1 as the working agreement. Amendments allowed via new log entry + version bump, never silent edits.

**Next**
- Step 2 (EDA on FakeNewsNet): label balance, tweet-count distributions, domain overlap, crawlability audit. LIAR still pending from user.

## 2026-09-08 — Step 1.6: environment restore caught; data rehydration added

**What happened**
- Sandbox was rebuilt between sessions. Two effects, caught by post-session verification: (1) untracked raw data (`data/raw/`, git-ignored) was lost; (2) the previous session's commit boundary was squashed — `d0436ab` now contains both step 1 and step 1.5 (content verified complete against expectations, nothing missing).

**What we did**
- Added `scripts/fetch_data.py`: one-command rehydration of all GitHub-fetchable raw data, with SHA256 verification against the checksums recorded in `data/README.md` at acquisition time.
- Re-downloaded all 4 FakeNewsNet CSVs — all 4 checksums match the originals (data is byte-identical).

**Why**
- Ground rule in action: log the break, don't hide it. And the checksum mandate proved its worth within one day of existing: we can prove the restored data is identical rather than trusting it.

**Decisions**
- D8: Raw data in this sandbox is EPHEMERAL across sessions. Every dataset must be rehydratable via a committed script; checksums are recorded at acquisition, verified at every rehydration.

**Next**
- Step 2 (EDA) unchanged. LIAR zip still pending from user (UCSB unreachable from sandbox).

## 2026-09-08 — Step 1.7: publishing gap caught; rules amended to v1.1

**What happened**
- User checked GitHub and saw the repo unchanged. Cause: all work since the pivot existed only as local commits on the session branch — nothing had been pushed. `master` on GitHub was still at the initial commit `e74cf57`.

**What we did**
- Pushed `arena/01a080cf-mifo` to origin and opened PR #1 (arena branch → master).
- Amended GROUND_RULES.md to v1.1: **push** is now an explicit step in the session ritual (between commit and explain), and rehydration now includes `scripts/fetch_data.py`.

**Why**
- Rule break logged, rule fixed. "Commit" without "push" means the work is invisible to everyone but the sandbox — for a repo whose whole point is documented progress, that's a broken state.

**Decisions**
- D9: Session ritual is now log → commit → push → explain (GROUND_RULES v1.1). PRs into `master` are merged by the human (decisions belong to the human).

**Next**
- User merges PR #1 (or asks me to). Then Step 2 (EDA) on go. LIAR zip still pending from user.
