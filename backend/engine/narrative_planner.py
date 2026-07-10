"""Narrative planner: long-arc worldline + per-post task cards.

Design goals
------------
- One persona's real publishing window of 3–5 months ≈ 5–10 world years
  of prime years (default ~15 posts / world year).
- Diaries stay diary-scale: sparse political/relationship pressure, not
  chapter-novel plot dumps.
- Fight homogenization via forced relation-tone / scene-bucket rotation,
  opening/title avoid lists, and phase-aware pressure notes.
"""

from __future__ import annotations

import hashlib
import random
import re
from dataclasses import asdict, dataclass, field
from typing import Any

from backend.utils.serde import json_dumps, json_loads

# ── Worldline phases (prime years, ~5–10y total) ─────────────────

WORLD_PHASES: list[dict[str, Any]] = [
    {
        "id": "shadow_stable",
        "name": "影中位稳",
        "year_start": 0,
        "year_end": 2,
        "pressure": (
            "你仍站在王爷半步之后，位置看似稳固。江湖表面平静，暗线只偶尔颤一下。"
            "姐姐多在外行走，回府是例外。你把偏爱误读为「差遣在影里」，日日守着。"
        ),
        "diary_hints": [
            "一件小事里的规矩感",
            "一次未被点名的守候",
            "远方姐姐的消息只是一句",
        ],
    },
    {
        "id": "misread_deepens",
        "name": "误解加深",
        "year_start": 2,
        "year_end": 4,
        "pressure": (
            "姐姐回府更勤或带功而归，名望与体面在灯下被说起。"
            "你仍不知王爷偏爱的真相，比较与不服在夜里变重，却不许失态。"
        ),
        "diary_hints": [
            "一句淡比较",
            "被误读的安排",
            "压住的不服",
        ],
    },
    {
        "id": "shadow_tightens",
        "name": "暗线收紧",
        "year_start": 4,
        "year_end": 6,
        "pressure": (
            "武林暗潮涌动：门派合纵、密令加重、有人试探王府虚实。"
            "你被派去脏活更多，旧伤与夜路叠在一起。一统江湖的传闻只在边角掠过，你不信大话，只信刀。"
        ),
        "diary_hints": [
            "密令途中的疲惫",
            "府外眼线",
            "局势变紧而仍守规矩",
        ],
    },
    {
        "id": "favor_surfaces",
        "name": "偏爱渐显",
        "year_start": 6,
        "year_end": 8,
        "pressure": (
            "王爷的偏爱开始有可感痕迹：一句多问、一次留人、一次把姐姐的差遣推远。"
            "你仍不敢认，只当是任务需要。姐姐察觉你的伤，却说不出口。"
        ),
        "diary_hints": [
            "一次差点被看穿的温柔",
            "偏爱的误读",
            "姐姐欲言又止",
        ],
    },
    {
        "id": "year_of_choice",
        "name": "抉择之年",
        "year_start": 8,
        "year_end": 10,
        "pressure": (
            "局势逼近分岔：护王爷、护暗线、还是与姐姐正面摊开命运的不公。"
            "一统武林不是口号，是有人想借刀、借名、借府。你仍不能撒娇哭喊，只能在夜记里写清自己的位置。"
        ),
        "diary_hints": [
            "不得不选时的冷",
            "位份危机的一刺",
            "收束回守护",
        ],
    },
]

RELATION_TONES = ("主从", "守护", "占有", "暗火")
SCENE_BUCKETS = ("府内夜", "江湖路", "姐姐线", "密令", "白日闲笔")

# Keywords for bucket classification of scene_pool entries.
_BUCKET_KEYWORDS: dict[str, tuple[str, ...]] = {
    "姐姐线": ("姐姐", "西厢", "送姐姐", "接姐姐", "回府"),
    "密令": ("密令", "密林", "暗巷", "伏击", "边关", "脏活", "夜行", "追踪"),
    "江湖路": ("客栈", "驿", "渡口", "码头", "山道", "酒馆", "茶楼", "药铺", "铁匠", "武器铺", "回府的路上", "马厩"),
    "白日闲笔": ("午后", "正午", "白天", "清晨", "花园", "湖边", "集市", "厨房", "茶室", "藏书阁"),
    "府内夜": ("廊下", "寝室", "书房", "后院", "练武场", "王府", "屋顶", "高处", "庭院"),
}

_TONE_REQUIREMENTS: dict[str, list[str]] = {
    "主从": [
        "至少一次「王爷」称呼与一次位份感（可自称属下，或写出规矩/半步距离）。",
        "不要写成平等闺蜜闲聊；主从是外壳，感情压在规矩里。",
    ],
    "守护": [
        "写出一次可感的守护动作或警戒（不必拔剑，递物、掩窗、挡风、先查路亦可）。",
        "危险或脆弱可以点到，但不要喊口号。",
    ],
    "占有": [
        "第三层必须落到「为什么不能是我 / 最贴近的位置」的淡刺，禁止只写守夜站位。",
        "若写到姐姐：禁止仅用「教过我/在外面办事」一句交差；须有比较、误读或说不出口的疼之一。",
        "禁止直接写「我嫉妒」四个字；用比较、停顿、收手来写。",
    ],
    "暗火": [
        "允许一闪而过的黑念/独占念，必须立刻收回守护与克制；禁止真伤害王爷或姐姐。",
        "失控要写成更稳、更冷、更轻，而不是爆发。",
    ],
}


@dataclass(slots=True)
class NarrativeState:
    posts_published: int = 0
    world_year: float = 0.0
    phase_id: str = "shadow_stable"
    last_relation_tones: list[str] = field(default_factory=list)
    last_scene_buckets: list[str] = field(default_factory=list)
    last_titles: list[str] = field(default_factory=list)
    last_openings: list[str] = field(default_factory=list)
    sister_in_residence: bool | None = None
    last_secret_order: str = ""
    wound_known: bool | None = None
    lord_warm_line: str = ""
    plot_pressure: str = ""

    def to_json(self) -> str:
        return json_dumps(asdict(self))

    @classmethod
    def from_json(cls, raw: str | None) -> NarrativeState:
        data = json_loads(raw or "", {})
        if not isinstance(data, dict):
            return cls()
        return cls(
            posts_published=int(data.get("posts_published") or 0),
            world_year=float(data.get("world_year") or 0.0),
            phase_id=str(data.get("phase_id") or "shadow_stable"),
            last_relation_tones=[str(x) for x in (data.get("last_relation_tones") or [])][-12:],
            last_scene_buckets=[str(x) for x in (data.get("last_scene_buckets") or [])][-12:],
            last_titles=[str(x) for x in (data.get("last_titles") or [])][-20:],
            last_openings=[str(x) for x in (data.get("last_openings") or [])][-14:],
            sister_in_residence=data.get("sister_in_residence"),
            last_secret_order=str(data.get("last_secret_order") or ""),
            wound_known=data.get("wound_known"),
            lord_warm_line=str(data.get("lord_warm_line") or ""),
            plot_pressure=str(data.get("plot_pressure") or ""),
        )


@dataclass(slots=True)
class NarrativeTaskCard:
    relation_tone: str
    scene_bucket: str
    scene: dict[str, str]
    world_year: float
    world_year_label: str
    phase_id: str
    phase_name: str
    phase_pressure: str
    diary_hint: str
    avoid_titles: list[str]
    avoid_openings: list[str]
    requirements: list[str]
    relation_state_notes: list[str]
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "relation_tone": self.relation_tone,
            "scene_bucket": self.scene_bucket,
            "scene": self.scene,
            "world_year": self.world_year,
            "world_year_label": self.world_year_label,
            "phase_id": self.phase_id,
            "phase_name": self.phase_name,
            "phase_pressure": self.phase_pressure,
            "diary_hint": self.diary_hint,
            "avoid_titles": self.avoid_titles,
            "avoid_openings": self.avoid_openings,
            "requirements": self.requirements,
            "relation_state_notes": self.relation_state_notes,
            "enabled": self.enabled,
        }


class NarrativePlanner:
    """Build per-post task cards and advance slow worldline state."""

    STATE_KEY_PREFIX = "narrative.state."
    DEFAULT_POSTS_PER_WORLD_YEAR = 15
    OPENING_FINGERPRINT_CHARS = 40
    RECENT_BUCKET_WINDOW = 5
    RECENT_TONE_WINDOW = 7

    def state_key(self, persona_id: int) -> str:
        return f"{self.STATE_KEY_PREFIX}{persona_id}"

    def load_state(self, raw: str | None) -> NarrativeState:
        return NarrativeState.from_json(raw)

    def phase_for_year(self, world_year: float) -> dict[str, Any]:
        year = max(0.0, float(world_year))
        for phase in WORLD_PHASES:
            if phase["year_start"] <= year < phase["year_end"]:
                return phase
        return WORLD_PHASES[-1]

    def classify_scene_bucket(self, scene: dict[str, Any]) -> str:
        blob = " ".join(str(v) for v in scene.values())
        scores: dict[str, int] = {bucket: 0 for bucket in SCENE_BUCKETS}
        for bucket, keywords in _BUCKET_KEYWORDS.items():
            for kw in keywords:
                if kw in blob:
                    scores[bucket] += 1
        # Prefer non-zero; default 府内夜 only if clearly courtyard, else 江湖路 for travel-ish.
        best = max(SCENE_BUCKETS, key=lambda b: (scores[b], 0 if b == "府内夜" else 1))
        if scores[best] == 0:
            return "江湖路"
        return best

    def pick_relation_tone(self, state: NarrativeState, *, rng: random.Random) -> str:
        recent = state.last_relation_tones[-self.RECENT_TONE_WINDOW :]
        # Force 占有 if missing in last 7.
        if recent and "占有" not in recent:
            return "占有"
        # Soft force 暗火 about once per cycle of 7.
        if recent and "暗火" not in recent and len(recent) >= 6:
            return "暗火"
        candidates = [t for t in RELATION_TONES if t not in recent[-2:]]
        if not candidates:
            candidates = list(RELATION_TONES)
        # Weight: 守护 and 主从 common; 占有/暗火 less frequent but guaranteed by rules above.
        weights = {"主从": 3, "守护": 3, "占有": 2, "暗火": 1}
        pool: list[str] = []
        for tone in candidates:
            pool.extend([tone] * weights.get(tone, 1))
        return rng.choice(pool)

    def pick_scene(
        self,
        scene_pool: list[dict[str, Any]],
        state: NarrativeState,
        *,
        rng: random.Random,
        forced_bucket: str | None = None,
    ) -> tuple[dict[str, str], str]:
        if not scene_pool:
            scene_pool = [
                {
                    "时间": "深夜",
                    "地点": "室内",
                    "天气": "寂静",
                    "方向": "独处时的内心独白，回望白天发生的事",
                }
            ]

        recent_buckets = state.last_scene_buckets[-self.RECENT_BUCKET_WINDOW :]
        annotated: list[tuple[dict[str, str], str]] = []
        for raw in scene_pool:
            if not isinstance(raw, dict):
                continue
            scene = {str(k): str(v) for k, v in raw.items()}
            bucket = self.classify_scene_bucket(scene)
            annotated.append((scene, bucket))

        if not annotated:
            scene = {str(k): str(v) for k, v in scene_pool[0].items()}
            return scene, self.classify_scene_bucket(scene)

        target_bucket = forced_bucket
        if target_bucket is None:
            # Prefer buckets not used in recent window; rotate if all used.
            unused = [b for b in SCENE_BUCKETS if b not in recent_buckets]
            if not unused:
                # Drop the most recent bucket preference.
                unused = [b for b in SCENE_BUCKETS if not recent_buckets or b != recent_buckets[-1]]
            # Soft bias: 府内夜 should not dominate — if it appeared in last 2, avoid.
            if recent_buckets[-2:].count("府内夜") >= 1 and "府内夜" in unused and len(unused) > 1:
                unused = [b for b in unused if b != "府内夜"]
            target_bucket = rng.choice(unused or list(SCENE_BUCKETS))

        bucket_scenes = [(s, b) for s, b in annotated if b == target_bucket]
        if not bucket_scenes:
            bucket_scenes = annotated

        # Avoid exact same 地点 as recent openings if possible — light diversity by hash of 地点.
        recent_places = set()
        for opening in state.last_openings[-5:]:
            recent_places.add(opening[:8])

        def score(item: tuple[dict[str, str], str]) -> float:
            scene, _b = item
            place = scene.get("地点", "")
            penalty = 0.0
            if any(place and place[:4] in op for op in state.last_openings[-5:]):
                penalty += 2.0
            return rng.random() - penalty

        scene, bucket = max(bucket_scenes, key=score)
        return scene, bucket

    def build_task_card(
        self,
        *,
        persona_id: int,
        scene_pool: list[dict[str, Any]],
        state: NarrativeState,
        recent_titles: list[str] | None = None,
        recent_openings: list[str] | None = None,
        posts_per_world_year: int = DEFAULT_POSTS_PER_WORLD_YEAR,
        enabled: bool = True,
        seed: str | None = None,
    ) -> NarrativeTaskCard:
        posts_per_world_year = max(6, int(posts_per_world_year or self.DEFAULT_POSTS_PER_WORLD_YEAR))
        seed_material = seed or f"{persona_id}:{state.posts_published}:{state.world_year}"
        rng = random.Random(int(hashlib.sha256(seed_material.encode()).hexdigest()[:16], 16))

        phase = self.phase_for_year(state.world_year)
        tone = self.pick_relation_tone(state, rng=rng) if enabled else "守护"
        scene, bucket = self.pick_scene(scene_pool, state, rng=rng)

        # Align bucket with 占有 sometimes → prefer 姐姐线 if available.
        if tone == "占有" and "姐姐线" not in state.last_scene_buckets[-3:]:
            sister_scenes = [
                s
                for s in scene_pool
                if isinstance(s, dict) and self.classify_scene_bucket(s) == "姐姐线"
            ]
            if sister_scenes:
                scene, bucket = self.pick_scene(sister_scenes, state, rng=rng, forced_bucket="姐姐线")

        if tone == "暗火" and bucket == "府内夜" and rng.random() < 0.5:
            scene, bucket = self.pick_scene(scene_pool, state, rng=rng, forced_bucket="密令")

        avoid_titles = list(dict.fromkeys((recent_titles or state.last_titles)[-20:]))
        avoid_openings = list(dict.fromkeys((recent_openings or state.last_openings)[-14:]))

        requirements = list(_TONE_REQUIREMENTS.get(tone, []))
        requirements.extend(
            [
                "必须有具体动作、物件或体感；禁止复述设定小传。",
                "开场时间、地点、姿态不得与回避清单中的文章相同。",
                f"本篇场景大类为「{bucket}」，须在指定时间/地点/情境下展开。",
                "世界线压力只作背景渗入日记，不要写成章回体密谋大纲。",
            ]
        )
        diary_hints = phase.get("diary_hints") or ["一处可感细节"]
        diary_hint = rng.choice(list(diary_hints))
        requirements.append(f"情绪落点建议：{diary_hint}（点到为止，不解释）。")

        relation_notes = self._relation_state_notes(state, phase)

        year_label = self._year_label(state.world_year)
        return NarrativeTaskCard(
            relation_tone=tone,
            scene_bucket=bucket,
            scene={str(k): str(v) for k, v in scene.items()},
            world_year=round(float(state.world_year), 2),
            world_year_label=year_label,
            phase_id=str(phase["id"]),
            phase_name=str(phase["name"]),
            phase_pressure=str(phase["pressure"]),
            diary_hint=str(diary_hint),
            avoid_titles=avoid_titles,
            avoid_openings=avoid_openings,
            requirements=requirements,
            relation_state_notes=relation_notes,
            enabled=enabled,
        )

    def advance_after_publish(
        self,
        state: NarrativeState,
        card: NarrativeTaskCard | None,
        *,
        title: str,
        content: str,
        posts_per_world_year: int = DEFAULT_POSTS_PER_WORLD_YEAR,
    ) -> NarrativeState:
        posts_per_world_year = max(6, int(posts_per_world_year or self.DEFAULT_POSTS_PER_WORLD_YEAR))
        opening = self.opening_fingerprint(content)
        new_state = NarrativeState(
            posts_published=state.posts_published + 1,
            world_year=state.world_year + (1.0 / posts_per_world_year),
            phase_id=state.phase_id,
            last_relation_tones=list(state.last_relation_tones),
            last_scene_buckets=list(state.last_scene_buckets),
            last_titles=list(state.last_titles),
            last_openings=list(state.last_openings),
            sister_in_residence=state.sister_in_residence,
            last_secret_order=state.last_secret_order,
            wound_known=state.wound_known,
            lord_warm_line=state.lord_warm_line,
            plot_pressure=state.plot_pressure,
        )
        if card is not None:
            new_state.last_relation_tones = (new_state.last_relation_tones + [card.relation_tone])[-12:]
            new_state.last_scene_buckets = (new_state.last_scene_buckets + [card.scene_bucket])[-12:]
            # Light relation-state inference from card bucket/tone (not NLP — diary-level hints).
            if card.scene_bucket == "姐姐线":
                new_state.sister_in_residence = True
            elif card.scene_bucket == "江湖路" and card.relation_tone == "守护":
                # Sister often away while 全真 travels for the lord.
                pass
            if card.scene_bucket == "密令":
                place = card.scene.get("地点", "途中")
                new_state.last_secret_order = f"{card.world_year_label}密令于{place}"
            if card.relation_tone == "占有" and "偏爱" in card.phase_pressure:
                new_state.lord_warm_line = new_state.lord_warm_line or "王爷似有一句未说尽的话"
            phase = self.phase_for_year(new_state.world_year)
            new_state.plot_pressure = str(phase["pressure"])[:120]
            new_state.phase_id = str(phase["id"])
        else:
            phase = self.phase_for_year(new_state.world_year)
            new_state.phase_id = str(phase["id"])
            new_state.plot_pressure = str(phase["pressure"])[:120]

        if title:
            new_state.last_titles = (new_state.last_titles + [title.strip()])[-20:]
        if opening:
            new_state.last_openings = (new_state.last_openings + [opening])[-14:]
        return new_state

    def format_task_card_block(self, card: NarrativeTaskCard) -> str:
        if not card.enabled:
            return ""
        lines = [
            "本篇任务卡（硬性遵守，优先于空泛发挥）：",
            f"- 世界线：{card.world_year_label} · 阶段「{card.phase_name}」",
            f"- 局势渗入（日记级，勿写成阴谋大纲）：{card.phase_pressure}",
            f"- 关系主音：{card.relation_tone}（另两层最多点到为止）",
            f"- 场景大类：{card.scene_bucket}",
            "- 场景方向：",
        ]
        for key, value in card.scene.items():
            lines.append(f"  · {key}：{value}")
        if card.relation_state_notes:
            lines.append("- 当前关系状态（可延续，勿自相矛盾）：")
            lines.extend(f"  · {note}" for note in card.relation_state_notes)
        lines.append("- 必达：")
        lines.extend(f"  {i}. {req}" for i, req in enumerate(card.requirements, start=1))
        if card.avoid_titles:
            lines.append("- 禁用标题（不得完全相同）：" + "、".join(f"《{t}》" for t in card.avoid_titles[:12]))
        if card.avoid_openings:
            lines.append("- 禁用开场指纹（前约40字不得近似）：")
            lines.extend(f"  · {op}" for op in card.avoid_openings[:8])
        lines.append(
            "写作提醒：每一篇都是全新的夜晚与事件；长线只通过细节与局势轻颤推进，"
            "禁止日日相同的廊下无病呻吟。"
        )
        return "\n".join(lines)

    def format_worldline_memory_content(self, state: NarrativeState) -> str:
        phase = self.phase_for_year(state.world_year)
        lines = [
            f"世界线进度：{self._year_label(state.world_year)}（已发布约 {state.posts_published} 篇夜记）",
            f"阶段：{phase['name']}（{phase['id']}）",
            f"局势：{phase['pressure']}",
        ]
        if state.sister_in_residence is True:
            lines.append("关系状态：姐姐近期在府或刚回府。")
        elif state.sister_in_residence is False:
            lines.append("关系状态：姐姐仍在外行走。")
        if state.last_secret_order:
            lines.append(f"最近密令痕迹：{state.last_secret_order}")
        if state.wound_known is True:
            lines.append("旧伤：似已被旁人察觉。")
        elif state.wound_known is False:
            lines.append("旧伤：仍对王爷隐瞒。")
        if state.lord_warm_line:
            lines.append(f"王爷温度痕迹：{state.lord_warm_line}")
        if state.last_relation_tones:
            lines.append("近篇关系主音：" + " → ".join(state.last_relation_tones[-7:]))
        if state.last_scene_buckets:
            lines.append("近篇场景大类：" + " → ".join(state.last_scene_buckets[-7:]))
        return "\n".join(lines)

    def format_worldline_memory_summary(self, state: NarrativeState) -> str:
        phase = self.phase_for_year(state.world_year)
        return f"世界线·{self._year_label(state.world_year)}·{phase['name']}"

    @staticmethod
    def opening_fingerprint(content: str, limit: int = OPENING_FINGERPRINT_CHARS) -> str:
        body = NarrativePlanner._body_without_title(content)
        compact = re.sub(r"\s+", "", body)
        return compact[:limit]

    @staticmethod
    def opening_similarity(a: str, b: str) -> float:
        """Opening near-clone score; longest common prefix is primary signal."""
        if not a or not b:
            return 0.0
        window = min(len(a), len(b), 40)
        if window == 0:
            return 0.0
        prefix = 0
        for i in range(window):
            if a[i] == b[i]:
                prefix += 1
            else:
                break
        # Shared first 24+ chars of a 40-char window ≈ same scene opening.
        if prefix >= 24:
            return max(0.9, prefix / window)
        prefix_ratio = prefix / window
        same = sum(1 for i in range(window) if a[i] == b[i])
        seq = same / window
        sa, sb = set(a[:window]), set(b[:window])
        jaccard = len(sa & sb) / len(sa | sb) if sa and sb else 0.0
        return max(prefix_ratio, 0.6 * seq + 0.4 * jaccard)

    @staticmethod
    def _body_without_title(content: str) -> str:
        lines = content.splitlines()
        # Skip optional front matter
        if lines and lines[0].strip() == "---":
            for index, line in enumerate(lines[1:], start=1):
                if line.strip() == "---":
                    lines = lines[index + 1 :]
                    break
        # Skip leading blank + H1
        while lines and not lines[0].strip():
            lines = lines[1:]
        if lines and lines[0].lstrip().startswith("#"):
            lines = lines[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]
        return "\n".join(lines).strip()

    def _year_label(self, world_year: float) -> str:
        year = max(0.0, float(world_year))
        whole = int(year)
        frac = year - whole
        if frac < 0.25:
            season = "初"
        elif frac < 0.5:
            season = "仲"
        elif frac < 0.75:
            season = "季"
        else:
            season = "末"
        # Display as 第N年 (1-indexed for readers)
        return f"影中第{whole + 1}年{season}"

    def _relation_state_notes(self, state: NarrativeState, phase: dict[str, Any]) -> list[str]:
        notes: list[str] = []
        if state.sister_in_residence is True:
            notes.append("姐姐近期在府或刚回——写她须落到比较/误读/疼，禁止工具句。")
        elif state.sister_in_residence is False:
            notes.append("姐姐仍在外——可用一封信、一句传言、一件她留下的物件作回响。")
        if state.last_secret_order:
            notes.append(f"密令余波：{state.last_secret_order}")
        if state.wound_known is True:
            notes.append("旧伤已被察觉，勿再写成「首次发现」。")
        if state.lord_warm_line:
            notes.append(f"可感偏爱痕迹（你仍可能误读）：{state.lord_warm_line}")
        if not notes:
            notes.append(f"阶段基调：{phase['name']}")
        return notes

