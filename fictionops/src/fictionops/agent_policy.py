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
    counterevidence_open_count: int = 0,
    counterevidence_blocked_count: int = 0,
    counterevidence_withdrawn_count: int = 0,
    counterevidence_candidate_state: str | None = None,
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
    if counterevidence_open_count > 0:
        if counterevidence_candidate_state == "ready_for_approval":
            return AgentPolicyDecision(POLICY_SCHEMA, "review_counterevidence_candidate", "The bounded candidate passed independent verification; explicit author acceptance is required.", "R3", "author", False)
        if counterevidence_candidate_state == "needs_revision_attention":
            return AgentPolicyDecision(POLICY_SCHEMA, "revise_counterevidence_candidate", "The bounded candidate failed verification and must not be accepted.", "R2", "controller", False)
        if counterevidence_candidate_state == "repairable_regression":
            return AgentPolicyDecision(POLICY_SCHEMA, "repair_counterevidence_candidate", "The contracted fix is present, but a local prose regression requires bounded candidate repair.", "R2", "controller", False)
        if counterevidence_candidate_state == "awaiting_verification":
            return AgentPolicyDecision(POLICY_SCHEMA, "verify_counterevidence_revision", "A staged bounded candidate exists and requires independent contract verification.", "R2", "controller", False)
        return AgentPolicyDecision(
            POLICY_SCHEMA,
            "prepare_counterevidence_revision",
            f"{counterevidence_open_count} grounded counterevidence issue(s) are open and may enter a staged reviser.",
            "R2",
            "controller",
            False,
        )
    if counterevidence_blocked_count > 0:
        return AgentPolicyDecision(
            POLICY_SCHEMA,
            "retrieve_counterevidence",
            f"{counterevidence_blocked_count} issue(s) remain evidence-blocked; retrieve matching-scope sources before another verdict.",
            "R1",
            "controller",
            False,
        )
    if counterevidence_withdrawn_count > 0:
        return AgentPolicyDecision(
            POLICY_SCHEMA,
            "review_model_withdrawals",
            f"{counterevidence_withdrawn_count} model-withdrawn issue(s) await optional author confirmation; no automatic revision is justified.",
            "R3",
            "author",
            False,
        )
    return AgentPolicyDecision(POLICY_SCHEMA, "inspect_project", "No safe automatic transition is currently justified.", "R0", "controller", False)
