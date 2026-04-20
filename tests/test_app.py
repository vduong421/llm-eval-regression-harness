from app import check_case, summarize


def test_check_case_validates_json_route_and_terms():
    result = check_case({
        "id": "route-1",
        "feature": "routing",
        "output": '{"route":"billing","summary":"invoice refund"}',
        "must_be_json": True,
        "expected_route": "billing",
        "required_terms": ["invoice", "refund"],
        "banned_terms": ["guaranteed"],
    })

    assert result["status"] == "PASS"
    assert result["failures"] == []


def test_check_case_reports_failures():
    result = check_case({
        "id": "bad-1",
        "feature": "routing",
        "output": '{"route":"support","summary":"guaranteed fix"}',
        "must_be_json": True,
        "expected_route": "billing",
        "required_terms": ["invoice"],
        "banned_terms": ["guaranteed"],
    })

    assert result["status"] == "FAIL"
    assert "missing required term: invoice" in result["failures"]
    assert "contains banned term: guaranteed" in result["failures"]
    assert "route mismatch: expected billing, got support" in result["failures"]


def test_summarize_groups_by_feature():
    summary = summarize([
        {"feature": "routing", "status": "PASS"},
        {"feature": "routing", "status": "FAIL"},
        {"feature": "safety", "status": "PASS"},
    ])

    assert summary["total"] == 3
    assert summary["pass_rate"] == 0.667
    assert summary["by_feature"]["routing"] == {"PASS": 1, "FAIL": 1}
