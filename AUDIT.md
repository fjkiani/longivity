# Longivity (Longevity) module — A→Z audit (RUO)

This package is a **standalone extraction** of the CrisPRO longevity assessment logic and its JSON resources, intended for **Research Use Only (RUO)**.

> Naming note: the package is spelled `longivity` (historic typo); it implements **longevity** assessment functions and resources.

---

## A) API surface

- **FastAPI app**: `src/longivity/app.py`
- **Routes**: `src/longivity/api.py`
  - `GET /healthz`: basic health check
  - `POST /api/v1/longevity/assessment_level0`: “bloodwork only” PhenoAge-level assessment
  - `POST /api/v1/longevity/full_assessment`: full report orchestrating level0 + hallmarks + optional genetics/PRS + compound recs

## B) Core orchestrator

- **File**: `src/longivity/services/longevity_report_builder.py`
- **Entry**: `run_longevity_full_assessment(payload: dict) -> dict`
- **Responsibilities**:
  - normalize/merge compound queries
  - run Level0 (PhenoAge-ish) assessment
  - score hallmarks from biomarkers
  - optional genetics annotation + DNA repair scoring + PRS scoring
  - return one consolidated JSON report (stable field names)

## C) Level0 (PhenoAge-ish) scoring

- **File**: `src/longivity/services/longevity_phenoage_level0.py`
- **Resource dependency**:
  - `resources/longevity/phenoage_gompertz_coefficients_levine2018.json`
- **Notes**:
  - Assumes common lab fields (e.g., CRP, albumin, creatinine, glucose/HbA1c variants) with conservative missing-data handling.
  - Output is an RUO risk proxy (not clinical risk).

## D) Hallmark scoring from biomarkers

- **File**: `src/longivity/services/longevity_hallmark_scorer.py`
- **Resource dependency**:
  - `resources/longevity/biomarker_hallmark_map.json`
- **Notes**:
  - Biomarkers map to hallmarks with evidence metadata and “optimal ranges”.
  - Current design is deterministic and auditable (rule + weights), not ML.

## E) Genetics annotation (lightweight)

- **File**: `src/longivity/services/genetic_annotator.py`
- **Notes**:
  - Interprets user-provided genotype-ish keys (not a VCF parser).
  - Designed for “known loci” inputs (e.g., APOE, MTHFR) and returns caveats heavily.

## F) DNA repair scoring

- **File**: `src/longivity/services/dna_repair_scorer.py`
- **Resource dependency**:
  - `resources/longevity/dna_repair_gene_panel.json`
- **Notes**:
  - Uses pathway panels + example polymorphisms with enzyme activity heuristics.
  - Not a comprehensive clinical-grade DDR inference system; explicitly RUO.

## G) PRS (parental lifespan proxy)

- **File**: `src/longivity/services/longevity_prs.py`
- **Resource dependency**:
  - `resources/longevity/longevity_prs_variants.json`
- **Notes**:
  - Implements a simple allele-count × beta aggregation.
  - Produces an “honest caveat” block; output is not a medical PRS.

## H) Compound ↔ hallmark mapping

- **Resource dependency**:
  - `resources/longevity/longevity_compound_hallmark_map.json`
- **Used by**:
  - `longevity_hallmark_scorer.py` / `longevity_phenoage_level0.py` (recommendation synthesis)
- **Notes**:
  - Evidence strength fields are treated as guidance metadata, not proof.

## I) Data/resources integrity

Vendored JSON resources live in:

- `src/longivity/resources/longevity/`

This is intentionally self-contained (no runtime dependence on the original monorepo paths).

## J) Determinism & reproducibility

- The core scoring paths are deterministic given the same payload + resource JSONs.
- No network calls are required for the core report in this extracted package.

## K) Error handling behavior

- Primary design is **graceful degradation**:
  - missing biomarkers/genetics/PRS fields reduce completeness and add caveats rather than raising hard exceptions.
  - unexpected keys are ignored (best-effort).

## L) Security / PHI posture

- This package contains no persistence layer by default.
- Treat all payloads as sensitive; do not log raw biomarker/genetics payloads in production deployments.

## M) Packaging layout & deps

- `pyproject.toml` with `src/` layout.
- Minimal runtime deps:
  - `fastapi`, `uvicorn[standard]`, `pydantic`

## N) Python compatibility

- Declared: `requires-python = ">=3.9"`
- Smoke-tested in a Python 3.9.x environment via editable install.

## O) What’s explicitly out of scope (current extraction)

- No VCF parsing, liftover, reference genome validation.
- No clinical guideline engine (this is longevity-style scoring only).
- No database, no auth, no user sessions.

## P) Known “sharp edges”

- Input schemas are permissive by design; strict validation is minimal.
- Biomarker naming variability is handled heuristically; adding an explicit alias layer would improve robustness.
- The `longivity` naming typo is preserved for API stability; rename would be a breaking change.

## Q) Suggested next hardening steps (non-breaking)

- Add Pydantic request models for the two POST endpoints (keep response shape stable).
- Add `pytest` tests (golden JSON snapshots) for 3 canonical payloads.
- Add structured logging hooks with redaction.
- Add a strict-mode flag that raises on unknown biomarkers instead of ignoring.

## R) Quick local run

From repo root:

```bash
python3 -m pip install -e packages/longivity
python3 -m longivity.app
```

Then:

```bash
curl -sS http://127.0.0.1:8000/healthz
```

## S) Quick import smoke (no server)

```python
from longivity.services import run_longevity_full_assessment
print(run_longevity_full_assessment({"age": 45, "biomarkers": {"hba1c": 5.8}})["status"])
```

## T) License

Current `pyproject.toml` declares `license = { text = "Proprietary" }`.

---

## Z) “Zero-surprises” guarantee

- This extracted package only vendors what it needs: **services + JSON resources + minimal API wrapper**.
- No coupling to the rest of the monorepo is required at runtime.

