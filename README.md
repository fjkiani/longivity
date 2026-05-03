## longivity (RUO)

Standalone packaging of CrisPRO's longevity assessment module:

- **Level 0**: PhenoAge Gompertz (Levine 2018; PMID `29676998`) + hallmark narrative + optional compound ranking
- **Full assessment**: Level 0 + optional genetics annotation + optional DNA repair scoring + optional parental-lifespan PRS

This package is **Research Use Only (RUO)**.

### Run locally

```bash
cd packages/longivity
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -e .
uvicorn longivity.app:app --reload --host 127.0.0.1 --port 8088
```

### Endpoints

- `POST /api/v1/longevity/assessment_level0`
- `POST /api/v1/longevity/full_assessment`

