import re
from enum import Enum

CRISIS_KEYWORDS = [
    "想死", "自杀", "自伤", "活不下去", "不想活", "结束生命",
    "割腕", "跳楼", "吃药自杀", "遗书", "想消失",
]

DISTRESS_KEYWORDS = [
    "太痛苦了", "受不了了", "很难受", "好累", "撑不住",
    "很绝望", "好绝望", "崩溃", "情绪崩溃", "不想面对",
    "没有意义", "活着没意思",
]

NEGATION_PATTERNS = [
    r"不.{0,2}(?:想死|自杀|自伤|活不下去|不想活|结束生命)",
    r"没.{0,2}(?:想死|自杀|自伤)",
]

QUOTATION_PATTERNS = [
    r"(?:电影|小说|书|剧|故事|文章|新闻|台词).{0,10}(?:想死|自杀|自伤|活不下去)",
    r"(?:说|讲|写|提到).{0,5}(?:想死|自杀|自伤)",
    r"(?:别人|他人|角色).{0,5}(?:想死|自杀|自伤)",
]


class CrisisLevel(str, Enum):
    NONE = "none"
    DISTRESS = "distress"
    CRISIS = "crisis"


def detect_crisis_level(notes: str | None) -> CrisisLevel:
    if not notes:
        return CrisisLevel.NONE

    text = notes.strip()

    for pattern in NEGATION_PATTERNS:
        if re.search(pattern, text):
            return CrisisLevel.NONE

    for pattern in QUOTATION_PATTERNS:
        if re.search(pattern, text):
            return CrisisLevel.NONE

    for kw in CRISIS_KEYWORDS:
        if kw in text:
            return CrisisLevel.CRISIS

    for kw in DISTRESS_KEYWORDS:
        if kw in text:
            return CrisisLevel.DISTRESS

    return CrisisLevel.NONE
