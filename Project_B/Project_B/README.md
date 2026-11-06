# Project B — Data Quality Detection (Python 3.10+)

## Run
From this directory, with Python 3.10+:
```bash
python run_project.py
```
One command profiles the supplied export, creates reproducible corrupt batches for all 12 assignment problem types, runs rule/statistical/LLM-proxy detector families, evaluates detection and clean false alarms, and regenerates all result files.

## Data note
The supplied `export(1).csv` contains 99,200 rows with Created Date values in Oct–Nov 2026. The assignment calls for NYC 311 requests created in calendar year 2023. The pipeline explicitly reports that mismatch and profiles the uploaded data as supplied; it does not fabricate 2023 records. Replace `data/export.csv` with the 2023 dataset to run the assignment target year.

## Honest LLM measurement
`llm_review` is a deterministic, locally executable LLM-review proxy, not a Gemini API call. Cost is therefore reported as $0 local execution and the report marks Gemini measurements as not measured. Replace the proxy with Gemini for real token cost/latency measurement; don't present proxy results as Gemini results.
