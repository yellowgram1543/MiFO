# Data Provenance

Raw data lives in `data/raw/` (git-ignored; retained in workspace). For every dataset record: source, retrieval date, counts, checksums, license/usage notes.

## FakeNewsNet — metadata CSVs (Step 1, 2026-09-08)
- **Source:** https://github.com/KaiDMML/FakeNewsNet (`dataset/` folder), retrieved via GitHub API.
- **Citation:** Shu et al., "FakeNewsNet: A Data Repository with News Content, Social Context and Spatiotemporal Context for Studying Fake News on Social Media" (2020).
- **Files & article counts:**

  | file | articles |
  |---|---|
  | politifact_fake.csv | 432 |
  | politifact_real.csv | 624 |
  | gossipcop_fake.csv | 5,323 |
  | gossipcop_real.csv | 16,817 |
  | **total** | **23,196** |

- **Columns:** `id, news_url, title, tweet_ids` (tweet IDs are tab-separated).
- **Labels:** fake/real by file membership (PolitiFact / GossipCop professional fact-checks).
- **Limitation:** URLs + titles + tweet IDs only. Full article text must be crawled separately (planned with the event-cluster dataset work).
- **SHA256 (first 16 hex):** `c6932bffadb1230b` (gossipcop_fake), `d721e9a8b7e660da` (gossipcop_real), `abe7fe7aad801b1e` (politifact_fake), `2500f86a7addca0f` (politifact_real).
- **License:** research use (see source repo README).

## LIAR — PENDING
- Source: https://www.cs.ucsb.edu/~william/data/liar_dataset.zip — blocked from sandbox egress; to be attached by user or fetched in Colab.

## NELA-GT — PENDING
- Harvard Dataverse doi:10.7910/DVN/ULZLCV — large; decide year subsets later.
