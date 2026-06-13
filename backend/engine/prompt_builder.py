from __future__ import annotations

import random
from dataclasses import dataclass, field

from backend.models import Event, Persona, SensorySnapshot
from backend.schemas.memory import MemoryHit
from backend.utils.serde import json_loads

_FALLBACK_SCENE_POOL = [
    {"时间": "深夜", "地点": "练武场", "天气": "月明", "动作": "独自收剑", "方向": "把白天压住的情绪落进剑势收尾里"},
    {
        "时间": "黄昏",
        "地点": "城外山道",
        "天气": "秋风",
        "动作": "护送归程",
        "方向": "途中发生一个需要临时判断的小变故",
    },
    {"时间": "清晨", "地点": "药铺街巷", "天气": "薄雾", "动作": "买药遮伤", "方向": "不想让人察觉旧伤，却被细节泄露"},
    {
        "时间": "午后",
        "地点": "集市",
        "天气": "晴朗",
        "动作": "在人群中警戒",
        "方向": "热闹与暗线并行，最后带出一个新线索",
    },
    {"时间": "入夜", "地点": "藏书阁", "天气": "闷热", "动作": "查旧卷宗", "方向": "从纸页里翻出一件会改变判断的旧事"},
    {"时间": "凌晨", "地点": "客栈后院", "天气": "暴雨", "动作": "清点行囊", "方向": "赶路被困，必须做一次取舍"},
    {"时间": "傍晚", "地点": "渡口", "天气": "江风", "动作": "送人离岸", "方向": "把没说的话压在船离开之前"},
    {
        "时间": "天亮前",
        "地点": "暗巷",
        "天气": "无风",
        "动作": "处理伏击后痕迹",
        "方向": "事已办完，却要面对是否越权的后果",
    },
    {"时间": "正午", "地点": "茶楼", "天气": "阴天", "动作": "听旧识闲谈", "方向": "从别人的近况里照见另一种活法"},
    {"时间": "夜晚", "地点": "屋顶", "天气": "繁星", "动作": "独自望远", "方向": "短暂脱离守候位置后又主动回到原处"},
    {
        "时间": "白天",
        "地点": "铁匠铺",
        "天气": "晴热",
        "动作": "修一件兵器",
        "方向": "兵器上的损伤暴露出上一场任务的代价",
    },
    {
        "时间": "春雨初停",
        "地点": "厨房或茶室",
        "天气": "潮湿",
        "动作": "备一盏热茶",
        "方向": "把关心藏进一个不会被追问的小物件",
    },
    {"时间": "夏夜", "地点": "湖边", "天气": "闷热", "动作": "巡看水面", "方向": "平静水声下藏着一次试探"},
    {"时间": "冬夜", "地点": "城墙", "天气": "大风", "动作": "确认烽火讯号", "方向": "远处消息逼近，心绪必须先稳住"},
]


@dataclass(slots=True)
class RecentPostContext:
    id: int
    title: str
    summary: str
    published_at: str | None
    opening: str = ""
    ending: str = ""
    motifs: list[str] = field(default_factory=list)


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
            "标题、开头第一幕、结尾姿态和核心物件都必须与近期文章明显不同。"
            "本篇必须发生一个可辨认的状态变化：得到线索、做出取舍、处理后果、关系出现细小转折，至少满足其一。"
            "正文必须采用第一人称叙事：叙述者就是人格本人，可自称“我”或符合人格的自称。"
            "禁止用“你”“您”“你们”作为正文叙事视角或面向读者持续称呼；提及王爷时使用“王爷”或“主人”。"
        )
        if anti_perfection:
            block += " 当前允许轻微碎片化与不稳定跳接，但仍必须像同一个人格写下。"
        return block

    def _build_persona_block(self, persona: Persona) -> str:
        lines = [
            f"人格名称：{persona.name}\n"
            f"核心身份：{persona.identity_setting}\n"
            f"世界观：{persona.worldview_setting}\n"
            f"说话方式：{persona.language_style}\n"
            f"长度偏好：{persona.structure_preference}\n"
            f"表达强度：{persona.expression_intensity}\n"
            "务必维持同一人格连续存在的感觉。\n"
            "注意：上面的设定可能用第二人称描述人格，只能作为设定说明；正文必须改写成第一人称夜记。"
        ]
        taboos = [str(item).strip() for item in json_loads(persona.taboos, []) if str(item).strip()]
        if taboos:
            lines.append("硬性禁忌：")
            lines.extend(f"- {item}" for item in taboos)
            lines.append("以上禁忌必须遵守；如与其他设定冲突，以禁忌为准。")
        return "\n".join(lines)

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
        scene = self._select_scene(pool, recent_posts)
        lines = ["本篇场景方向（必须严格遵守，以此为叙事骨架展开）："]
        for key, value in scene.items():
            lines.append(f"- {key}：{value}")
        lines.append("以上场景方向是硬性要求，文章必须在这个时间、地点、动作和情境下展开。")
        lines.append("不要把场景写回近期文章已经使用过的马厩、回府路、同一段廊下等待或同一种残月收束。")
        return "\n".join(lines)

    def _select_scene(self, pool: list[object], recent_posts: list[RecentPostContext]) -> dict:
        scenes = [item for item in pool if isinstance(item, dict) and item]
        if not scenes:
            return random.choice(_FALLBACK_SCENE_POOL)

        recent_motifs = {motif for post in recent_posts for motif in post.motifs}
        if not recent_motifs:
            return random.choice(scenes)

        scored: list[tuple[int, dict]] = []
        for scene in scenes:
            scene_text = " ".join(str(value) for value in scene.values())
            score = sum(1 for motif in recent_motifs if motif and motif in scene_text)
            scored.append((score, scene))
        min_score = min(score for score, _ in scored)
        candidates = [scene for score, scene in scored if score == min_score]
        return random.choice(candidates)

    def _build_recent_posts_block(self, recent_posts: list[RecentPostContext]) -> str:
        lines = ["最近已发布文章回避清单（严格禁止复写下列标题、开头、结尾、场景与动作）："]
        for item in recent_posts:
            summary = (item.summary or item.title).strip()
            parts = [f"- [{item.published_at or 'recent'}] 《{item.title}》：{summary[:100]}"]
            if item.opening:
                parts.append(f"开头：{item.opening[:90]}")
            if item.ending:
                parts.append(f"收束：{item.ending[-70:]}")
            if item.motifs:
                parts.append(f"母题：{'、'.join(item.motifs[:8])}")
            lines.append("；".join(parts))
        lines.append(
            "严格要求：\n"
            "1. 新稿必须推进到全新的夜晚、全新的事件或全新的关系转折，绝不能只换说法重写上一稿。\n"
            "2. 如果上面的文章已经写过某个具体场景或动作（如递药、拂雪、按剑柄、站在廊下等），"
            "新稿中必须回避这些动作，换用从未出现过的新动作和新物件。\n"
            "3. 新稿标题不得复用近期标题，也不要继续使用同一组“夜、旧、残、归、渡”等窄词。\n"
            "4. 新稿的开场时间、地点、姿态必须与上述所有文章不同，结尾也不得再落回等待、沉默、转身、站住的同一姿态。\n"
            "5. 严格按照上面给出的「本篇场景方向」展开，不要偏离。"
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
            "- 正文建议控制在 900 到 1500 个中文字符之间，宁可凝练，也不要为凑篇幅重复同一情绪。\n"
            "- 必须有具体动作、物件或体感。\n"
            "- 必须写出一个具体进展或后果，不要只停留在原地等待和内心独白。\n"
            "- 必须贴合本篇场景方向所指定的时间、地点和叙事方向。\n"
            "- 必须严格使用第一人称正文，不得把读者、王爷或叙述对象写成“你/您/你们”。"
        )
