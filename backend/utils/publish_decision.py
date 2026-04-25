from __future__ import annotations

AUTO_PUBLISH_BLOCKING_RISK_LEVELS = {"high"}
POST_PUBLISHED_STATUSES = {"approved", "publishing", "published", "archived"}


def qa_allows_auto_publish(qa_result: dict | None) -> bool:
    qa_result = qa_result or {}
    return (
        bool(qa_result.get("integrity_ok", True))
        and bool(qa_result.get("passed"))
        and qa_result.get("risk_level", "unknown") not in AUTO_PUBLISH_BLOCKING_RISK_LEVELS
    )


def build_publish_decision(
    *,
    qa_result: dict | None = None,
    review_info: dict | None = None,
    task_status: str | None = None,
    post_status: str | None = None,
    has_task: bool = True,
) -> dict[str, object]:
    qa_result = qa_result or {}
    review_info = review_info or {}

    qa_passed = bool(qa_result.get("passed"))
    risk_level = qa_result.get("risk_level", "unknown")
    integrity_ok = bool(qa_result.get("integrity_ok", True))
    qa_auto_passed = qa_allows_auto_publish(qa_result)

    human_approval_recorded = bool(review_info.get("human_approved"))
    legacy_human_approval = (
        has_task
        and not human_approval_recorded
        and task_status in {"ready_to_publish", "publishing", "published"}
        and post_status in POST_PUBLISHED_STATUSES
        and not qa_auto_passed
        and risk_level == "high"
    )
    human_approved = human_approval_recorded or legacy_human_approval

    final_publish_allowed = qa_auto_passed or human_approved
    if not has_task:
        final_publish_allowed = final_publish_allowed or post_status in POST_PUBLISHED_STATUSES

    if not has_task:
        path = "manual_post"
        reason = "manual_post_not_bound_to_automatic_qa"
    elif qa_auto_passed:
        path = "qa_auto_passed"
        reason = "qa_auto_passed"
    elif human_approval_recorded:
        path = "human_approved"
        reason = "high_risk_content_was_human_approved"
    elif legacy_human_approval:
        path = "human_approved_legacy_inferred"
        reason = "high_risk_publish_inferred_from_legacy_terminal_state"
    elif task_status in {"failed", "circuit_open", "aborted"} and post_status in POST_PUBLISHED_STATUSES:
        path = "human_approved_legacy_inferred"
        reason = "task_failed_but_post_was_published_separately"
        human_approved = True
        final_publish_allowed = True
    elif task_status == "waiting_human_signoff":
        path = "waiting_human_signoff"
        reason = "high_risk_content_waiting_for_human_signoff"
    elif task_status in {"failed", "circuit_open", "aborted"}:
        path = "blocked"
        reason = "task_reached_terminal_failure_before_publish"
    else:
        path = "pending"
        reason = "publish_decision_not_finalized"

    return {
        "qa_passed": qa_passed,
        "qa_risk_level": risk_level,
        "risk_level": risk_level,
        "qa_integrity_ok": integrity_ok,
        "integrity_ok": integrity_ok,
        "qa_auto_passed": qa_auto_passed,
        "human_approved": human_approved,
        "human_approval_recorded": human_approval_recorded,
        "human_approved_at": review_info.get("human_approved_at"),
        "final_publish_allowed": final_publish_allowed,
        "publish_decision_path": path,
        "publish_decision_reason": reason,
    }
