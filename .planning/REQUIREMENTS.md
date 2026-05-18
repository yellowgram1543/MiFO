# Requirements

## Validated
(None yet)

## Active
- [ ] R1: Provision Azure Infrastructure (Cosmos, Blob, App Service, AI Search)
- [ ] R2: Build FastAPI scaffold with health endpoints and rate limiting
- [ ] R3: Implement data ingestion (NewsAPI, extraction, embedding via OpenAI)
- [ ] R4: Implement Anchor Selection Score (ASS) algorithm
- [ ] R5: Extract factual claims and perform hybrid sampling
- [ ] R6: Compute Distortion Components (S, E, C)
- [ ] R7: Implement Calibration, Confidence Score, and Propagation Anomaly Score (PAS)
- [ ] R8: Build Chrome Extension with D3.js Threat Matrix
- [ ] R9: Implement Golden Path (pre-analyze 25 topics) and Demo Polish

## Out of Scope
- [ ] Redis caching — Replaced by Cosmos DB native TTL to stay within student budget.
- [ ] Local Heavy Embeddings — all-mpnet-base-v2, DeBERTa-large too heavy for F1 tier (1GB RAM).
