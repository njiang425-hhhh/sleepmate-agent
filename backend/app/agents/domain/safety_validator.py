from app.schemas.routine import SleepRoutine

MEDICAL_TERMS = [
    "诊断", "疾病", "治疗", "处方", "药物", "药方",
    "失眠症", "抑郁症", "焦虑症", "睡眠障碍",
]

DRUG_TERMS = [
    "褪黑素", "安眠药", "阿普唑仑", "佐匹克隆", "地西泮",
    "助眠药", "镇静剂", "抗组胺", "苯二氮卓",
]


def _text_contains_terms(text: str, terms: list[str]) -> bool:
    for term in terms:
        if term in text:
            return True
    return False


def validate_routine(routine: SleepRoutine) -> bool:
    fields_to_check = [routine.strategy, routine.script]
    for step in routine.steps:
        fields_to_check.append(step.instruction)

    for text in fields_to_check:
        if _text_contains_terms(text, MEDICAL_TERMS + DRUG_TERMS):
            return False
    return True
