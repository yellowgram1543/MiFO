# MiFO: Advanced Misinformation Analysis
### Semantic Evolution & Propagation Modeling Framework (v2.0)

## 1. Executive Abstract
MiFO (Misinformation Forensics) is an advanced, multidimensional analysis framework designed to combat the "Evolution Problem" in digital misinformation. Traditional detection methods rely on static classification—binary "True/False" labels that fail to account for how news stories evolve, distort, and become weaponized over time. MiFO shifts the paradigm from static verification to **Semantic Evolution Tracking** and **Coordinated Propagation Modeling.**

The system operates on a **Dynamic Multi-Anchor** architecture. Instead of comparing claims against a static, fallible database of "truth," MiFO identifies high-credibility source clusters to form a moving "ground truth" (the Anchor Set). It then calculates the **Distortion Score ($D$)** of target articles by measuring three atomic vectors: **Semantic Drift ($S$)**, which captures changes in core meaning; **Emotional Amplification ($E$)**, which detects manipulative framing; and **Factual Contradiction ($C$)**, which uses DeBERTa-based NLI to identify explicit conflicts.

To distinguish between organic viral news and malicious campaigns, MiFO employs a **Propagation Anomaly Score ($PAS$)**. This graph-based model analyzes velocity, coordination tightness, and source diversity to flag coordinated inauthentic behavior (CIB). The v2.0 architecture introduces **Adversarial Resilience** layers, including Hybrid Claim Sampling to defeat "Gish Gallop" tactics, and Syndication Whitelisting to prevent false positives from legitimate wire services like AP and Reuters.

The framework is built as a cloud-native, Azure-optimized ecosystem. It utilizes **Azure OpenAI (GPT-4o)** for high-reasoning NLI, **Azure AI Search** for managed vector similarity, and **Cosmos DB** for high-throughput metadata storage. Results are delivered via an interactive **4D Threat Matrix**, a D3.js visualization that maps Source Trust, Distortion Intensity, System Confidence, and Propagation Abnormality into a single, actionable forensic dashboard. 

MiFO is engineered for high performance and low cost, utilizing a "Golden Path" caching strategy and serverless orchestration to maintain a sustainable footprint for the Microsoft Imagine Cup 2027.

---

## 2. The Finalized Formulas (Locked v2.0)

### A. Distortion Score ($D$)
Calculates the level of semantic and factual drift in an article.
$$D = 0.20S + 0.25E + 0.55C$$
*   **$S$ (Semantic Drift):** $1 - \text{cosine}(\text{article}, \text{weighted\_anchor})$.
*   **$E$ (Emotional Amp):** $(0.5 \times \text{emotion} + 0.3 \times \text{certainty} + 0.2 \times \text{moral\_framing}) \times W_{dir}$.
*   **$C$ (Factual Contradiction):** $\frac{\sum (\text{NLI}_i \times \text{Weight}_i)}{\sum \text{Weight}_i}$, where $\text{Weight}_i = 1 + \max(0, \text{AnchorDistance}_i)$. NLI labels: Contradiction=1, Neutral=0.15, Entailment=0.

### B. Anchor Selection Score ($ASS$)
Identifies high-credibility articles to form the "Anchor Set."
$$ASS = 0.35 \times \text{SourceCredibility} + 0.30 \times \text{Recency} + 0.20 \times \text{ContentMaturity} + 0.15 \times \text{Consensus}$$

### C. Propagation Anomaly Score ($PAS$)
Detects coordinated inauthentic behavior (CIB) and bot-driven amplification.
$$PAS = 0.35 \times \text{Velocity} + 0.30 \times (\text{Coordination} \times [1 - \text{mean\_SCS}]) + 0.20 \times \text{Diversity} + 0.15 \times \text{Clustering}$$

---

## 3. Adversarial Defenses (The "Reviewer-Proof" Layer)

| Vulnerability | v2.0 Patch Implementation |
| :--- | :--- |
| **Anchor Poisoning** | **Dynamic Eligibility:** Threshold for anchor entry drops as $Stability$ decreases (breaking news), but imposes a "Hard Floor" ($SCS < 0.7$ caps Confidence at 0.4). |
| **Syndication Trap** | **Graduated Whitelist + Impersonation Defense (v2.1):** Linear interpolation from $ParaSim = 0.80$ to $0.92$. **v2.1 Patch:** If $ParaSim > 0.92$ but domain $\notin$ `SYNDICATION_WHITELIST`, flags as `IMPERSONATION_DETECTED` and amplifies PAS penalty by 1.5×. |
| **Satire/Opinion** | **Genre-Aware Gating (v2.1):** Opinion weights rebalanced: $W_s=0.25, W_e=0.35, W_c=0.40$ (captures emotional manipulation). Satire is excluded from the Threat Matrix and flagged with an out-of-band banner. |
| **NLP Hallucination** | **Confidence Tiers:** Coreference resolution is only used for Factual ($C$) scoring if confidence $> 0.85$. Proportional penalty to global confidence for ambiguous text. |
| **Gish Gallop** | **Hybrid Sampling:** 40% of claims are selected based on max semantic distance from anchor, ensuring "buried lies" are always evaluated. |
| **Weak-Data Overconfidence** | **Uncertainty Clip (v2.0):** If $Confidence < 0.4$, the $D$ score is linearly pulled toward $0.5$ ("I Don't Know" center) to prevent confident-looking reports based on weak data. |

---

## 4. Technical Architecture (Azure Ecosystem)

### Backend (FastAPI on Azure App Service F1)
*   **Streaming:** SSE (Server-Sent Events) for real-time analysis progress.
*   **Idempotency:** Request hashing to prevent redundant NewsAPI calls.
*   **Fail-Safe:** Graceful degradation; returns partial results instead of 500 errors.

### AI Services (Azure AI Stack)
*   **Azure OpenAI (gpt-4o-mini):** NLI scoring, Moral framing, Tier-2 Claim Normalization.
*   **Azure AI Search:** Managed vector storage for semantic similarity (HNSW/Cosine).
*   **Azure AI Language:** NER and Key Phrase extraction.

### Data & Persistence (Cosmos DB + Blob)
*   **Cosmos DB:** Partitioned by `topic_id` for $O(1)$ retrieval of dashboards.
*   **Azure Blob Storage:** Long-term storage for raw article text and calibration datasets.
*   **Redis Cache:** Ephemeral storage for quick URL lookups.

---

## 5. User Interface & Observability

### The 4D Threat Matrix
A D3.js visualization mapping four dimensions of data:
1.  **X-Axis:** Source Trust (SCS).
2.  **Color:** Distortion Intensity (D-Calibrated).
3.  **Opacity:** System Confidence (based on claim count/NLI consistency). Applies **Uncertainty Clip** when $Conf < 0.4$. Renders as **INDETERMINATE** (grey, `?` tooltip) when $Conf < 0.15$.
4.  **Size:** Propagation Abnormality (PAS).

### Observability
*   **Azure Application Insights:** Real-time monitoring of latency, success rates, and dependency health.
*   **KL-Drift Monitoring:** Weekly monitoring of live data distributions vs. training data for recalibration.

---

## 6. Financial Sustainability (MIC Ready)
*   **Operating Cost:** ~$5-8/month (primarily Azure OpenAI tokens).
*   **Runway:** 20-30 months using $100 Student Credits.
*   **Scalability:** Zero-persistent workers; scale-to-zero capability with Azure Functions.
