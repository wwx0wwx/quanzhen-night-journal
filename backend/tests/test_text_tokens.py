from __future__ import annotations

from backend.utils.text_tokens import token_overlap_score, tokenize_for_search


def test_tokenize_chinese_uses_unigrams_and_bigrams():
    tokens = tokenize_for_search("廊柱旁的风贴着剑鞘过去")
    assert "廊" in tokens
    assert "廊柱" in tokens
    assert "剑鞘" in tokens


def test_tokenize_mixed_chinese_english():
    tokens = tokenize_for_search("机箱 fan 风声")
    assert "机箱" in tokens or "机" in tokens
    assert "fan" in tokens


def test_token_overlap_scores_chinese_without_spaces():
    query = "廊柱 剑鞘"
    document = "我靠在廊柱旁，手按剑鞘。"
    score = token_overlap_score(query, document)
    assert score > 0
