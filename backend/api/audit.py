from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_session
from backend.models import AuditEventDefinition, AuditLog, Event, GenerationTask
from backend.security.auth import get_current_user
from backend.utils.serde import json_loads
from backend.utils.response import paginated


router = APIRouter()


STATUS_LABELS = {
    "queued": "排队中",
    "running": "执行中",
    "draft_saved": "已存草稿",
    "waiting_human_signoff": "待人工签发",
    "published": "已发布",
    "failed": "失败",
    "circuit_open": "质量熔断",
    "aborted": "已终止",
    "pending_review": "待审核",
    "approved": "已审核通过",
    "archived": "已归档",
    "publish_failed": "发布失败",
}


def _parse_int(value: object) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(str(value))
    except (TypeError, ValueError):
        return None


async def _load_processed_events(
    db: AsyncSession,
    rows: list[AuditLog],
) -> tuple[dict[int, str], dict[int, str], dict[str, AuditEventDefinition]]:
    task_ids: set[int] = set()
    event_ids: set[int] = set()
    actions = {row.action for row in rows}

    for row in rows:
        detail = json_loads(row.detail, {})
        if row.target_type == "task":
            task_id = _parse_int(row.target_id)
            if task_id is not None:
                task_ids.add(task_id)
        if row.target_type == "event":
            event_id = _parse_int(row.target_id)
            if event_id is not None:
                event_ids.add(event_id)
        if isinstance(detail, dict):
            task_id = _parse_int(detail.get("task_id"))
            event_id = _parse_int(detail.get("event_id"))
            if task_id is not None:
                task_ids.add(task_id)
            if event_id is not None:
                event_ids.add(event_id)

    task_event_map: dict[int, str] = {}
    if task_ids:
        task_rows = await db.execute(
            select(GenerationTask.id, Event.normalized_semantic)
            .outerjoin(Event, Event.id == GenerationTask.event_id)
            .where(GenerationTask.id.in_(task_ids))
        )
        task_event_map = {
            task_id: (normalized_semantic or "")
            for task_id, normalized_semantic in task_rows.all()
        }

    event_map: dict[int, str] = {}
    if event_ids:
        event_rows = await db.execute(
            select(Event.id, Event.normalized_semantic).where(Event.id.in_(event_ids))
        )
        event_map = {
            event_id: (normalized_semantic or "")
            for event_id, normalized_semantic in event_rows.all()
        }

    definition_map: dict[str, AuditEventDefinition] = {}
    if actions:
        definition_rows = await db.scalars(
            select(AuditEventDefinition).where(AuditEventDefinition.action.in_(actions))
        )
        definition_map = {row.action: row for row in definition_rows}

    return task_event_map, event_map, definition_map


def _format_status(status: object) -> str:
    text = str(status or "").strip()
    if not text:
        return ""
    return STATUS_LABELS.get(text, text)


def _resolve_processed_event(
    row: AuditLog,
    detail: object,
    task_event_map: dict[int, str],
    event_map: dict[int, str],
) -> str:
    if row.target_type == "task":
        task_id = _parse_int(row.target_id)
        if task_id is not None and task_event_map.get(task_id):
            return task_event_map[task_id]

    if row.target_type == "event":
        event_id = _parse_int(row.target_id)
        if event_id is not None and event_map.get(event_id):
            return event_map[event_id]

    if isinstance(detail, dict):
        task_id = _parse_int(detail.get("task_id"))
        if task_id is not None and task_event_map.get(task_id):
            return task_event_map[task_id]

        event_id = _parse_int(detail.get("event_id"))
        if event_id is not None and event_map.get(event_id):
            return event_map[event_id]

    return ""


def _resolve_event_mapping(
    row: AuditLog,
    detail: object,
    task_event_map: dict[int, str],
    event_map: dict[int, str],
) -> str:
    processed_event = _resolve_processed_event(row, detail, task_event_map, event_map)
    if processed_event:
        return processed_event

    if not isinstance(detail, dict):
        return ""

    if row.action == "setup.complete":
        site_title = str(detail.get("site_title") or "").strip()
        if site_title:
            return f'站点标题设为“{site_title}”'
        return "已完成首次配置"

    if row.action == "system.apply_site_runtime":
        domain = str(detail.get("domain") or "").strip()
        enabled = bool(detail.get("enabled"))
        reason = str(detail.get("reason") or "").strip()
        if domain and enabled:
            return f"站点入口已切到 {domain}"
        if reason:
            return reason
        return "已刷新站点访问设置"

    if row.action == "system.ensure_seed_persona":
        if detail.get("created"):
            return "已补齐默认人格设定"
        return "默认人格设定已检查"

    if row.action == "system.ensure_encryption_key":
        return "已补齐系统保护项"

    if row.action == "system.import_legacy_assets":
        posts = int(detail.get("posts") or 0)
        memories = int(detail.get("memories") or 0)
        if posts or memories:
            return f"导入旧文章 {posts} 篇、旧记忆 {memories} 条"
        return "已检查旧数据导入"

    if row.action == "system.restart_recovery":
        recovered_tasks = int(detail.get("recovered_tasks") or 0)
        if recovered_tasks:
            return f"已恢复 {recovered_tasks} 个中断任务"
        return "已检查中断任务恢复"

    if row.action == "config.update":
        changed_keys = detail.get("changed_keys") or []
        if isinstance(changed_keys, list) and changed_keys:
            return f"已更新 {len(changed_keys)} 项配置"
        count = int(detail.get("count") or 0)
        if count:
            return f"已更新 {count} 项配置"
        return "系统设置已更新"

    if row.action == "task.status_change":
        from_status = _format_status(detail.get("from"))
        to_status = _format_status(detail.get("to"))
        if from_status and to_status:
            return f"{from_status} -> {to_status}"
        if to_status:
            return f"状态变为 {to_status}"
        return "任务状态已更新"

    if row.action == "task.create":
        trigger_source = str(detail.get("trigger_source") or "").strip()
        if trigger_source == "manual":
            return "由后台手动发起"
        if trigger_source:
            return f"触发来源：{trigger_source}"
        return "已创建新的写作任务"

    if row.action == "ghost.export":
        return "已生成一份备份包"

    if row.action == "ghost.import":
        return "已导入备份内容"

    if row.action == "auth.login":
        return "已进入后台"

    if row.action == "auth.logout":
        return "已退出后台"

    if row.action == "auth.change_password":
        return "管理员密码已更新"

    return ""


def _resolve_display_target(
    row: AuditLog,
    definition: AuditEventDefinition | None,
) -> str:
    if definition and definition.target_label:
        if row.target_type in {"persona", "memory", "post", "task", "folder_monitor"} and row.target_id:
            return f"{definition.target_label} #{row.target_id}"
        if row.target_type == "ghost" and row.target_id:
            return f"{definition.target_label} {row.target_id}"
        return definition.target_label

    if row.target_type == "system" and row.target_id == "startup":
        return "启动自检"
    if row.target_type == "system" and row.target_id == "1":
        return "首次配置"
    if row.target_type == "user":
        return "管理员账号"
    if row.target_type == "config":
        return "系统设置"
    if row.target_type == "event" and row.target_id:
        return f"触发事件 #{row.target_id}"
    if row.target_type and row.target_id:
        return f"{row.target_type} #{row.target_id}"
    return "-"


@router.get("")
async def list_audit_logs(
    severity: str | None = None,
    action: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user),
) -> object:
    stmt = select(AuditLog).outerjoin(AuditEventDefinition, AuditEventDefinition.action == AuditLog.action)
    count_stmt = select(func.count()).select_from(AuditLog).outerjoin(
        AuditEventDefinition,
        AuditEventDefinition.action == AuditLog.action,
    )
    if severity:
        stmt = stmt.where(AuditLog.severity == severity)
        count_stmt = count_stmt.where(AuditLog.severity == severity)
    if action:
        stmt = stmt.where(
            or_(
                AuditLog.action.contains(action),
                AuditEventDefinition.display_name.contains(action),
            )
        )
        count_stmt = count_stmt.where(
            or_(
                AuditLog.action.contains(action),
                AuditEventDefinition.display_name.contains(action),
            )
        )
    stmt = stmt.order_by(AuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.scalars(stmt)).all()
    total = await db.scalar(count_stmt) or 0
    task_event_map, event_map, definition_map = await _load_processed_events(db, rows)
    items = [
        {
            "id": row.id,
            "timestamp": row.timestamp,
            "actor": row.actor,
            "action": row.action,
            "display_action": (definition_map.get(row.action).display_name if definition_map.get(row.action) else row.action),
            "target_type": row.target_type,
            "target_id": row.target_id,
            "display_target": _resolve_display_target(row, definition_map.get(row.action)),
            "detail": detail,
            "ip_address": row.ip_address,
            "severity": row.severity,
            "processed_event": _resolve_processed_event(row, detail, task_event_map, event_map),
            "event_mapping": _resolve_event_mapping(row, detail, task_event_map, event_map),
        }
        for row in rows
        for detail in [json_loads(row.detail, {})]
    ]
    return paginated(items, int(total), page, page_size)
