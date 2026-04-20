# LLM Eval Regression Harness

Role fit: AI testing, AI agent engineering, LLM evaluation, SDET, QA automation, and AI platform roles.

This project evaluates prompt/response outputs against deterministic checks. It is useful for showing that AI projects need test coverage too: expected keywords, banned terms, JSON validity, citation requirements, and routing labels.

## Features

- Loads test cases from JSON.
- Checks generated outputs for required terms, banned terms, JSON validity, and expected route labels.
- Produces pass/fail summaries by feature area.
- Writes JSON and Markdown reports for review.

## Run

```bash
python app.py --cases samples/cases.json --out report
```

## Resume Bullets

- Built a Python LLM evaluation harness that validates AI-agent outputs for required content, banned terms, JSON shape, and routing labels.
- Created regression-style test cases for support, safety, summarization, and tool-routing workflows.
- Generated structured reports that show pass rate, failing checks, and feature-level quality trends for AI applications.
