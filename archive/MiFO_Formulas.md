# MiFO v2.0: Atomic Formula Reference

This document serves as the exhaustive mathematical and logical specification for the MiFO (Misinformation Forensics) framework.

---

### 1. Stability Engine (v1.6)
**Purpose:** Quantifies the level of consensus or chaos within the current information topic to modulate system strictness.
**Formula:** 
$$Stability = \begin{cases} 0.3, & \text{if } N < 3 \\ \max(0.3, 1 - Div), & \text{if } N \ge 3 \end{cases}$$
**Variables:**
| Symbol | Name | Type | Range | Computation | Feeds Into |
| :--- | :--- | :--- | :--- | :--- | :--- |
| $N$ | Article Count | int | $[0, \infty)$ | Count of unique articles in topic cluster. | Stability Branching |
| $Div$ | Embedding Divergence | float | $[0, 1]$ | $\min(1.0,\; \text{Var}(\text{cosine\_similarities}) \;/\; 0.25)$. $\text{MaxVar} = 0.25$ (theoretical max for any distribution on $[0, 1]$, achieved by Bernoulli at extremes). **v2.1 Fix:** Previous $\text{MaxVar} = 1.0$ collapsed Stability to $\approx 1.0$ in all cases. | Stability |
| $Stability$ | Stability Score | float | $[0.3, 1]$ | Degree of cross-source consensus. | Anchor Threshold ($T_{dyn}$) |

**Logic Gates:**
```python
if N < 3:
    Stability = 0.3 # Basal Information Noise floor
else:
    Stability = max(0.3, 1 - Div)
```
**Failure Modes:** Sparse data ($N < 3$) forces a "low stability" state, which lowers the bar for anchor selection.
**Floor Justification (v2.0) [POLICY]:** In a cluster of $N < 3$, there is insufficient cross-validation to establish a "Stable" state. $0.3$ is an **engineered prior** (not a derived constant) representing "Basal Information Noise"—the system acknowledges it is in speculative mode, and all downstream thresholds ($T_{dyn}$) adjust accordingly.
**Dependencies:** Article embeddings (Azure AI Search).
**Feeds Into:** Dynamic Anchor Threshold ($T_{dyn}$).

---

### 2. Anchor Selection Score (ASS) (v2.0)
**Purpose:** Ranks and filters articles to identify the high-credibility "Anchor Set" (Ground Truth).
**Formula:** 
$$ASS = 0.35(SCS) + 0.30(Recency) + 0.20(Maturity) + 0.15(Consensus)$$
**Variables:**
| Symbol | Name | Type | Range | Computation | Feeds Into |
| :--- | :--- | :--- | :--- | :--- | :--- |
| $SCS$ | Source Credibility | float | $[0, 1]$ | Lookup from domain-authority registry. **Source (v2.1):** Configurable; default options include NewsGuard API, Media Bias/Fact Check, or manual curation. Registry is periodically updated (minimum: monthly) and versioned in Cosmos DB. | ASS |
| $Recency$ | Recency Score | float | $[0, 1]$ | $e^{-\lambda \Delta t}$ where $\Delta t$ is hours since first report. $\lambda = \ln(2) / T_{half}$, with default $T_{half} = 24\text{h}$ (article relevance halves every 24 hours). **Note:** Higher value = more recent = higher score (not a penalty). | ASS |
| $Maturity$ | Content Maturity (Entity Density) | float | $[0, 1]$ | $\min(1.0,\; \frac{\text{Count(Unique\_Entities)}}{\text{Word\_Count}} \times SF)$, where $SF = 1 / \max(0.01,\; \mu(\text{EntityDensity}_{anchors}))$. Floor on $\mu$ prevents division-by-near-zero. | ASS |
| $Consensus$ | Inter-Article Consensus | float | $[0, 1]$ | Mean cosine similarity to other articles. | ASS |

**Logic Gates:**
```python
# Layer 1: Dynamic Eligibility
T_dyn = 0.6 - 0.2 * (1 - Stability)
eligible = [a for a in articles if a.SCS >= T_dyn]

# Layer 1.5: Empty-Set Guard (v2.1)
if not eligible:
    return State.UNANCHORABLE  # Pipeline halts; no anchor set possible

# Layer 2: Confidence Penalties
max_scs = max(a.SCS for a in eligible)  # Safe: eligible is non-empty
if max_scs < 0.75:
    Confidence *= 0.8 # Mid-tier penalty
if max_scs < 0.7:
    Confidence = min(Confidence, 0.4) # Hard Floor (Safety)
```
**Failure Modes:** No articles pass $T_{dyn}$ $\to$ State: `UNANCHORABLE` (Pipeline halts or reverts to low-confidence mode).
**Dependencies:** Source Database, Timestamps, Stability Score.
**Feeds Into:** Weighted Anchor Embedding.

**Weighted Anchor Embedding (v2.1):**
$$\text{weighted\_anchor} = \frac{\sum_{i \in \text{AnchorSet}} \text{ASS}_i \cdot \text{embedding}_i}{\sum_{i \in \text{AnchorSet}} \text{ASS}_i}$$
Anchors contribute to the consensus embedding proportionally to their ASS score. High-credibility, recent, entity-dense articles dominate the anchor vector. The resulting embedding is used as the reference point for $S$ (Semantic Drift) and claim-level $AnchorDistance$ calculations.

---

### 3. Claim Extraction Pipeline (v1.6)
**Purpose:** Selects the most factual and verifiable sentences for NLI analysis.
**Formula:** 
$$Candidacy = 0.40(Factuality) + 0.35(Specificity) + 0.25(Verifiability)$$
**Variables:**
| Symbol | Name | Type | Range | Computation | Feeds Into |
| :--- | :--- | :--- | :--- | :--- | :--- |
| $Fact$ | Factuality Signal | float | $[0, 1]$ | NER density + verb-tense check (spaCy). | Candidacy |
| $Spec$ | Specificity Signal | float | $[0, 1]$ | Count of temporal/numerical markers. | Candidacy |
| $Verif$ | Verifiability | float | $[0, 1]$ | Cross-referenceable entity count. | Candidacy |

**Logic Gates:**
```python
threshold = 0.6
selected_claims = [s for s in sentences if candidacy(s) > threshold]

# v2.1: Cap depends on available sentences, not a fixed floor
cap = max(1, min(len(selected_claims), min(15, article_length // 200)))

# Short-text fallback
if len(selected_claims) == 0:
    selected_claims = []  # Empty set; TextAdequacy penalty applied
```
**Failure Modes:** Very short articles or articles with no factual claims $\to$ returns empty set (handled by `TextAdequacy` penalty in Confidence Score).
**Dependencies:** spaCy NER, Tense analysis.
**Feeds Into:** NLI Engine ($C$ Component).

---

### 4. Coreference Resolution Gates (v2.0)
**Purpose:** Prevents pronoun-resolution errors from polluting factual analysis.
**Formula:** $RC \in [0, 1]$ (Resolution Confidence)
**RC Heuristic (v2.1 — Deterministic Definition):**
| Condition | $RC$ Value | Rationale |
| :--- | :--- | :--- |
| Pronoun and antecedent in **same sentence** | $1.0$ | Syntactically unambiguous resolution. |
| Antecedent in **different sentence** (proper noun) | $0.9 - 0.05 \times \text{sentence\_distance}$ | Confidence decays with distance. Floor: $0.5$. |
| Antecedent is a **common noun** (e.g., "the company") | $0.7$ | Referential ambiguity discount. |
| **Ambiguous antecedent** (multiple candidate entities) | $0.5$ | Coin-flip mapping; too risky for factual scoring. |
| Resolution **failed** / no antecedent found | $0.0$ | Full fallback to original sentence. |

**Variables:**
| Symbol | Name | Type | Range | Computation | Feeds Into |
| :--- | :--- | :--- | :--- | :--- | :--- |
| $RC$ | Resolution Confidence | float | $[0, 1]$ | Deterministic heuristic (see table above), modulated by `TextAdequacy`. | Usage Logic |

**Logic Gates:**
```python
# RC Calculation (v2.1)
if same_sentence:
    RC = 1.0
elif antecedent_is_proper_noun:
    RC = max(0.5, 0.9 - 0.05 * sentence_distance)
elif antecedent_is_common_noun:
    RC = 0.7
elif multiple_candidate_entities:
    RC = 0.5  # Ambiguous antecedent
else:
    RC = 0.0  # Resolution failed

# Usage Tiers
if RC >= 0.85:
    # High Trust Tier
    use(resolved_sentence) for [S, E, C]
elif RC >= 0.65:
    # Factual Protection Tier
    use(resolved_sentence) for [S, E]
    use(original_sentence) for [C] # Safeguard Facts
else:
    # Fallback Tier
    use(original_sentence) for [S, E, C]
```
**Failure Modes:** Resolution errors at $RC > 0.85$ $\to$ Manufacturing of false "lies."
**Dependencies:** `TextAdequacy`, neuralcoref / spaCy coref.
**Feeds Into:** Distortion Components (S, E, C), Global Confidence Penalty.

---

### 5. Gish Gallop Defense (Hybrid Sampling) (v2.0)
**Purpose:** Ensures "buried lies" are detected by sampling based on semantic drift, not just factuality.
**Logic Gates:**
```python
# Bucket 1: Top Candidacy (60% of slots)
# Bucket 2: Top AnchorDistance (40% of slots)
# AnchorDistance = clamp(1 - cosine(claim, anchor_embedding), 0, 1)  # v2.1: clamped

selected = deduplicate(bucket1 + bucket2)[:cap]

# Guaranteed Outlier Slot
most_distant_claim = max(all_claims, key=lambda c: c.anchor_distance)
if most_distant_claim not in selected:
    selected[-1] = most_distant_claim
    selected[-1].forced_outlier = True
```
**Dependencies:** Anchor Embedding, Candidacy Scores.
**Feeds Into:** $C$ Component (Factual Contradiction).

---

### 6. S Component: Semantic Drift (v1.5)
**Purpose:** Measures how the article's core meaning deviates from the anchor set.
**Formula:** 
$$S = \text{clamp}(1 - \text{cosine}(\text{article\_embedding}, \text{weighted\_anchor}),\; 0,\; 1)$$
**Range Safety (v2.1):** Cosine similarity for text embeddings is typically in $[0, 1]$, but is not mathematically guaranteed. Explicit clamping ensures $S \in [0, 1]$ regardless of embedding model behavior.
**Variables:**
| Symbol | Name | Type | Range | Computation | Feeds Into |
| :--- | :--- | :--- | :--- | :--- | :--- |
| $S$ | Semantic Drift | float | $[0, 1]$ | $\max(0, \min(1, 1 - \text{cosine\_sim}))$. Clamped. | Distortion Score ($D$) |

**Dependencies:** Azure OpenAI Embeddings (text-embedding-3-small).
**Feeds Into:** Distortion Score ($D$).

---

### 7. E Component: Emotional Amplification (v1.7)
**Purpose:** Detects manipulative emotional, moral, or certainty-based framing.
**Formula:** 
$$E = (0.5 \cdot \text{emotional} + 0.3 \cdot \text{certainty} + 0.2 \cdot \text{moral\_framing}) \times W_{dir}$$
**Variables:**
| Symbol | Name | Type | Range | Computation | Feeds Into |
| :--- | :--- | :--- | :--- | :--- | :--- |
| $Emo$ | Emotional Amp | float | $[0, 1]$ | $\max(0,\; \text{article\_emo} - \text{anchor\_emo})$. Non-negative by construction. | E |
| $Cert$ | Certainty Inflation | float | $[0, 1]$ | $\max(0,\; \text{article\_certainty} - \text{anchor\_certainty})$. **v2.1:** Explicitly clamped non-negative. Measures upward shift in epistemic certainty markers. | E |
| $Moral$ | Moral Density | float | $[0, 1]$ | $\max(0,\; \text{article\_moral} - \text{anchor\_moral})$. **v2.1:** Explicitly clamped non-negative. Measures upward shift in moral foundations dictionary density. | E |
| $W_{dir}$ | Directional Weight (Correction Discount) | float | $\{1.0, 0.6\}$ | 1.0 if amplifying, 0.6 if de-escalating. **Justification:** De-escalation (e.g., "It wasn't a bomb") is a standard forensic correction pattern. The 40% discount reflects this asymmetry. | E |

**Logic Gates:**
```python
# v2.1: All sub-components are non-negative; E_linear is guaranteed >= 0
E_linear = max(0, 0.5 * Emo + 0.3 * Cert + 0.2 * Moral)  # Belt-and-suspenders clamp

# Direction detection: is the article amplifying or correcting?
if article_E > anchor_E:
    W_dir = 1.0  # Amplifying
else:
    W_dir = 0.6  # De-escalating (Correction Discount)

E_directed = E_linear * W_dir

# Gamma Scaling (Locked Trigger v2.0)
# Purpose: Non-linear noise suppression — attenuates moderate emotional
# signals while preserving genuine outliers. Exponent > 1 on [0,1]
# compresses low/mid values more than high values.
gamma_on = (Stability > 0.7) and (article_E > max(0.15, 1.5 * anchor_E))
if gamma_on:
    E = E_directed ** 1.3  # Noise suppression: moderate E crushed, high E preserved
else:
    E = E_directed  # Linear mode
```
**Range Safety (v2.1):** All three sub-components ($Emo$, $Cert$, $Moral$) are explicitly clamped to $\ge 0$, and $E_{linear}$ has a belt-and-suspenders $\max(0, \ldots)$ clamp. Combined with $W_{dir} \in \{0.6, 1.0\}$ and gamma exponent on $[0, 1]$, $E \in [0, 1]$ is guaranteed.
**Dependencies:** Azure OpenAI GPT-4o-mini (structured JSON output for emotion, certainty, and moral framing scores). **v2.1 Architecture Decision:** All emotion/moral inference offloaded to GPT-4o-mini to stay within F1 App Service RAM limits (1GB). Local models (distilroberta, MFD 2.0) were removed from the deployment target. The mathematical formulas are model-agnostic — only the output scores matter.
**Feeds Into:** Distortion Score ($D$).

---

### 8. C Component: Factual Contradiction (v2.0)
**Purpose:** Measures explicit factual conflicts between the article and the anchors.
**Formula:** 
$$C = \frac{\sum (\text{Contradiction}_i \times \text{Weight}_i)}{\sum \text{Weight}_i}$$
**Variables:**
| Symbol | Name | Type | Range | Computation | Feeds Into |
| :--- | :--- | :--- | :--- | :--- | :--- |
| $AnchorDist_i$ | Clamped Anchor Distance | float | $[0, 1]$ | $\text{clamp}(1 - \text{cosine}(\text{claim}_i, \text{anchor}),\; 0,\; 1)$. **v2.1:** Clamped to prevent range violation. | Weight Calc |
| $Weight_i$ | Outlier Weight | float | $[1, 2]$ | $1.0 + AnchorDist_i$. Range guaranteed by clamped input. | Weighted Mean C |
| $Contradict_i$ | NLI Label | float | $\{0, 0.15, 1\}$ | NLI output (see logic below). | Weighted Mean C |

**NLI Self-Consistency Check (v2.1):**
```python
# Architecture Decision: All NLI via GPT-4o-mini (no local DeBERTa).
# DeBERTa-large-mnli (~1.5GB) cannot run on F1 App Service (1GB RAM).
# Self-consistency replaces cross-model reconciliation.

# Pass 1: Standard NLI prompt
label_1 = gpt4o_nli(
    prompt="Does the claim contradict, entail, or neither with the anchor?",
    claim=claim, anchor=anchor,
    response_format={"label": "entailment|neutral|contradiction"}
)

# Pass 2: Inverted framing (adversarial check)
label_2 = gpt4o_nli(
    prompt="Does the anchor support or refute the claim?",
    claim=claim, anchor=anchor,
    response_format={"label": "entailment|neutral|contradiction"}
)

if label_1 == label_2:
    final_label = label_1  # Self-consistent: high trust
else:
    # Disagreement: use the more conservative label
    final_label = max(label_1, label_2, key=severity)  # contradiction > neutral > entailment
    claim.nli_disagreement = True  # Feeds into NLI_Consist penalty
```

**Label Values:**
```python
# If claim contradicts anchor -> value = 1
# If claim entails anchor -> value = 0
# If neutral -> value = 0.15 [CALIBRATED] (Topical Tangent discount; neutrality ≠ contradiction)
```
**Dependencies:** Azure OpenAI GPT-4o-mini (structured JSON), Hybrid Sampling logic.
**Feeds Into:** Distortion Score ($D$).

---

### 9. Distortion Score D (v2.0)
**Purpose:** The final uncalibrated measure of article distortion.
**Formula:** 
$$D = W_s S + W_e E + W_c C$$
**Genre Variants:**
| Genre | $W_s$ | $W_e$ | $W_c$ |
| :--- | :--- | :--- | :--- |
| **News** | 0.20 | 0.25 | 0.55 |
| **Opinion** | 0.25 | 0.35 | 0.40 |
| **Analysis** | 0.25 | 0.20 | 0.55 |

**Logic Gates:**
```python
if genre == "satire":
    display_mode = "BANNER_ONLY" # No D calculation
```

**Genre Classifier (v2.1):**
```python
# Classification Method: GPT-4o-mini zero-shot with structured output
genre = gpt4o_mini(
    prompt="Classify this article as exactly one of: News, Opinion, Analysis, Satire.",
    article_text=article.first_500_words,
    response_format={"genre": "enum[News, Opinion, Analysis, Satire]"}
)

# Fallback: if API fails or confidence is low, default to News (strictest weights)
if genre is None or genre not in VALID_GENRES:
    genre = "News"  # Safe default: highest C weight
```
**Dependencies:** S, E, C components, Genre Classifier (GPT-4o-mini).
**Feeds Into:** Calibration Engine.

---

### 10. Calibration (v1.8)
**Purpose:** Maps raw $D$ scores to human-interpretable probabilities.
**Formula:** 
$$D_{calibrated} = \text{PCHIP}(\text{Isotonic}(D_{raw}))$$
**Monotonicity Guarantee (v2.1):** Uses **Piecewise Cubic Hermite Interpolating Polynomial (PCHIP)** instead of unconstrained cubic spline. PCHIP preserves the monotonicity of the isotonic regression output, ensuring higher raw $D$ always maps to higher calibrated $D$. A generic cubic spline can introduce non-monotonic artifacts, breaking the probability interpretation.
**Logic Gates:**
```python
from scipy.interpolate import PchipInterpolator

# Step 1: Isotonic Regression (monotone staircase)
isotonic_D = isotonic_model.predict(D_raw)

# Step 2: PCHIP smoothing (monotone-preserving)
pchip = PchipInterpolator(isotonic_x, isotonic_y)
D_calibrated = pchip(isotonic_D)

# Note: GMM boundaries from LIAR/FakeNewsNet are used only during
# isotonic model TRAINING to establish the label-to-probability mapping.
# At inference time, the trained isotonic + PCHIP pipeline handles
# the full D_raw -> D_calibrated mapping end-to-end.
```
**Dependencies:** Pre-trained Isotonic Regression + PCHIP interpolation (scipy). Training data: LIAR dataset (6-class labels) and FakeNewsNet (binary labels), mapped to continuous distortion probabilities via GMM-derived boundaries.
**Feeds Into:** Threat Matrix (Color).

---

### 11. Confidence Score (v2.0)
**Purpose:** Quantifies system trust in the generated analysis.
**Formula:** 
$$Conf = 0.35(AnchorQuality) + 0.25(EffectiveVolume) + 0.20(NLI\_Consist) + 0.20(TextAdequacy)$$
**Sub-Variable Definitions:**
| Symbol | Name | Type | Range | Computation |
| :--- | :--- | :--- | :--- | :--- |
| $AnchorQuality$ | Anchor Set Quality | float | $[0, 1]$ | Mean $SCS$ of all articles in the final Anchor Set. |
| $EffectiveVolume$ | Effective Claim Volume | float | $[0, 1]$ | $\min(1.0,\; \text{claims\_analyzed} \;/\; 10)$. Saturates at 10 claims; penalizes thin analysis. |
| $NLI\_Consist$ | NLI Consistency | float | $[0, 1]$ | If claims $\ge 2$: $1 - \text{StdDev}(\text{NLI\_scores})$. If claims $< 2$: $0.5$ (pessimistic default; single-claim "consistency" is not meaningful). |
| $TextAdequacy$ | Text Adequacy | float | $[0, 1]$ | $\min(1.0,\; \text{Word\_Count} \;/\; 300)$. Penalizes ultra-short articles where NLP models underperform. |

**Penalty Modifiers:**
1.  **Anchor Floor Penalty:** If max(SCS) < 0.7, $Conf = \min(Conf, 0.4)$.
2.  **Coref Penalty:** $Conf \times= (1 - \min(0.40, \text{failure\_rate} \times 0.5))$.
3.  **Uncertainty Clip (v2.0):** If $Conf < 0.4$, the Distortion Score $D$ is linearly pulled toward $0.5$.
    **Execution Order:** Runs AFTER calibration (Section 10), since $0.5$ only has semantic meaning ("50% distortion probability") in calibrated probability space.
    ```python
    # Runs on D_calibrated, not D_raw
    if Confidence < 0.15:
        # INDETERMINATE state (v2.1): System has near-zero trust
        D_Display_State = "INDETERMINATE"
        D_clipped = 0.5
        D_clipped.color_override = "#808080"  # Grey — not a risk color
        D_clipped.tooltip = "Insufficient data for analysis"
    elif Confidence < 0.4:
        pull_strength = 1 - (Confidence / 0.4)  # 1.0 at Conf=0.15, 0.0 at Conf=0.4
        D_clipped = D_calibrated + pull_strength * (0.5 - D_calibrated)
        D_Display_State = "UNCERTAIN"
    else:
        D_clipped = D_calibrated
        D_Display_State = "NORMAL"
    ```
    **Justification:** Prevents confident-looking reports based on weak data. The **INDETERMINATE** state ($Conf < 0.15$) prevents faintly visible amber dots that could be misread as moderate risk assessments.

**Dependencies:** SCS scores, claim counts, coreference RC scores, calibrated $D$.
**Feeds Into:** Threat Matrix (Opacity), Distortion Score ($D_{calibrated}$) via Uncertainty Clip.

---

### 12. Propagation Anomaly Score (PAS) (v1.6)
**Purpose:** Detects coordinated, abnormal dissemination patterns.
**Formula:** 
$$PAS = 0.35(VelocityAnom) + 0.30(Coordination \times [1 - \text{mean\_SCS}]) + 0.20(Diversity) + 0.15(Clustering)$$
**Sub-Variable Definitions (v2.1):**
| Symbol | Name | Type | Range | Computation |
| :--- | :--- | :--- | :--- | :--- |
| $VelocityAnom$ | Velocity Anomaly | float | $[0, 1]$ | $\min(1.0,\; \text{articles\_per\_hour} \;/\; \text{topic\_baseline\_rate})$. `topic_baseline_rate` = 30-day rolling average of articles/hour for this topic category, stored in Cosmos DB and updated daily. | 
| $Coordination$ | Coordination Tightness | float | $[0, 1]$ | $\text{clamp}(1 - \text{StdDev}(\text{publish\_timestamps}) \;/\; \text{topic\_timespan},\; 0,\; 1)$. High value = tightly clustered in time. |
| $Diversity$ | Source Diversity (Inverse) | float | $[0, 1]$ | $1 - (\text{unique\_domains} \;/\; N)$. Low diversity (few unique sources) = high score = more suspicious. |
| $Clustering$ | Network Clustering Coefficient | float | $[0, 1]$ | Average clustering coefficient of the co-link graph: nodes = source domains, edges = shared outbound hyperlinks or social media amplifier accounts. $CC = \frac{2 \times \text{triangles}}{\text{triplets}}$. Standard graph metric with well-defined $[0, 1]$ range. |

**Logic Gates:**
```python
if N < 5:
    PAS = None  # Insufficient data; Threat Matrix renders no radius
elif N < 10:
    # Simplified: only Diversity and Velocity (Coordination/Clustering unreliable)
    PAS = 0.50 * VelocityAnom + 0.50 * Diversity
else:
    PAS = 0.35 * VelocityAnom + 0.30 * (Coordination * (1 - mean_SCS)) + 0.20 * Diversity + 0.15 * Clustering
```
**Dependencies:** Article metadata (Source, Timestamp, Domain, external links).
**Feeds Into:** Threat Matrix (Radius/Size).

---

### 13. Syndication Detection (v2.0)
**Purpose:** Whitelists legitimate wire services (AP/Reuters) to prevent false PAS penalties.
**Formula:** 
$$Score = 0.5(ParaSim) + 0.3(DocSim) + 0.2(CredSignal)$$
**Thresholds (Linear Interpolation v2.0):**
*   $ParaSim > 0.92 \to$ `WhitelistWeight = 1.0` (Full Whitelist).
*   $0.80 < ParaSim \le 0.92 \to$ `WhitelistWeight = (ParaSim - 0.80) / 0.12` (Graduated).
*   $ParaSim \le 0.80 \to$ `WhitelistWeight = 0.0` (No Whitelist).
*   Final Status: $Score > 0.7 \to$ `STATUS: SYNDICATED`.

**Logic Gates:**
```python
# Configurable whitelist of legitimate syndication partners
SYNDICATION_WHITELIST = ["apnews.com", "reuters.com", ...registered_partners]

# Step 1: Source Domain Check (v2.1 Impersonation Defense)
if domain in ["apnews.com", "reuters.com"]:
    status = "SOURCE_IS_ANCHOR"  # Don't analyze as target
    return

# Step 2: Graduated Whitelist
if ParaSim > 0.92:
    whitelist_weight = 1.0
elif ParaSim > 0.80:
    whitelist_weight = (ParaSim - 0.80) / 0.12
else:
    whitelist_weight = 0.0

# Step 3: Impersonation Detection (v2.1)
if whitelist_weight > 0.5 and domain not in SYNDICATION_WHITELIST:
    # High content similarity from unknown domain = Content Theft
    status = "IMPERSONATION_DETECTED"
    PAS_Penalty *= 1.5  # Amplified coordination penalty
else:
    # PAS_Penalty = the Coordination component of PAS (Section 12):
    # PAS_Penalty = 0.30 × (Coordination × [1 - mean_SCS])
    PAS_Penalty *= (1 - whitelist_weight)  # Graduated reduction
```
**Dependencies:** Cosine similarity on first paragraphs, `SYNDICATION_WHITELIST` domain registry.
**Feeds Into:** PAS Coordination Component ($0.30 \times \text{Coordination} \times [1 - \text{mean\_SCS}]$).

---

### 14. Threat Matrix (v1.3)
**Purpose:** Visualizes article threat levels in 4 dimensions.
**Mapping:**
| UI Dimension | Data Variable | Description |
| :--- | :--- | :--- |
| **X-Axis** | $SCS$ | Left (Low Trust) to Right (High Trust). |
| **Color** | $D_{calibrated}$ | Green (Clean) to Red (Distorted). |
| **Opacity** | $Confidence$ | Transparent (Uncertain) to Solid (Certain). |
| **Radius** | $PAS$ | Small (Normal) to Large (Abnormal Spread). |

---

### 15. Drift Monitoring (v1.8)
**Purpose:** Detects when live misinformation patterns deviate from training data.
**Monitored Variable (v2.1):** $P$ = histogram of **calibrated $D_{calibrated}$ scores** (20 equal-width bins on $[0, 1]$) computed over a rolling 7-day window. $P_{train}$ is the same histogram from the LIAR/FakeNewsNet training set. Drift in the distortion score distribution indicates the calibration model is stale.
**Metric (Empirical Variable v2.0):** 
$$KL(P_{live} \| P_{train}) > T_{drift}$$
$$T_{drift} = \mu(\text{Baseline\_KL}) + 2\sigma(\text{Baseline\_KL})$$
**Justification:** Replaces the fixed $0.2$ threshold with a statistically defensible outlier detection method derived from the system's own baseline KL-divergence distribution.

**Logic Gates:**
```python
# v2.1: Laplace smoothing to prevent KL divergence explosion on zero bins
epsilon = 1e-8
P_live_smooth = (P_live + epsilon) / (1 + epsilon * len(P_live))
P_train_smooth = (P_train + epsilon) / (1 + epsilon * len(P_train))

KL_drift = sum(P_live_smooth * log(P_live_smooth / P_train_smooth))

T_drift = mean(baseline_KL) + 2 * std(baseline_KL)
# Fallback: if baseline is heavily skewed, use 95th percentile instead
T_drift = min(T_drift, percentile(baseline_KL, 95))

if KL_drift > T_drift:
    trigger_alert("CALIBRATION_DRIFT_DETECTED")
    # Mark scores as "Requires Recalibration"
```
**Dependencies:** Cosmos DB live data distribution history, Baseline KL distribution.
**Feeds Into:** Application Insights / Maintenance Logs.
