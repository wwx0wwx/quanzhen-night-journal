"""Tests for night_journal.narrative.material_selector"""
from night_journal.narrative.material_selector import choose_world_material

IMAGERY = {
    'visual': ['灯芯', '纸窗', '檐影', '旧漆', '案角', '帐钩', '砚台'],
    'sound': ['更漏', '风压窗纸', '檐角滴水', '火星噼剥'],
    'smell': ['墨气', '冷铁味', '灯油气', '夜露气'],
    'touch': ['指腹发冷', '袖口微重', '砖面返潮'],
    'object_groups': {},
}

SCENES = {
    'indoor': ['床榻边缘', '案前', '屏风后'],
    'semi_outdoor': ['廊下', '门槛边'],
    'outer_yard': ['檐角', '院中'],
    'special': ['暗处', '帐外'],
}

EMOTIONS = {
    'primary': ['贪恋', '幽怨', '克制', '嫉妒', '不服', '空寂'],
    'secondary': ['羞', '惭', '倦', '慌', '失落', '警觉'],
    'pairing_hints': {
        '嫉妒': ['失落', '不服', '羞'],
        '贪恋': ['克制', '慌'],
    },
}

STATE = {
    'zhen': {'jealousy': 55, 'longing': 70, 'restraint': 65, 'emptiness': 50},
    'continuity': {'recent_imagery': [], 'recent_scenes': [], 'recent_emotions': []},
}

OVERRIDES = {}


def test_returns_four_values():
    result = choose_world_material(IMAGERY, SCENES, EMOTIONS, STATE, OVERRIDES, [])
    assert len(result) == 4


def test_chosen_imagery_is_list():
    imagery, scene, primary, secondary = choose_world_material(IMAGERY, SCENES, EMOTIONS, STATE, OVERRIDES, [])
    assert isinstance(imagery, list)
    assert len(imagery) > 0


def test_chosen_scene_is_string():
    _, scene, _, _ = choose_world_material(IMAGERY, SCENES, EMOTIONS, STATE, OVERRIDES, [])
    assert isinstance(scene, str)
    assert len(scene) > 0


def test_primary_in_emotion_pool():
    _, _, primary, _ = choose_world_material(IMAGERY, SCENES, EMOTIONS, STATE, OVERRIDES, [])
    assert primary in EMOTIONS['primary']


def test_secondary_is_string():
    _, _, _, secondary = choose_world_material(IMAGERY, SCENES, EMOTIONS, STATE, OVERRIDES, [])
    assert isinstance(secondary, str)


def test_force_scene_override():
    overrides = {'force_scene': '床榻边缘'}
    _, scene, _, _ = choose_world_material(IMAGERY, SCENES, EMOTIONS, STATE, overrides, [])
    assert scene == '床榻边缘'


def test_force_primary_emotion():
    overrides = {'force_primary_emotion': '嫉妒'}
    _, _, primary, _ = choose_world_material(IMAGERY, SCENES, EMOTIONS, STATE, overrides, [])
    assert primary == '嫉妒'


def test_repeated_phrases_avoidance():
    # With repeated phrases, imagery should still return results
    result = choose_world_material(IMAGERY, SCENES, EMOTIONS, STATE, OVERRIDES, ['灯', '剑'])
    imagery, _, _, _ = result
    assert isinstance(imagery, list)
