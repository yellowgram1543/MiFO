# MiFO — Build Log

Append-only lab journal. One entry per work session.
Format: **What we did → Why → What we found → Decisions → Next.**
Old planning docs live in `archive/` (the v2.1 formula spec is our hypothesis reference for the fitting phase, not a locked design).

**Current step:** 3 — Text acquisition (full crawl in progress)
**Next action:** F4 crawl completion → Wayback recovery stage → text corpus lock

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

## 2026-09-08 — Step 2: FakeNewsNet EDA — propagation

**What we did** (Colab, notebook.ipynb)
- Combined 4 CSVs (23,196 articles). Tweet-count availability + distributions per group×label; Mann-Whitney U + rank-biserial per source group.

**What we found**
- Zero-tweet share: politifact real 34.5% vs fake 9.3%; gossipcop real 6.3% vs fake 3.5%.
- politifact real is bimodal: median 8 but mean 670 (p99 = 12,505). Fakes spread more consistently but with a lower ceiling.
- **Propagation volume reverses by source group with near-equal force:** politifact rank-biserial +0.268 (p=7.7e-14, fake spreads more); gossipcop −0.269 (p=2.3e-193, real spreads more). Pooled, they cancel → tweet volume is a source-context feature, NOT a fakeness feature.
- Caveats: counts only (no timestamps yet); dataset is fact-checked articles (selection bias).

**Decisions**
- D10: Propagation features must be event-relative (compare to same-event baseline, never global constants). Validates the anchor-relative design in archive/MiFO_Formulas.md.

## 2026-09-08 — Step 2.5: Domain structure — the honesty baseline

**What we did**
- Domain parsing, fake/real overlap, domain-prior leave-one-out baseline, domain buckets (clean_fake ≥90% / MIXED / clean_real ≤10%), crawlability audit.

**What we found**
- Domain-prior LOO accuracy: ALL 83.4% (n=22,866) vs 75.2% majority (+8.2 pts only); politifact 67.9%, gossipcop 84.1%.
- Buckets: MIXED = 373 domains / 14,098 articles (61.6%) @ 77.9% LOO; clean_fake 546/1,557 @ 69.7% (cold-start artifact: singleton domains tie-break to global majority); clean_real 1,510/7,211 @ 97.2%.
- Minority-label articles (domain prior's irreducible errors): 3,184; actual LOO errors ≈ 3,807 (gap = tie-breaks on singleton domains). Math closes.
- **Structure: gossipcop is a within-domain problem** (75.9% of articles from domains publishing both labels — same outlet, story-level variation) **while politifact is between-domain** (long-tail fake sites vs mainstream real). Two different ML problems in one dataset.
- Crawlability: 330 no-URL, 204 archive.org-only, 1,208 duplicate URLs, 1,472 duplicate titles, 2,429 unique domains / 75 TLDs.

**Decisions**
- D11: All evaluation reported per source group, never pooled. Evaluation target: beat 77.9% on MIXED-domain articles using per-story content. The 84.1% pooled number is vanity and banned from claims.

## 2026-09-08 — Step 3: Text acquisition — LIAR + crawl pilot + Wayback

**What we did**
- LIAR acquired in Colab (UCSB zip; SHA256 611c1addad919743…, 1.0MB): train 10,269 / valid 1,284 / test 1,283 × 14 cols. Label counts (train): half-true 2,123, false 1,998, mostly-true 1,966, true 1,683, barely-true 1,657, pants-fire 842. The checksummed FILE is canonical (paper's published per-class numbers differ slightly — file wins).
- Agent error logged: initial parse spec used 15 column names for a 14-col file → one-position shift; fixed same session. Second agent error: report cell compared mixed-dtype status to int → "0.0% live" false reading; fixed (real pilot live rate 52.0%).
- Stratified pilot crawl: 1,430 URLs (all politifact + 125/cell gossipcop sample), polite crawler (2s/domain), trafilatura extraction.
- Wayback availability checks on failed URLs.

**What we found**
- Pilot: 52.0% live, 42.2% extracted ≥200 chars (604 texts), median 2,478 chars. Gossipcop extracts ~60%; politifact ~27% (link rot). Of live pages, 81% extract → bottleneck is dead links, not extraction. 403/402 blocks ≈ 18% (partly Colab datacenter IP).
- Wayback: A4's "0/150 coverage" was INVALID (agent error: 150 unspaced calls → throttled, all failures swallowed by except-pass; plus unencoded URL concatenation). Proper spaced diagnostics: 12/18 and 18/20 URLs have snapshots → real coverage of failed URLs ≈ 65–90%. Fake-news domains ARE archived.
- Full manifest: 21,461 unique crawlable URLs; 654 already have pilot text; TO CRAWL 20,807 (politifact 248f/286r, gossipcop 4,446f/15,827r).

**Decisions**
- D12: Hybrid text strategy — direct crawl for the full manifest + Wayback recovery stage (era-filtered snapshots) for failures. Rationale: gossipcop viable direct (~60%), politifact needs Wayback (~65–90% coverage of the dead).

## 2026-09-08 — Step 3.5: LIAR signal tests — the leakage lesson

**What we did**
- C3: TF-IDF(1-2gram)+LogReg 6-class baseline on claim text. C4: content vs context (speaker credit history) vs combined, with raw and leave-one-out (LOO) history variants.

**What we found**
- C3: acc 0.252 / macro-F1 0.219 vs 0.207 majority. Within published text-only band (~0.23–0.28). pants-fire recall 0.03 — text alone almost never catches the worst class.
- C4: **raw history-only scored 0.449 — that was leakage** (tallies include the current statement). LOO-corrected: 0.233. Combined text+history (LOO): **0.272 acc / 0.263 macro-F1** — best honest model; +20% relative macro-F1 over text-only. Multi-signal combination validated, modestly.
- The +4.4 macro-F1 points' source (per-class crosstab) — not yet run. Open item.

**Decisions**
- D13 (principle): Any feature computed from an aggregate that includes the current item must be leave-one-out corrected. Applies to speaker history, domain priors, and future anchor-consensus scores. The 0.449 number is banned from all claims.

## 2026-09-08 — Step 3.6: F3 stall incident (in progress)

**What happened**
- F3 (full crawl, Drive-direct writes): zero checkpoints in 36.5 min (<500 completions vs expected ~5/s). Pilot wrote 604 Drive texts in 5.3 min, so per-item Drive FUSE writes are the suspected bottleneck — this session's mount is degraded; each .txt write blocks its worker for seconds and writes serialize.

**What we did / are doing**
- F4 written: VM-local text writes + 60s heartbeat + checkpoint every 200 (local) + Drive sync (results.csv + texts zip) every 2,000. Rescues F3's partial texts automatically. Heartbeat confirms or refutes the Drive diagnosis at minute 1.

**Decisions**
- D14: During crawls, never put per-item I/O on the Drive mount — write VM-local, sync bulk snapshots to Drive. (Generalizes: per-item file writes go to fast local disk everywhere; network mounts get batch writes only.)

**Correction (post F4):** F4 heartbeat (0 completions with VM-local writes) + zero rescued F3 texts disproved the Drive-write theory. F3 completed zero items — actual cause is a network-layer hang (DNS/getaddrinfo is not covered by requests timeout) or dead VM egress. Triage + curl-based fetch (F5) issued. Agent diagnosis error logged.
