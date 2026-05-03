from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import json

DATA_FILE = Path("eval-ui-data.json")
WEB_ROOT = Path("web")


def load_data():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {
        "summary": {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "pass_rate": 0,
            "by_feature": {},
            "failure_reasons": {},
            "failed_cases": [],
            "release_decision": "unknown",
            "operator_priority": [],
            "ai_copilot": {}
        },
        "results": [],
        "cases": []
    }


def answer_question(question, data):
    q = question.lower()
    summary = data.get("summary", {})
    ai = summary.get("ai_copilot", {})

    if "risk" in q or "fail" in q:
        answer = f"Failed cases: {summary.get('failed', 0)} across features {summary.get('by_feature', {})}."
        evidence = f"Failure reasons: {summary.get('failure_reasons', {})}."
        next_action = "Start with the feature group with the most failures."
        recommendation = "Fix repeated failure reasons before adding new eval cases."
        decision = "Hold release if any critical feature has failing cases."
    elif "feature" in q or "area" in q:
        answer = f"Feature breakdown: {summary.get('by_feature', {})}."
        evidence = "Counts are grouped from deterministic regression results."
        next_action = "Review feature groups with FAIL counts first."
        recommendation = "Add owner labels for each feature group if this becomes a team tool."
        decision = "Use feature-level pass rate as the release gate."
    elif "json" in q or "schema" in q:
        answer = "JSON/schema failures are detected through deterministic JSON parsing and route checks."
        evidence = f"Failure reasons include: {summary.get('failure_reasons', {})}."
        next_action = "Fix invalid JSON and route mismatch cases first."
        recommendation = "Keep JSON checks deterministic and add AI only for explanation."
        decision = "Do not ship agents with invalid JSON outputs."
    elif "release" in q or "ship" in q or "ready" in q:
        answer = f"Release decision is {summary.get('release_decision', 'unknown')} with pass rate {round(summary.get('pass_rate', 0) * 100, 1)}%."
        evidence = f"Passed={summary.get('passed', 0)}, failed={summary.get('failed', 0)}, total={summary.get('total', 0)}."
        next_action = "Rerun after fixing failing eval cases."
        recommendation = ai.get("recommendation", "Use failed cases as regression blockers.")
        decision = ai.get("decision", "Hold release if failures remain.")
    else:
        answer = f"Evaluation processed {summary.get('total', 0)} cases with {summary.get('passed', 0)} pass and {summary.get('failed', 0)} fail."
        evidence = f"Pass rate is {round(summary.get('pass_rate', 0) * 100, 1)}%."
        next_action = "Review failing cases and repeated failure reasons."
        recommendation = ai.get("recommendation", "Prioritize the worst feature groups.")
        decision = ai.get("decision", "Proceed only after regression failures are resolved.")

    return {
        "answer": answer,
        "evidence": evidence,
        "next_action": next_action,
        "recommendation": recommendation,
        "decision": decision
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode())
            return

        if self.path == "/data":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(load_data()).encode())
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path == "/ask":
            length = int(self.headers.get("Content-Length", 0))
            question = self.rfile.read(length).decode()
            response = answer_question(question, load_data())

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            return

        self.send_response(404)
        self.end_headers()


if __name__ == "__main__":
    print("[OK] LLM Eval Dashboard running at http://localhost:8007/")
    HTTPServer(("localhost", 8007), Handler).serve_forever()