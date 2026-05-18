# MiFO (Misinformation Forensics)

## Core Value
An advanced, multidimensional analysis framework to combat the "Evolution Problem" in digital misinformation by shifting the paradigm from static verification to Semantic Evolution Tracking and Coordinated Propagation Modeling. Target: Microsoft Imagine Cup 2027.

## Architecture
- **Client:** Browser Extension (React / Manifest V3 / D3.js)
- **Backend:** FastAPI on Azure App Service F1
- **Data Layer:** Cosmos DB, AI Search, Blob Storage
- **AI Engine:** Azure OpenAI (gpt-4o-mini), Azure AI Language

## Key Dimensions
- **S:** Semantic Drift
- **E:** Emotional Amplification
- **C:** Factual Contradiction
- **D:** Distortion Score (calibrated)
- **PAS:** Propagation Anomaly Score
- **Confidence:** Uncertainty Clip

## Key Decisions
| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Cosmos DB instead of Redis | Cache for Redis exceeded student budget | Using Cosmos native TTL for URLCache |
| Azure OpenAI gpt-4o-mini | High reasoning required for NLI scoring | Cost-effective and powerful |
| Never 500 Rule | Fail-safe degradation if sub-services fail | Returns partial result with degradation flag |

---
*Last updated: 2026-05-19 after initialization*
