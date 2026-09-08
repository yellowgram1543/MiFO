# MiFO: Project Technical Specification (Architect Version)
**Project Name:** Misinformation Forensics (MiFO)  
**Target:** Microsoft Imagine Cup 2027 / Senior Engineering Portfolio  
**Status:** Locked v2.1 Specification  

---

## 1. SYSTEM ARCHITECTURE

### 1.1 High-Level Layer Diagram
```text
CLIENT LAYER
─────────────────────────────────────
Browser Extension (React / Manifest V3)
  → calls FastAPI directly
  → no intermediate hops

BACKEND LAYER
─────────────────────────────────────
Azure App Service (FastAPI, F1 Free)
  → /health endpoint (DB + model checks)
  → /analyze (main pipeline)
  → /cached (golden path topics)
  → response cache (URL → result)
  → fail-safe: never crash, always degrade gracefully

AI SERVICES LAYER (Azure only)
─────────────────────────────────────
Azure OpenAI (gpt-4o-mini)
  → NLI scoring (structured JSON output)
  → Emotion detection
  → Moral framing
  → Genre classification (zero-shot)
  → Tier 2 claim normalization
  → Strict JSON response format enforced

Azure AI Language (Free tier)
  → NER (claim extraction)
  → Key phrase extraction
  → Sentiment baseline

Azure AI Content Safety (Free tier)
  → Article toxicity screening
  → Responsible AI narrative for MIC

DATA LAYER
─────────────────────────────────────
Azure Cosmos DB (Free tier)
  → Articles + metadata
  → Extracted claims
  → Distortion scores
  → PAS graph data
  → Precomputed: embeddings + ASS + claims
    for 20-30 golden path topics

Azure AI Search (Free tier)
  → Embedding vector storage
  → Semantic similarity queries

BACKGROUND LAYER
─────────────────────────────────────
Azure Functions (Consumption, Free tier)
  → Timer: ping /health every 14 min (keep-alive)
  → Timer: preprocessing new topics
  → Timer: KL drift monitoring (weekly)
  → Event: cache warming for new topics

OBSERVABILITY LAYER
─────────────────────────────────────
Azure Application Insights
  → Request latency tracking
  → API success rates
  → Dependency monitoring
  → Show live in demo = "wow" moment

EXTERNAL (minimal, fallback only)
─────────────────────────────────────
NewsAPI
  → Fallback only when topic not in cache
  → 100 req/day sufficient for fallback use
```

### 1.2 Component Responsibilities
*   **FastAPI Backend:** Orchestrates the pipeline, manages state transitions, and streams progress to the client via SSE.
*   **Azure OpenAI:** Acts as the high-reasoning engine for NLI (Natural Language Inference), claim normalization, emotion detection, moral framing, and genre classification.
*   **Azure AI Search:** Managed vector store for high-speed cosine similarity checks (Article vs. Anchor).
*   **Cosmos DB:** The primary source of truth for topics, claims, propagation graphs, and calibration data.
*   **Azure Functions:** Handles background maintenance (Keep-alive pings, daily drift monitoring, cache warming).
*   **Azure AI Language:** NER and key phrase extraction for claim candidacy scoring.
*   **Azure AI Content Safety:** Toxicity screening for Responsible AI compliance.

### 1.3 Data Flow (End-to-End)
1.  **Ingress:** Client sends URL or Topic Query.
2.  **Cache Check:** Cosmos `URLCache` checked for existing result (Instant Return via point-read, <10ms).
3.  **Fetch:** NewsAPI retrieves top 12-15 articles.
4.  **Anchor Selection:** Articles scored via $ASS$; top 3 form the ASS-weighted vector anchor.
5.  **Claim Extraction:** Target article segmented; hybrid sampling selects claims (max 15).
6.  **Inference:** Parallel calls to Azure OpenAI GPT-4o-mini for NLI (with self-consistency check), emotion, moral framing, and genre classification — all via structured JSON.
7.  **Scoring:** Formulas $S, E, C$ computed; $D$ is calibrated via Isotonic + PCHIP (monotone).
8.  **Egress:** Final 4D result stored in Cosmos `URLCache` + `Topics` and pushed to Client.

### 1.4 Routing Logic
```text
Request comes in
  ↓
Topic in Cosmos cache?
  YES → return precomputed result (instant)
  NO  → call NewsAPI → run full pipeline
          → store result in cache
          → return result
```

### 1.5 Fail-Safe & Degradation

**Rule: Never return HTTP 500. Always return something meaningful.**

| Failure | Fallback | User-Facing Flag |
| :--- | :--- | :--- |
| **OpenAI Timeout** | Fallback to `all-MiniLM-L6-v2` local embeddings (S only). NLI/E unavailable. | `"Basic Analysis Only"` |
| **NewsAPI Limit** | Serve from "Golden Path" cache. | `"Historical Data Only"` |
| **Cosmos Latency** | Serve result from in-memory LRU; retry DB write in background. | `"Results may be delayed"` |
| **AI Search Down** | Skip vector similarity; return S=null. | `"Partial analysis — Semantic Drift unavailable"` |
| **Any Component** | Return partial result with degradation flag. | `"Partial analysis — [component] unavailable"` |

---

## 2. AZURE INFRASTRUCTURE

| Service | Reason | Free Tier / Student Constraint |
| :--- | :--- | :--- |
| **App Service (F1)** | Hosts FastAPI. | Free (60 min/day CPU limit - mitigated by keep-alive). |
| **Cosmos DB** | Multi-model NoSQL for Article/Claim storage. | 1000 RU/s + 25GB Storage (Free). |
| **AI Search** | Vector search + Semantic Ranking. | Free (3 indexes / 50MB storage). |
| **Azure OpenAI** | SOTA LLM Reasoning (GPT-4o-mini). | Student Credits ($100) cover millions of tokens. |
| **Functions** | Timer-based maintenance / Keep-alive. | 1 Million free executions/month. |
| **Blob Storage** | Raw text storage + Calibration models. | 5GB LRS (Free). |
| **App Insights** | Real-time observability + Demo metrics. | 5GB/month data ingestion (Free). |
| **AI Language** | NER + Key Phrase extraction. | Free (5K transactions/month). |
| **AI Content Safety** | Toxicity screening. | Free (1K transactions/month). |
| **Key Vault** | Secrets management (API keys). | Free tier. |

**Keep-Alive Strategy:** An Azure Function triggers a `GET /health/ping` every 14 minutes to prevent the F1 App Service from entering "Cold Sleep."

### 2.1 Cost Breakdown
```text
Azure OpenAI (gpt-4o-mini)  → ~$3-8/month
Everything else              → $0 (free tiers)
─────────────────────────────
TOTAL                        → ~$3-8/month

$100 student credits = 12-30 months runway
MIC 2027 deadline = well within budget ✅
```

---

## 3. TECH STACK

### 3.1 Frontend
| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Framework** | React (Vite) | Speed, ecosystem, TypeScript support |
| **Language** | TypeScript | Type safety across components |
| **Styling** | TailwindCSS | Rapid UI development |
| **Visualization** | D3.js (Threat Matrix), Recharts (PAS timeline) | D3 for custom 4D charting; Recharts for standard charts |
| **Extension** | Chrome Extension (Manifest V3) | Primary user interface |
| **State** | Zustand | Lightweight alternative to Redux |
| **API Client** | Axios + React Query | Caching, retry, and invalidation |
| **Hosting** | Azure Static Web Apps (free) | Integrated CI/CD |

### 3.2 Backend
| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Framework** | FastAPI (Python 3.11) | Pydantic-native async + Auto-Swagger docs |
| **Testing** | Pytest | Standard Python testing |
| **Hosting** | Azure App Service F1 (free) | Zero-cost deployment |

### 3.3 AI Services
| Service | Usage |
| :--- | :--- |
| **Azure OpenAI (gpt-4o-mini)** | NLI scoring (structured JSON), Emotion detection, Moral framing, Genre classification, Tier 2 claim normalization |
| **Azure AI Language (free)** | NER, Key phrase extraction |
| **Azure AI Content Safety (free)** | Toxicity screening |

### 3.4 Embeddings
| Priority | Model | Constraint |
| :--- | :--- | :--- |
| **Primary** | Azure OpenAI `text-embedding-3-small` (1536 dims) | Generated via API call; stored/queried in Azure AI Search. Zero local RAM. |
| **Fallback** | `all-MiniLM-L6-v2` (~90MB, 384 dims) | Only if Azure OpenAI unavailable. Loaded on-demand, not at startup. |
| ❌ **Never** | `all-mpnet-base-v2`, DeBERTa-large, distilroberta | Too heavy for F1 tier (1GB RAM limit) |

### 3.5 DevOps
*   **Version Control:** GitHub
*   **CI/CD:** GitHub Actions → Azure Static Web Apps + Azure App Service
*   **Monitoring:** Azure Application Insights
*   **Secrets:** Azure Key Vault (free tier)
*   **Local Dev:** Docker (dev only, not deployed)

---

## 4. DATABASE SCHEMA

### 4.1 Cosmos DB Containers

#### 1. `Topics` (PK: `/topic_id`)
| Field | Type | Description |
| :--- | :--- | :--- |
| `query` | string | Original search query |
| `status` | string | `processing` / `complete` / `failed` |
| `anchor_ids` | string[] | References to anchor articles |
| `D_calibrated` | float | Final calibrated distortion score |
| `threat_matrix` | object | Precomputed 4D visualization data |
| `PAS_score` | float | Propagation anomaly score |
| `pattern_type` | string | `organic` / `coordinated` / `unknown` |
| `cache_ttl` | int | TTL in seconds |
| `created_at` | datetime | |

#### 2. `Articles` (PK: `/topic_id_shardN`)
Sharding: `shard = hash(article_id) % 4` — distributes load across 4 logical partitions per topic.
| Field | Type | Description |
| :--- | :--- | :--- |
| `url_hash` | string | Deduplication key |
| `source_credibility` | float | SCS score |
| `ASS` | float | Anchor Selection Score |
| `distortion_components` | object | `{S, E, C, D_raw}` |
| `blob_url` | string | Pointer to full text in Blob Storage |
| `clean_text_preview` | string | First 500 chars only (saves RU cost) |
| `embedding_id` | string | Reference to AI Search vector |

#### 3. `Claims` (PK: `/article_id`)
| Field | Type | Description |
| :--- | :--- | :--- |
| `original_sentence` | string | Raw extracted sentence |
| `normalized_claim` | string | GPT-4o normalized version |
| `candidacy_score` | float | Factuality + Specificity + Verifiability |
| `normalization_tier` | int | 1 (simple) or 2 (GPT-enhanced) |
| `negation_present` | bool | Negation detection flag |
| `entities` | string[] | Named entities in claim |
| `nli_result` | object | `{label, pass1_label, pass2_label, disagreement}` (GPT-4o-mini self-consistency) |
| `cluster_segment` | string | Bucket assignment (candidacy / outlier) |

#### 4. `GraphMetadata` (PK: `/topic_id`)
| Field | Type | Description |
| :--- | :--- | :--- |
| `node_count` | int | Total sources in graph |
| `edge_count` | int | Total relationships |
| `PAS_score` | float | Computed PAS |
| `pattern_type` | string | Classification result |
| `created_at` | datetime | |

#### 5. `GraphNodes` (PK: `/topic_id_shardN`)
Stores batches of 50 nodes per document.
| Field | Type | Description |
| :--- | :--- | :--- |
| `source_domain` | string | Domain name |
| `SCS` | float | Source credibility |
| `published_at` | datetime | |
| `geo_location` | string | Optional geolocation |

#### 6. `GraphEdges` (PK: `/topic_id_shardN`)
Stores batches of 50-100 edges per document.
| Field | Type | Description |
| :--- | :--- | :--- |
| `source` | string | Source node ID |
| `target` | string | Target node ID |
| `semantic_similarity` | float | Cosine similarity |
| `time_delta_minutes` | int | Publish time gap |
| `edge_weight` | float | Combined weight |
| `relationship_type` | string | `syndication` / `derivative` / `independent` |

#### 7. `GraphTimeline` (PK: `/topic_id`)
One document per time window.
| Field | Type | Description |
| :--- | :--- | :--- |
| `timestamp` | datetime | Window start |
| `PAS` | float | PAS at this point |
| `velocity` | float | Articles per hour |
| `coordination_signal` | float | Coordination tightness |

#### 8. `URLCache` (PK: `/url_hash`)
| Field | Type | Description |
| :--- | :--- | :--- |
| `url` | string | Original URL |
| `topic_id` | string | Reference |
| `result_ref` | string | Pointer to Topics doc |
| `created_at` | datetime | |
| `TTL` | int | Cosmos native TTL (auto-expire) |

#### 9. `CalibrationData` (PK: `/model_version`)
| Field | Type | Description |
| :--- | :--- | :--- |
| `GMM_boundaries` | object | Label-to-probability boundaries |
| `drift_metrics` | object | Historical KL values |
| `performance_metrics` | object | Precision, recall, F1 |
| `model_refs` | string[] | Blob Storage paths to `.pkl` files |

### 4.2 Azure Blob Storage (Free 5GB)
```text
/articles/
  {article_id}.txt          → full raw text

/models/
  isotonic_v{n}.pkl         → calibration isotonic model
  pchip_v{n}.pkl            → PCHIP interpolation model

/datasets/
  liar_processed.csv        → calibration training data (6-class)
  fakenewsnet.csv           → calibration training data (binary)
  multifc.csv               → multi-source fact-checking corpus
```

### 4.3 Azure AI Search Index
```text
Index: article-embeddings
─────────────────────────────────────
Fields:
  id              string (key)
  article_id      string (filterable)
  topic_id        string (filterable)
  published_at    datetime (filterable)
  embedding       vector (1536 dims)
  chunk_index     int32
  chunk_text      string

Vector Search:
  algorithm:      HNSW
  metric:         cosine
```

### 4.4 Caching Strategy (No Redis — Cosmos Only)

> **Architecture Decision (v2.1):** Redis removed from the stack. Azure Cache for Redis (C0 Basic) costs ~$13/month — over 11 months that exceeds the $100 student credit budget. Cosmos DB `URLCache` with native TTL provides <10ms point-read latency, which is sufficient for demo and production use.

*   **URL deduplication:** Cosmos `URLCache` container (PK: `/url_hash`, native TTL).
*   **In-memory LRU:** Python `functools.lru_cache` or `cachetools.TTLCache` on the FastAPI process for hot-path results. Lost on restart, but golden path topics are in Cosmos anyway.
*   **TTL:** 6 Hours (Standard), 1 Hour (Breaking News) — set via Cosmos native TTL.
*   ❌ **NEVER** store full articles or embeddings in cache — only `{D, PAS, Confidence, topic_id}`.

### 4.5 Query Patterns
| Query | Data Source | Access Pattern |
| :--- | :--- | :--- |
| All articles for topic X | Cosmos `Articles` (PK = `topic_id_shard*`) | Fan-out across 4 shards |
| Distortion score for article Y | Cosmos `Articles` (id = article_uuid) | Single doc read (instant) |
| Claim comparisons for topic X | Cosmos `Claims` (PK = `article_id`) | Batch read per article |
| PAS timeline for topic X | Cosmos `GraphTimeline` (PK = `topic_id`) | Single partition (fast) |
| Has URL been analyzed? | In-memory LRU → Cosmos `URLCache` fallback | Two-tier lookup (no Redis) |
| Threat matrix dashboard | Cosmos `Topics` (single doc, precomputed) | Instant |

---

## 5. API DESIGN

### 5.1 Base Configuration
```text
Base URL:  https://misinfo-forensics.azurewebsites.net/api/v1
Auth:      Header: x-api-key: <secret> (stored in Azure Key Vault)
           ❌ No JWT (unnecessary complexity for this scope)
```

### 5.2 Rate Limiting
| Endpoint | Limit | Implementation |
| :--- | :--- | :--- |
| `POST /analyze` | 10/hour | `slowapi` with in-memory backend (`cachetools.TTLCache`) |
| `GET` requests | 100/hour | Key: IP + API key (prevents shared IP abuse) |

### 5.3 Health Endpoints
| Method | Path | Purpose |
| :--- | :--- | :--- |
| `GET` | `/health` | Full status check (Cosmos, OpenAI, AI Search, Blob) |
| `GET` | `/health/ping` | `{"pong": true}` — used by keep-alive Azure Function |

### 5.4 Analysis Endpoints
**`POST /analyze`**
```
Header: Idempotency-Key: hash(query)
Body:
{
  "query": "Ukraine missile Kyiv",
  "mode": "full|fast",
  "options": {
    "include_claims": true,
    "include_graph": true,
    "max_articles": 12
  }
}
```
| Scenario | Code | Response |
| :--- | :--- | :--- |
| Cache hit | `200` | `{"status": "cached", "topic_id": "uuid", "result": {...}}` |
| Cache miss | `202` | `{"status": "processing", "topic_id": "uuid", "job_id": "uuid", "estimated_seconds": 25, "stream_url": "/jobs/uuid/stream", "poll_url": "/jobs/uuid/status"}` |
| Duplicate (idempotency) | `200` | `{"status": "existing_job", "job_id": "uuid"}` |

**`GET /analyze/{topic_id}`** → Full completed analysis result.

### 5.5 Fast Mode Behavior
| Feature | Full Mode | Fast Mode |
| :--- | :--- | :--- |
| PAS (propagation) | ✅ | ❌ `null` |
| Tier 2 claim normalization | ✅ | ❌ skipped |
| NLI self-consistency (Pass 2) | ✅ | ❌ single-pass only |
| Max anchor articles | 5+ | 3 |
| Max claims per article | 15 | 5-7 |
| Calibration (Isotonic + PCHIP) | ✅ | ✅ (always runs — required for Uncertainty Clip) |
| Latency | 20-30s | 3-8s |
| Output | Full D + PAS + Confidence | Calibrated D (no PAS) + higher uncertainty flag |

### 5.6 Streaming (Primary — SSE)
**`GET /jobs/{job_id}/stream`** → `text/event-stream` via FastAPI `StreamingResponse`

**Event Format:**
```json
{"stage": "fetching",    "progress": 20,  "message": "Retrieving articles..."}
{"stage": "claims",      "progress": 45,  "message": "Extracting claims..."}
{"stage": "distortion",  "progress": 70,  "message": "Computing S, E, C..."}
{"stage": "graph",       "progress": 85,  "message": "Building PAS graph..."}
{"stage": "complete",    "progress": 100, "result": {...}}
{"stage": "error",       "message": "...", "partial_result": {...}}
```

### 5.7 Polling (Fallback)
**`GET /jobs/{job_id}/status`** → Poll every 2 seconds. Returns current stage + progress. Cannot break.

### 5.8 Resource Endpoints
| Method | Path | Parameters | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/topics/{topic_id}/articles` | `?is_anchor=true&sort=ASS&limit=12` | List articles for topic |
| `GET` | `/articles/{article_id}` | — | Full article + claims |
| `GET` | `/articles/{article_id}/claims` | — | All claims + NLI results |
| `GET` | `/topics/{topic_id}/graph` | `?include_edges=true&max_nodes=50` | PAS graph data |
| `GET` | `/topics/{topic_id}/graph/timeline` | — | PAS over time + pattern type |
| `GET` | `/dashboard` | `?limit=20&sort=D_calibrated` | All topics + threat matrix data |
| `GET` | `/cache/status` | — | Cache hit/miss stats |
| `DELETE` | `/cache/{topic_id}` | — | Invalidate cached topic |
| `GET` | `/calibration/status` | — | Current model version + drift metrics |
| `POST` | `/calibration/trigger` | — | Admin only: retrain calibration model |

### 5.9 Error Shape (The "Never 500" Rule)
```json
{
  "status": "degraded",
  "degraded_components": ["PAS", "E"],
  "confidence_adjusted": true,
  "partial_result": {...},
  "available_components": ["S", "C"],
  "timestamp": "2026-04-14T04:00:00Z"
}
```

**HTTP Codes:**
| Code | Meaning |
| :--- | :--- |
| `200` | Success |
| `202` | Accepted (async processing) |
| `400` | Bad request |
| `404` | Not found |
| `429` | Rate limited |
| `503` | Degraded (never 500) |

---

## 6. PHASE ARCHITECTURE

*   **Phase 1 (Foundation):** Setup Azure Infrastructure, FastAPI scaffolding, Cosmos DB CRUD, API Auth, Health endpoints.
*   **Phase 2 (Inference):** Integrate Azure OpenAI, implement S and E component scoring, Anchor Selection logic, Genre Classifier.
*   **Phase 3 (Forensics):** Implement C Component (NLI + Reconciliation), Hybrid Claim Sampling, PAS graph, Syndication Detection.
*   **Phase 4 (UX/Polish):** Build Chrome Extension, D3.js Threat Matrix, SSE Streaming, Golden Path Cache, INDETERMINATE state.

---

## 7. DEMO STRATEGY

### 7.1 Golden Path Topics
The system will ship with 25 pre-analyzed topics (e.g., "Deepfake Election Video," "Kyiv Missile Strike") stored in Cosmos.
*   **Benefit:** Zero-latency demo; protects against API rate limits during live judge Q&A.

### 7.2 Observability Demo
Open **Azure Application Insights** during the presentation to show:
1.  **Live Metrics Stream:** Real-time request traffic.
2.  **Failure Map:** Visual proof of graceful degradation when a service is mock-disabled.
3.  **Latency Distribution:** Proof of "Golden Path" vs. "Live Pipeline" speed.
