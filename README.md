# LLM Eval Regression Harness

LLM Eval Regression Harness is a local evaluation tool for testing model outputs against schema, safety, content coverage, and regression expectations.

It combines deterministic checks with a local AI evaluation analyst so teams can track output quality and explain why a model response passes, fails, or needs review.

## What It Does

- Loads evaluation cases from local samples.
- Runs deterministic checks for JSON shape, required fields, banned terms, and content coverage.
- Computes pass/fail counts and regression categories.
- Produces JSON and dashboard-ready output.
- Adds local AI analysis for release-readiness interpretation.

## AI Features

- Local AI copilot summarizes quality risks and failure patterns.
- AI analyst explains what failed and what should be fixed first.
- Recommendations are grounded in deterministic evaluation results.
- Browser UI exposes test results and AI interpretation.

## Architecture

```text
Evaluation cases
      |
      v
Deterministic checks -> pass/fail metrics -> regression summary
      |
      v
Local AI analyst -> quality summary + fix priority
      |
      v
JSON report / browser dashboard
```

## Run

```powershell
run.bat
```

## Local AI Setup

Use LM Studio or another local OpenAI-compatible server. The default target model is `google/gemma-4-e4b`.

The deterministic evaluation harness works without AI.

## Main Files

- `app.py` - evaluation logic and AI summary generation.
- `server.py` - local dashboard server.
- `eval-ui-data.json` - UI data.
- `agents/Agent.md` - evaluation AI instructions.

## Output

The project outputs pass/fail metrics, violation categories, regression results, and AI-generated release-readiness guidance.
