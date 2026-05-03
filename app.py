import argparse
import json
import sys
from collections import Counter
from pathlib import Path

SHARED = Path(__file__).resolve().parents[1] / "_shared_project_workbench"
if str(SHARED) not in sys.path:
    sys.path.insert(0, str(SHARED))

try:
    from local_llm import chat_json
except Exception:
    chat_json = None


def check_case(case):
    output = case["output"]
    failures = []

    for term in case.get("required_terms", []):
        if term.lower() not in output.lower():
            failures.append(f"missing required term: {term}")

    for term in case.get("banned_terms", []):
        if term.lower() in output.lower():
            failures.append(f"contains banned term: {term}")

    if case.get("must_be_json"):
        try:
            parsed = json.loads(output)
        except json.JSONDecodeError:
            failures.append("output is not valid JSON")
            parsed = {}
        expected_route = case.get("expected_route")
        if expected_route and parsed.get("route") != expected_route:
            failures.append(f"route mismatch: expected {expected_route}, got {parsed.get('route')}")

    return {
        "id": case["id"],
        "feature": case["feature"],
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
    }


def summarize(results):
    by_feature = {}
    failure_reasons = Counter()
    failed_cases = []

    for result in results:
        bucket = by_feature.setdefault(result["feature"], {"PASS": 0, "FAIL": 0})
        bucket[result["status"]] += 1

        if result["status"] == "FAIL":
            failed_cases.append(result)
            for failure in result.get("failures", []):
                reason = failure.split(":")[0].strip()
                failure_reasons[reason] += 1

    total = len(results)
    passed = sum(1 for result in results if result["status"] == "PASS")
    failed = total - passed

    ranked_features = sorted(
        by_feature.items(),
        key=lambda item: (item[1].get("FAIL", 0), item[1].get("PASS", 0)),
        reverse=True,
    )

    release_decision = "hold" if failed else "ready"

    json_cases = sum(1 for result in results if "json" in result["feature"] or "routing" in result["feature"])
    critical_failures = [
        result for result in failed_cases
        if result["feature"] in {"safety", "policy_refusal", "json_schema", "tool_routing"}
    ]

    feature_pass_rates = {}
    for feature, counts in by_feature.items():
        feature_total = counts["PASS"] + counts["FAIL"]
        feature_pass_rates[feature] = round(counts["PASS"] / feature_total, 3) if feature_total else 0

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / total, 3) if total else 0,
        "json_case_count": json_cases,
        "critical_failures": len(critical_failures),
        "by_feature": by_feature,
        "feature_pass_rates": feature_pass_rates,
        "failure_reasons": dict(failure_reasons.most_common()),
        "failed_cases": failed_cases[:20],
        "ranked_features": ranked_features,
        "release_decision": release_decision,
        "operator_priority": [
            "Fix failing feature groups first",
            "Review repeated failure reasons",
            "Rerun regression before release signoff"
        ],
    }


def generate_ai_eval_brief(summary, model="google/gemma-4-e4b"):
    prompt = f"""You are a local AI evaluation copilot.

You are reviewing deterministic LLM regression results.

Return ONLY valid JSON with:
- result
- answer
- evidence
- next_action
- recommendation
- decision
- risks (array of 3)
- operator_actions (array of 3)

Rules:
- use only the deterministic summary
- do not invent metrics
- mention pass rate, failed cases, feature groups, and failure reasons when relevant
- keep it concise and engineering-focused

Summary:
{json.dumps(summary, indent=2)}
"""

    try:
        if chat_json is None:
            raise RuntimeError("local_llm unavailable")
        ai = chat_json(prompt, model=model)
        if not isinstance(ai, dict):
            ai = {}
    except Exception as e:
        ai = {
            "result": "Fallback LLM evaluation brief generated.",
            "answer": f"Local AI failed: {e}",
            "evidence": "Fallback used deterministic evaluation summary.",
            "next_action": "Review failed cases and repeated failure reasons.",
            "recommendation": "Fix feature groups with the most failures first.",
            "decision": "Hold release if any regression case fails.",
            "risks": [],
            "operator_actions": [],
        }

    return {
        "result": ai.get("result", "LLM regression evaluation complete."),
        "answer": ai.get("answer", "Evaluation summary generated."),
        "evidence": ai.get("evidence", f"Pass rate={summary.get('pass_rate')} failed={summary.get('failed')}"),
        "next_action": ai.get("next_action", "Review failed regression cases."),
        "recommendation": ai.get("recommendation", "Prioritize failing feature groups."),
        "decision": ai.get("decision", "Hold release if failures remain."),
        "risks": ai.get("risks", []),
        "operator_actions": ai.get("operator_actions", []),
    }


def write_markdown(path, results, summary):
    lines = [
        "# LLM Eval Regression Report",
        "",
        f"Pass rate: {summary['pass_rate']:.1%}",
        "",
        "## Feature Summary",
        "",
    ]
    for feature, counts in summary["by_feature"].items():
        lines.append(f"- {feature}: {counts['PASS']} pass, {counts['FAIL']} fail")
    lines += ["", "## Failing Cases", ""]
    failing = [result for result in results if result["status"] == "FAIL"]
    if not failing:
        lines.append("- None")
    for result in failing:
        lines.append(f"- {result['id']} ({result['feature']}): " + "; ".join(result["failures"]))
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", required=True)
    parser.add_argument("--out", default="report")
    parser.add_argument("--use-ai", action="store_true")
    parser.add_argument("--model", default="google/gemma-4-e4b")
    args = parser.parse_args()

    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    results = [check_case(case) for case in cases]
    summary = summarize(results)

    if args.use_ai:
        summary["ai_copilot"] = generate_ai_eval_brief(summary, model=args.model)

    report = {
        "summary": summary,
        "results": results,
        "cases": cases,
    }

    Path(f"{args.out}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    Path("eval-ui-data.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(f"{args.out}.md", results, summary)

    print(f"[EVAL DONE] total={summary['total']} passed={summary['passed']} failed={summary['failed']} pass_rate={summary['pass_rate']}")


if __name__ == "__main__":
    main()
