from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import AuditEventDefinition
from backend.utils.time import utcnow_iso


KNOWN_AUDIT_EVENTS = [
    {"action": "auth.login", "display_name": "管理员登录", "target_label": "管理员账号"},
    {"action": "auth.logout", "display_name": "退出登录", "target_label": "管理员账号"},
    {"action": "auth.change_password", "display_name": "修改密码", "target_label": "管理员账号"},
    {"action": "setup.complete", "display_name": "完成首次配置", "target_label": "首次配置"},
    {"action": "config.update", "display_name": "更新系统设置", "target_label": "系统设置"},
    {"action": "persona.create", "display_name": "创建人格设定", "target_label": "人格设定"},
    {"action": "persona.update", "display_name": "修改人格设定", "target_label": "人格设定"},
    {"action": "persona.delete", "display_name": "删除人格设定", "target_label": "人格设定"},
    {"action": "persona.activate", "display_name": "启用人格设定", "target_label": "人格设定"},
    {"action": "persona.repair_corrupted", "display_name": "修复人格设定", "target_label": "人格设定"},
    {"action": "memory.create", "display_name": "创建记忆碎片", "target_label": "记忆碎片"},
    {"action": "memory.update", "display_name": "修改记忆碎片", "target_label": "记忆碎片"},
    {"action": "memory.delete", "display_name": "删除记忆碎片", "target_label": "记忆碎片"},
    {"action": "memory.promote", "display_name": "提升记忆等级", "target_label": "记忆碎片"},
    {"action": "post.create", "display_name": "创建文章", "target_label": "文章"},
    {"action": "post.update", "display_name": "修改文章", "target_label": "文章"},
    {"action": "post.delete", "display_name": "删除文章", "target_label": "文章"},
    {"action": "post.publish", "display_name": "发布文章", "target_label": "文章"},
    {"action": "post.approve", "display_name": "审核通过", "target_label": "文章"},
    {"action": "post.archive", "display_name": "归档文章", "target_label": "文章"},
    {"action": "post.revert", "display_name": "回退文章版本", "target_label": "文章"},
    {"action": "task.create", "display_name": "创建写作任务", "target_label": "写作任务"},
    {"action": "task.status_change", "display_name": "任务状态变更", "target_label": "写作任务"},
    {"action": "ghost.export", "display_name": "导出备份", "target_label": "备份包"},
    {"action": "ghost.import", "display_name": "导入备份", "target_label": "备份包"},
    {"action": "folder_monitor.create", "display_name": "新增监听目录", "target_label": "监听目录"},
    {"action": "folder_monitor.delete", "display_name": "删除监听目录", "target_label": "监听目录"},
    {"action": "system.ensure_encryption_key", "display_name": "补齐系统保护项", "target_label": "启动自检"},
    {"action": "system.ensure_seed_persona", "display_name": "补齐默认人格设定", "target_label": "启动自检"},
    {"action": "system.import_legacy_assets", "display_name": "导入旧数据", "target_label": "启动自检"},
    {"action": "system.apply_site_runtime", "display_name": "刷新站点访问设置", "target_label": "启动自检"},
    {"action": "system.restart_recovery", "display_name": "恢复中断任务", "target_label": "启动自检"},
]


async def ensure_audit_event_definitions(db: AsyncSession) -> None:
    rows = await db.scalars(select(AuditEventDefinition))
    existing = {row.action: row for row in rows}
    now = utcnow_iso()

    for item in KNOWN_AUDIT_EVENTS:
        row = existing.get(item["action"])
        if row is None:
            db.add(
                AuditEventDefinition(
                    action=item["action"],
                    display_name=item["display_name"],
                    target_label=item["target_label"],
                    created_at=now,
                    updated_at=now,
                )
            )
            continue

        if row.display_name != item["display_name"] or row.target_label != item["target_label"]:
            row.display_name = item["display_name"]
            row.target_label = item["target_label"]
            row.updated_at = now
