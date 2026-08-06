# Project Decisions and Architecture Decision Records (ADRs)

This document records research, mathematical, and software architecture decisions for the OVON project.

---

## Architecture Decision Records (ADRs)

### ADR-001: Use encounter rate as the retrospective MVP target
**Status:** Accepted  
**Decision:** Model the probability of detecting a species on a standardized complete checklist ($y \sim \operatorname{Bernoulli}(\pi)$).  
**Rationale:** Standardized complete checklist encounter rates are computationally manageable and align with Cornell eBird best practices.

### ADR-002: Use a Kansas City regional pilot
**Status:** Accepted  
**Decision:** Centered on Greater Kansas City (`39.0997, -94.5786`) with a 30–50 km radius crossing Missouri and Kansas.

### ADR-003: Freeze historical outcomes at 2025-12-31
**Status:** Accepted  
**Decision:** Primary benchmark uses complete years 2021–2025.

### ADR-004: Use complete stationary and traveling checklists
**Status:** Accepted  
**Decision:** Infer non-detections only from complete checklists.

### ADR-005: Separate scientific utility from volunteer utility
**Status:** Accepted  
**Decision:** Report scientific information gain, route travel burden, and observer experience level separately.

### ADR-006: Bootstrap disagreement plus spatial-habitat redundancy
**Status:** Accepted  
**Decision:** Compute set utility $U(A)$ combining QBC disagreement $U_{\text{QBC}}$ and spatial-habitat redundancy kernels $k(a, b)$ instead of full Bayesian posterior sampling.

### ADR-007: Standardized 10-minute stationary checklists per stop
**Status:** Accepted  
**Decision:** Recommended field protocol consists of 3–5 fixed candidate stops, each with a 10-minute stationary complete checklist.

### ADR-008: No public individual observer ranking
**Status:** Accepted  
**Decision:** Observer skill levels are used for protocol guidance only and are never publicly ranked or gamified.

### ADR-010: Access, safety, and sensitive-species rules are hard constraints
**Status:** Accepted  
**Decision:** Legal public access and safety are hard constraints. Exclude sensitive locations from public outputs.

### ADR-016: Guild-based priority weighting for seasonal migratory birds
**Status:** Accepted  
**Date:** 2026-08-05  
**Decision:** Assign 2.5× higher optimization weight ($w_s$) to seasonal migratory species (*Indigo Bunting*, *Yellow-rumped Warbler*, *Belted Kingfisher*, *Bald Eagle*) compared to year-round residents (*Cardinal*, *Blue Jay*, *Robin*).  
**Rationale:** Capturing spring and autumn migration temporal dynamics generates higher scientific marginal value.

### ADR-017: Candidate POI expansion to public fountains, plazas, and riverfronts
**Status:** Accepted  
**Date:** 2026-08-05  
**Decision:** Expand candidate observation sites beyond standard public parks to include famous Kansas City fountains (J.C. Nichols Memorial Fountain, Firefighters Fountain, Loose Park Rose Garden Fountain), public plazas (Union Station Plaza, Mill Creek Park), and riverfront corridors (Berkley Riverfront Park, English Landing Park).  
**Rationale:** Increases spatial coverage across urban and riparian habitats.

### ADR-018: OSRM real road routing & turn-by-turn directions
**Status:** Accepted  
**Date:** 2026-08-05  
**Decision:** Use the Open Source Routing Machine (OSRM) API to compute driving travel times, render road-snapped driving polylines on Leaflet maps (snapping to highways I-70, I-435, US-71), and generate turn-by-turn volunteer directions.  
**Rationale:** Replaces straight-line approximations with realistic driving paths and actionable volunteer instructions.

### ADR-019: Form-based widget grouping for Streamlit UI performance
**Status:** Accepted  
**Date:** 2026-08-05  
**Decision:** Group optimization controls inside `st.form` with a single submission button and cache route solutions (`@st.cache_data`).  
**Rationale:** Eliminates map iframe re-rendering and flickering when adjusting sliders or dropdowns.

---

## Open Questions & Statuses

- **Q1. Ecological Target:** Migration-week encounter maps for a mixed portfolio (Implemented).
- **Q2. Spatial Representation:** 3 km equal-area square grid centered on Kansas City (Implemented).
- **Q3. Rarity vs. Uncertainty:** Epistemic uncertainty prioritized via QBC; raw vagrant rarity excluded from MVP to prevent chase behavior (Implemented).
