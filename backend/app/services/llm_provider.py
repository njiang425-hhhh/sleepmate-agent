from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from app.schemas.routine import RoutineStep, SleepRoutine


class RoutineGenerationContext(BaseModel):
    mood: str
    energy_level: int
    stress_level: int
    caffeine_after_3pm: bool
    screen_time_minutes: int
    available_minutes: int
    preferred_audio: str
    notes: str | None
    history_available: bool
    avg_latency: float | None = None
    avg_awakenings: float | None = None
    avg_quality: float | None = None
    avg_stress: float | None = None
    avg_screen: float | None = None
    record_count: int = 0


class ProviderError(Exception):
    pass


class ProviderTimeoutError(ProviderError):
    pass


class ProviderRefusedError(ProviderError):
    pass


class ProviderParseError(ProviderError):
    pass


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, ctx: RoutineGenerationContext) -> SleepRoutine:
        ...


MOCK_ROUTINES: dict[str, SleepRoutine] = {
    "high_stress": SleepRoutine(
        title="高压力呼吸引导放松",
        duration_minutes=15,
        strategy="针对高压力状态的呼吸引导，通过深度呼吸和渐进式放松帮助降低压力水平",
        steps=[
            RoutineStep(order=1, action="准备就位", duration_seconds=60,
                        instruction="找一个安静舒适的地方坐下或躺下，轻轻闭上眼睛，将双手自然放在身体两侧。"),
            RoutineStep(order=2, action="深呼吸练习", duration_seconds=300,
                        instruction='用鼻子缓慢吸气4秒，感受腹部隆起；屏息4秒；用嘴缓慢呼气6秒。重复8-10次，每次呼气时默念"放松"。'),
            RoutineStep(order=3, action="渐进式肌肉放松", duration_seconds=300,
                        instruction="从脚趾开始，依次收紧再放松身体各部位肌肉：脚趾、小腿、大腿、腹部、双手、手臂、肩膀、面部。每个部位保持紧张5秒，然后彻底放松。"),
            RoutineStep(order=4, action="平静收尾", duration_seconds=240,
                        instruction="保持自然呼吸，想象自己置身于一个宁静的地方。感受身体的沉重和温暖，让睡意自然降临。"),
        ],
        script="现在让我们一起开始放松之旅。首先，找一个舒适的姿势坐好或躺下，轻轻闭上眼睛。让我们从深呼吸开始。用鼻子慢慢吸气，一、二、三、四，感受腹部的起伏。屏住呼吸，一、二、三、四。然后用嘴慢慢呼气，一、二、三、四、五、六，让所有的紧张随呼气流出。非常好，我们再来几次。吸气...屏息...呼气...现在，让我们开始渐进式肌肉放松。先收紧你的脚趾，保持5秒...然后彻底放松。接下来是小腿，收紧...放松。大腿...收紧...放松。继续向上，腹部、双手、手臂、肩膀...最后是面部，轻轻皱眉...然后完全放松。现在你的身体已经很放松了，让呼吸自然流动，感受这份宁静。",
    ),
    "anxious": SleepRoutine(
        title="焦虑缓解冥想计划",
        duration_minutes=15,
        strategy="通过正念冥想和身体扫描技术，缓解焦虑情绪，引导身心进入平静状态",
        steps=[
            RoutineStep(order=1, action=" grounding 练习", duration_seconds=120,
                        instruction="双脚平放在地面，感受脚底与地面的接触。环顾四周，说出你能看到的5样东西、4种声音、3种触感。"),
            RoutineStep(order=2, action="正念呼吸", duration_seconds=300,
                        instruction='将注意力集中在呼吸上，不做任何改变，只是观察。吸气时默念"吸"，呼气时默念"呼"。思绪飘走时轻轻拉回。'),
            RoutineStep(order=3, action="身体扫描", duration_seconds=420,
                        instruction="从头顶开始，缓慢将注意力移向脚底。注意每个部位的感觉，不做判断，只是觉察。遇到紧张的部位，想象温暖的光芒包裹它。"),
            RoutineStep(order=4, action="安心收尾", duration_seconds=180,
                        instruction='将注意力回到呼吸，对自己说"我现在是安全的"。慢慢睁开眼睛。'),
        ],
        script='欢迎来到这个专属于你的宁静时刻。现在，让我们一起回到当下。看看你的周围，说出你能看到的5样东西...很好。听听周围的声音，4种不同的声音...感受你身体的3种触感...现在，你已经回到了当下。让我们把注意力放在呼吸上。不需要改变什么，只是观察。吸气，默念"吸"...呼气，默念"呼"。如果思绪飘走了，没关系，轻轻地把注意力拉回来。现在，让我们做一次身体扫描。把注意力放在头顶...感受那里的感觉...慢慢向下移动...额头...眼睛...脸颊...下巴...脖子...肩膀...让注意力像温暖的水流一样，缓缓流过全身。你现在是安全的，一切都会好起来的。',
    ),
    "high_energy": SleepRoutine(
        title="能量释放拉伸计划",
        duration_minutes=10,
        strategy="通过轻度拉伸运动释放多余能量，帮助身体从活跃状态过渡到放松状态",
        steps=[
            RoutineStep(order=1, action="颈部拉伸", duration_seconds=120,
                        instruction="缓慢将头向左倾斜，保持15秒，然后回到中间。再向右倾斜，保持15秒。重复3次。"),
            RoutineStep(order=2, action="肩部放松", duration_seconds=120,
                        instruction="双肩向上耸起靠近耳朵，保持5秒，然后突然放下。重复5次，感受肩膀的放松。"),
            RoutineStep(order=3, action="全身拉伸", duration_seconds=180,
                        instruction="坐在床边，双脚平放地面。慢慢弯腰，让双手自然下垂触碰脚尖，保持20秒。然后慢慢起身。"),
            RoutineStep(order=4, action="呼吸调整", duration_seconds=180,
                        instruction='躺下后做5次深呼吸，每次呼气时默念"放松"，让身体逐渐沉重。'),
        ],
        script='看来你今晚精力充沛呢。让我们先做一些轻柔的拉伸来释放这些能量。首先，慢慢把头向左倾斜...感受右侧颈部的拉伸...回到中间...再向右倾斜...非常好。现在，让我们放松肩膀。向上耸肩...保持...然后突然放下，让肩膀自然下沉。感觉好多了吧。最后，坐在床边，慢慢弯腰，让双手自然下垂...保持这个姿势...然后慢慢起身。现在躺下来，做几次深呼吸。吸气...呼气，默念"放松"...很好，让身体慢慢沉入床垫。',
    ),
    "default": SleepRoutine(
        title="平静入睡放松计划",
        duration_minutes=10,
        strategy="通用的睡前放松计划，通过呼吸引导和身体放松帮助顺利入睡",
        steps=[
            RoutineStep(order=1, action="准备就位", duration_seconds=60,
                        instruction="躺好后调整到最舒适的姿势，轻轻闭上眼睛。将一只手放在胸口，一只手放在腹部。"),
            RoutineStep(order=2, action="腹式呼吸", duration_seconds=300,
                        instruction="用鼻子吸气4秒，感受腹部的手上升；用嘴呼气6秒，感受腹部的手下降。重复8次。"),
            RoutineStep(order=3, action="想象放松", duration_seconds=180,
                        instruction="想象自己躺在温暖的沙滩上，海浪轻柔地拍打岸边，阳光温暖地照在身上。让这个画面越来越清晰。"),
            RoutineStep(order=4, action="自然入睡", duration_seconds=60,
                        instruction="保持自然呼吸，让睡意自然降临，不需要刻意做什么。"),
        ],
        script="现在是时候休息了。找到你最舒适的睡姿，闭上眼睛。把一只手轻轻放在胸口，另一只手放在腹部。让我们开始腹式呼吸。用鼻子慢慢吸气...一、二、三、四，感受腹部慢慢鼓起。用嘴慢慢呼气...一、二、三、四、五、六，感受腹部慢慢收回。非常好，我们再来几次。吸气...呼气...现在，想象自己躺在一片温暖的沙滩上。你能感受到细沙的温度，听到海浪轻柔的声音，闻到清新的海风。阳光温柔地照在你身上，一切都那么宁静美好。让这份宁静伴随你进入梦乡。晚安。",
    ),
}


class MockLLMProvider(LLMProvider):
    def generate(self, ctx: RoutineGenerationContext) -> SleepRoutine:
        if ctx.stress_level >= 7 or ctx.mood == "stressed":
            return MOCK_ROUTINES["high_stress"]
        if ctx.mood == "anxious":
            return MOCK_ROUTINES["anxious"]
        if ctx.energy_level >= 8:
            return MOCK_ROUTINES["high_energy"]
        return MOCK_ROUTINES["default"]
