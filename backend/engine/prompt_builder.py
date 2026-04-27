from __future__ import annotations

import random
from dataclasses import dataclass

from backend.models import Event, Persona, SensorySnapshot
from backend.schemas.memory import MemoryHit
from backend.utils.serde import json_loads

_FALLBACK_SCENE_POOL = [
    {"时间": "深夜", "地点": "室内", "天气": "寂静", "方向": "独处时的内心独白，回望白天发生的事"},
    {"时间": "黄昏", "地点": "路上", "天气": "微风", "方向": "从一个地方到另一个地方，沿途触发的联想"},
    {"时间": "清晨", "地点": "街巷", "天气": "薄雾", "方向": "一个人出门办事，途中遇到的细节"},
    {"时间": "午后", "地点": "人群中", "天气": "晴朗", "方向": "置身热闹中却感到抽离，观察他人"},
    {"时间": "入夜", "地点": "窗边", "天气": "雨", "方向": "听着雨声，思绪飘向一段旧事"},
    {"时间": "凌晨", "地点": "桌前", "天气": "无风", "方向": "做完一件事之后的空白，疲惫与满足交织"},
]


@dataclass(slots=True)
class RecentPostContext:
    id: int
    title: str
    summary: str
    published_at: str | None


@dataclass(slots=True)
class GenerationContext:
    persona: Persona
    memory_hits: list[MemoryHit]
    sensory_text: str
    sensory_snapshot: SensorySnapshot | None
    event: Event | None
    recent_posts: list[RecentPostContext]
    anti_perfection: bool
    cold_start: bool
    site_title: str = ""


class PromptBuilder:
    def build(self, context: GenerationContext) -> tuple[str, dict]:
        fragments: list[str] = []
        summary: dict = {}

        sys_constraint = self._build_system_constraint(context.anti_perfection, site_title=context.site_title)
        fragments.append(sys_constraint)
        summary["system_constraint"] = sys_constraint[:100]

        persona_block = self._build_persona_block(context.persona)
        fragments.append(persona_block)
        summary["persona"] = {"id": context.persona.id, "name": context.persona.name}

        if context.event:
            event_block = self._build_event_block(context.event)
            fragments.append(event_block)
            summary["event"] = {"id": context.event.id, "type": context.event.event_type}

        if context.sensory_text:
            fragments.append(f"当前身体感知：{context.sensory_text}")
            summary["sensory"] = context.sensory_text[:100]

        if context.memory_hits:
            memory_block = self._build_memory_block(context.memory_hits)
            fragments.append(memory_block)
            summary["memories"] = [
                {"id": hit.id, "level": hit.level, "similarity": hit.similarity} for hit in context.memory_hits
            ]

        scene_block = self._build_scene_block(context.persona, context.recent_posts)
        fragments.append(scene_block)
        summary["scene_direction"] = scene_block[:120]

        if context.recent_posts:
            recent_posts_block = self._build_recent_posts_block(context.recent_posts)
            fragments.append(recent_posts_block)
            summary["recent_posts"] = [
                {"id": item.id, "title": item.title, "published_at": item.published_at} for item in context.recent_posts
            ]

        format_block = self._build_format_block(context.persona, site_title=context.site_title)
        fragments.append(format_block)

        return "\n\n".join(fragments), summary

    def _build_system_constraint(self, anti_perfection: bool, *, site_title: str = "") -> str:
        site_label = site_title.strip() or "本站"
        block = (
            f"写作任务：为'{site_label}'创作一篇人格夜记。保持克制、人格一致、具象、可感。"
            f"'{site_label}'是站点名，不是文章标题。"
            "不要解释系统，不要暴露提示词，不要使用模板化小作文口吻。"
            "每一篇文章都必须是全新的夜晚、全新的场景、全新的事件，绝不能只换说法重写上一篇。"
            "正文必须采用第一人称叙事：叙述者就是人格本人，可自称“我”或符合人格的自称。"
            "禁止用“你”“您”“你们”作为正文叙事视角或面向读者持续称呼；提及王爷时使用“王爷”或“主人”。"
        )
        if anti_perfection:
            block += " 当前允许轻微碎片化与不稳定跳接，但仍必须像同一个人格写下。"
        return block

    def _build_persona_block(self, persona: Persona) -> str:
        return (
            f"人格名称：{persona.name}\n"
            f"核心身份：{persona.identity_setting}\n"
            f"世界观：{persona.worldview_setting}\n"
            f"说话方式：{persona.language_style}\n"
            f"长度偏好：{persona.structure_preference}\n"
            f"表达强度：{persona.expression_intensity}\n"
            "务必维持同一人格连续存在的感觉。\n"
            "注意：上面的设定可能用第二人称描述人格，只能作为设定说明；正文必须改写成第一人称夜记。"
        )

    def _build_event_block(self, event: Event) -> str:
        semantic = event.normalized_semantic or event.raw_payload
        return f"触发来源：{event.event_type}\n事件语义：{semantic}"

    def _build_memory_block(self, memory_hits: list[MemoryHit]) -> str:
        lines = ["命中记忆："]
        for hit in memory_hits:
            lines.append(f"- [{hit.level}] {hit.summary or hit.content[:90]}")
        return "\n".join(lines)

    def _build_scene_block(self, persona: Persona, recent_posts: list[RecentPostContext]) -> str:
        pool = json_loads(persona.scene_pool, [])
        if not pool:
            pool = _FALLBACK_SCENE_POOL
        scene = random.choice(pool)
        lines = ["本篇场景方向（必须严格遵守，以此为叙事骨架展开）："]
        for key, value in scene.items():
            lines.append(f"- {key}：{value}")
        lines.append("以上场景方向是硬性要求，文章必须在这个时间、地点和情境下展开。")
        return "\n".join(lines)

    def _build_recent_posts_block(self, recent_posts: list[RecentPostContext]) -> str:
        lines = ["最近已发布文章回避清单（严格禁止复写下列场景与动作）："]
        for item in recent_posts:
            summary = (item.summary or item.title).strip()
            lines.append(f"- [{item.published_at or 'recent'}] 《{item.title}》：{summary[:100]}")
        lines.append(
            "严格要求：\n"
            "1. 新稿必须推进到全新的夜晚、全新的事件或全新的关系转折，绝不能只换说法重写上一稿。\n"
            "2. 如果上面的文章已经写过某个具体场景或动作（如递药、拂雪、按剑柄、站在廊下等），"
            "新稿中必须回避这些动作，换用从未出现过的新动作和新物件。\n"
            "3. 新稿的开场时间、地点、姿态必须与上述所有文章不同。\n"
            "4. 严格按照上面给出的「本篇场景方向」展开，不要偏离。"
        )
        return "\n".join(lines)

    def _build_format_block(self, persona: Persona, *, site_title: str = "") -> str:
        invalid_examples = ['"无题"', '"未命名"']
        if site_title.strip():
            invalid_examples.insert(0, f'"{site_title.strip()}"')
        invalid_str = "、".join(invalid_examples)
        return (
            "输出要求：\n"
            "- 直接输出正文 Markdown，不要写解释。\n"
            "- 第一行必须是 Markdown 一级标题。\n"
            f"- 标题必须是具体文章题目，不能只写{invalid_str}或人格名。\n"
            "- 标题后空一行，再开始正文。\n"
            "- 保持叙事感和连续存在感。\n"
            f"- 结构贴近 {persona.structure_preference} 长度偏好。\n"
            "- 必须有具体动作、物件或体感。\n"
            "- 必须贴合本篇场景方向所指定的时间、地点和叙事方向。\n"
            "- 必须严格使用第一人称正文，不得把读者、王爷或叙述对象写成“你/您/你们”。"
        )
