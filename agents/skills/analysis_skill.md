# LLM Eval Analysis Skill

## When Used

Use this skill when the user asks about eval quality, failing features, JSON errors, safety checks, regression risk, or release readiness.

## Input

- eval summary
- feature pass/fail counts
- failure reasons
- failed case list
- release decision

## Output

Return:

- answer
- evidence
- next_action
- recommendation
- decision

## Rules

- Mention exact deterministic metrics.
- Prioritize feature groups with the most failures.
- Treat JSON/schema failures as release blockers.
- Clearly state whether the eval run should ship or hold.