from __future__ import annotations

from backend.utils.publish_decision import build_publish_decision


def test_legacy_human_approval_is_inferred_for_archived_published_post():
    decision = build_publish_decision(
        qa_result={"passed": False, "risk_level": "high", "integrity_ok": True},
        review_info={"reason": "waiting_human_signoff", "task_id": 10},
        task_status="published",
        post_status="archived",
        has_task=True,
    )

    assert decision["human_approved"] is True
    assert decision["final_publish_allowed"] is True
    assert decision["publish_decision_path"] == "human_approved_legacy_inferred"
