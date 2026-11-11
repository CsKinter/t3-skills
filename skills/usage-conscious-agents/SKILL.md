---
name: usage-conscious-agents
description: Keep token usage low when orchestrating coding subagents, especially paid OpenCode workers. Use for delegation planning, context control, and reducing agent cost while preserving task quality.
---

# Usage-conscious agents

Optimize total work and verified outcomes, not just price per token. Preserve the user's chosen providers, models, effort settings, and authorization boundaries. This skill does not itself authorize delegation or configuration changes.

For the measured motivation and limits of the November 2026 usage diagnosis, read [the trace findings](references/trace-findings.md) only when discussing that diagnosis. They are historical observations, not current provider guarantees.

## Before delegation

- Handle small, clear edits directly. Delegate only a bounded task with a concrete deliverable that benefits from independent work or specialized context.
- Avoid overlapping exploration and redundant reviews. Default to one worker for one coherent task; add parallel workers only for independent tasks with distinct ownership. Do not let workers spawn further workers unless explicitly authorized.
- Give each worker a compact brief: objective, exact paths or search area, relevant facts, constraints, acceptance checks, and expected report. Prefer file references and selected excerpts to transcripts or whole files.
- Prefer a fresh isolated context for a new task. Check the delegation mechanism's actual inheritance behavior; never assume children do or do not inherit parent history. Where supported and compatible with the task, disable full-history inheritance. Otherwise account for inherited context before choosing delegation.

## Model and effort

- Respect explicitly requested settings. When settings are unspecified, use a suitable inexpensive worker and moderate effort for bounded execution if the runtime supports it. Do not invent model IDs, option names, prices, or unsupported effort levels.
- Reserve deeper reasoning for ambiguous requirements, architecture, difficult debugging, and consequential correctness questions. Increase effort when evidence shows reasoning is the bottleneck; do not promise identical quality at lower effort.
- Discover supported provider options only when necessary. For T3 delegation, follow its capability-discovery and target.options requirements. Do not substitute providers or models silently when unavailable.
- Do not hard-code model rankings or subscription buckets from past usage. Compare observed task cost, latency, and quality when actual telemetry is available.

## Bound context growth

- Search narrowly first (paths, filenames, then bounded matches). Read relevant ranges. Limit tool output; save large logs to files and report the failure excerpt and artifact path.
- Avoid dumping repositories, full JSON traces, generated files, or repeated successful test output into context. Read only additional material needed for the next decision.
- After roughly 10 tool rounds on a small delegated task, reassess scope and progress. This is a checkpoint, not a forced stop or an invitation to spawn another worker. Continue when the remaining work is clear; otherwise return findings and the precise blocker.
- Treat roughly 80K-120K visible context tokens as a soft handoff checkpoint when telemetry exists, not a provider limit. Before further large reads or a distinct task, compact with the runtime's supported mechanism or write a concise handoff and use a fresh context. Do not repeatedly restart workers that lack necessary context.
- Reuse a worker only when the next step depends strongly on its recent work and retained context remains useful and reasonably small. Prefer fresh workers for distinct tasks and large, stale histories. For T3, every new delegated review or re-check must be a new delegate_task; fix small findings in the parent.
- Never assume a universal five-minute cache TTL. A cache miss may have several causes. Do not send keepalive calls, compact solely because five minutes passed, or claim inactivity proves cache eviction. Large histories are costly even when cached.

## Finish and verify

- Ask workers for a concise report: result, changed files, checks and outcomes, unresolved risks. Include decision-relevant evidence, not their transcript.
- Run checks proportionate to the change. Avoid repeated review cycles or duplicate tests after relevant checks pass unless a new change or unresolved concern warrants them.
- Stop unnecessary workers with the runtime's cancellation mechanism. Follow runtime wait/notification instructions; do not poll.
- If usage telemetry exists, distinguish uncached input, cached input, output/reasoning, and subscription accounting. Report measured savings only; do not estimate a guaranteed percentage from effort labels or request count alone.

## Example worker brief

> Implement [specific behavior] in [paths]. Relevant facts: [short summary]. Constraints: [requirements and ownership]. Inspect only material needed for this task and keep tool output bounded. Run [targeted check]. Return changed files, check results, and unresolved issues concisely. Do not delegate further.
