import argparse
import json
from pathlib import Path


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
    for result in results:
        bucket = by_feature.setdefault(result["feature"], {"PASS": 0, "FAIL": 0})
        bucket[result["status"]] += 1
    total = len(results)
    passed = sum(1 for result in results if result["status"] == "PASS")
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(passed / total, 3) if total else 0,
        "by_feature": by_feature,
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
    args = parser.parse_args()

    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    results = [check_case(case) for case in cases]
    summary = summarize(results)
    report = {"summary": summary, "results": results}
    Path(f"{args.out}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(f"{args.out}.md", results, summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
