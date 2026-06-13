from __future__ import annotations

import re

_SPACE_RE = re.compile(r"\s+")
_COMPACT_RE = re.compile(r"[^0-9A-Za-z\u4e00-\u9fff]+")

MOTIF_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("王府", ("王府", "府中", "府邸", "内院", "庭院")),
    ("书房", ("书房", "书案", "卷宗", "密室", "藏书阁")),
    ("长廊", ("长廊", "廊下", "走廊", "廊柱", "檐下")),
    ("马事", ("马厩", "马背", "马鞍", "鞍", "缰绳", "马蹄")),
    ("赶路", ("赶路", "连夜", "归途", "回府", "出远门", "山道", "驿路")),
    ("渡口", ("渡口", "码头", "江风", "舟", "船", "水面")),
    ("客栈", ("客栈", "驿站", "破庙", "借宿")),
    ("药事", ("药铺", "伤药", "药碗", "药味", "煎药")),
    ("铁匠铺", ("铁匠", "武器铺", "暗器", "刀鞘", "剑鞘")),
    ("集市", ("集市", "小镇", "街巷", "茶楼", "酒馆", "灯会", "庙会")),
    ("密令", ("密令", "暗线", "探子", "线报", "伏击", "截杀")),
    ("练剑", ("练剑", "剑势", "剑锋", "剑柄", "按剑", "刀背")),
    ("守夜", ("守夜", "守着", "门外", "不眠", "彻夜")),
    ("照料", ("照料", "受伤", "旧伤", "包扎", "病中")),
    ("送别", ("送别", "送行", "远行", "接归", "归来")),
    ("姐姐", ("姐姐", "她替", "她在外")),
    ("王爷", ("王爷", "主人")),
    ("霜雪", ("雪", "霜", "寒夜", "冬", "冰")),
    ("风雨", ("雨", "急雨", "暴雨", "春雨", "风声", "大风")),
    ("灯影", ("灯", "灯影", "灯火", "灯花", "檐灯")),
    ("拂晓", ("拂晓", "清晨", "天未亮", "天亮前")),
    ("黄昏", ("黄昏", "傍晚", "暮色")),
    ("深夜", ("深夜", "半夜", "子时", "丑时", "入夜")),
)


def body_text(content: str) -> str:
    lines = (content or "").splitlines()
    first = next((index for index, line in enumerate(lines) if line.strip()), None)
    if first is not None and lines[first].strip() == "---":
        for index in range(first + 1, len(lines)):
            if lines[index].strip() == "---":
                lines = lines[index + 1 :]
                break
    return "\n".join(line for line in lines if not line.lstrip().startswith("#"))


def compact_text(text: str) -> str:
    return _COMPACT_RE.sub("", text or "").casefold()


def extract_opening(content: str, *, limit: int = 120) -> str:
    return _excerpt(_body_plain(content), limit=limit)


def extract_ending(content: str, *, limit: int = 100) -> str:
    text = _body_plain(content)
    if limit <= 0 or len(text) <= limit:
        return text
    return text[-limit:].strip()


def extract_motifs(content: str, *, title: str = "", limit: int = 12) -> list[str]:
    source = f"{title}\n{content}"
    motifs: list[str] = []
    for label, keywords in MOTIF_RULES:
        if any(keyword and keyword in source for keyword in keywords):
            motifs.append(label)
        if len(motifs) >= limit:
            break
    return motifs


def shared_ngram(left: str, right: str, *, min_length: int = 18, max_length: int = 36) -> str:
    left_norm = compact_text(left)
    right_norm = compact_text(right)
    max_size = min(max_length, len(left_norm), len(right_norm))
    if max_size < min_length:
        return ""

    for size in range(max_size, min_length - 1, -1):
        seen = {
            left_norm[index : index + size]
            for index in range(0, len(left_norm) - size + 1)
            if _is_informative(left_norm[index : index + size])
        }
        if not seen:
            continue
        for index in range(0, len(right_norm) - size + 1):
            token = right_norm[index : index + size]
            if token in seen and _is_informative(token):
                return token
    return ""


def _body_plain(content: str) -> str:
    lines = [line.strip() for line in body_text(content).splitlines() if line.strip()]
    return _SPACE_RE.sub(" ", " ".join(lines)).strip()


def _excerpt(text: str, *, limit: int) -> str:
    if limit <= 0 or len(text) <= limit:
        return text
    return text[:limit].strip()


def _is_informative(token: str) -> bool:
    if len(set(token)) < min(5, max(1, len(token) // 3)):
        return False
    return any("\u4e00" <= char <= "\u9fff" or char.isalpha() for char in token)
