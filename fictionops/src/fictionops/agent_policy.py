from __future__ import annotations

from dataclasses import asdict, dataclass


POLICY_SCHEMA = "fictionops.agent_controller_policy.v1"
HUMAN_STATES = {"ready_for_approval", "awaiting_approval", "verified"}
FAILED_STATES = {"needs_revision_attention", "failed_recoverable", "blocked_stale_source"}


@dataclass(frozen=True)
class AgentPolicyDecision:
    schema: str
    action: str
    reason: str
    risk: str
    authority: str
    executable: bool

    def payload(self) -> dict[str, object]:
        return asdict(self)


def select_agent_policy(
    *,
    state: str | None,
    ready_for_approval: bool = False,
    budget_status: str | None = None,
    memory_stale: bool = False,
    canon_sync_pending: bool = False,
) -> AgentPolicyDecision:
    normalized = (state or "unknown").strip()
    if ready_for_approval or normalized in HUMAN_STATES:
        return AgentPolicyDecision(POLICY_SCHEMA, "review_candidate", "Automated gates passed; author authority is required.", "R3", "author", False)
    if budget_status == "exhausted":
        return AgentPolicyDecision(POLICY_SCHEMA, "replan_budget", "The hard model budget was exhausted; scope or budget changes require an explicit decision.", "R1", "author", False)
    if normalized in FAILED_STATES:
        return AgentPolicyDecision(POLICY_SCHEMA, "inspect_failed_candidate", "Blocking evidence remains; the candidate cannot continue as if it passed.", "R2", "author", False)
    if normalized == "cancelled":
        return AgentPolicyDecision(POLICY_SCHEMA, "start_new_session_after_cancellation", "The session was explicitly cancelled and cannot resume implicitly.", "R1", "author", False)
    if normalized == "applied" and canon_sync_pending:
        return AgentPolicyDecision(POLICY_SCHEMA, "review_canon_sync", "Manuscript text was applied, but canon synchronization remains an author decision.", "R4", "author", False)
    if memory_stale:
        return AgentPolicyDecision(POLICY_SCHEMA, "rebuild_memory", "Accepted evidence marked the derived memory index stale.", "R0", "controller", True)
    return AgentPolicyDecision(POLICY_SCHEMA, "inspect_project", "No safe automatic transition is currently justified.", "R0", "controller", False)
