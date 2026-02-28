"""
《手持花洒评价图套组生成器 V3.2》
场景固定强化 + 显性锁定
"""
import random
from typing import Dict, List, Tuple

# 8选6 结构池（⑧永久禁止）
SHOT_TYPES = {
    "1": {"name_cn": "半身手持展示", "name_en": "Half-body handheld display", "water": True},  # 可出水
    "2": {"name_cn": "手部握持近景", "name_en": "Hand grip close-up", "water": False},
    "3": {"name_cn": "喷头结构特写", "name_en": "Spray head structure close-up", "water": False},
    "4": {"name_cn": "出水功能证明图", "name_en": "Water spray function proof", "water": True},  # 必须出现
    "5": {"name_cn": "挂架安装展示", "name_en": "Wall mount installation display", "water": False},
    "6": {"name_cn": "空间远景", "name_en": "Wide space shot", "water": False},  # 仅1张
    "7": {"name_cn": "台面静物补充图", "name_en": "Tabletop still life supplement", "water": False},
    "9": {"name_cn": "侧面轮廓比例展示", "name_en": "Side profile proportion display", "water": False},
}


def _pick_shot_types() -> List[str]:
    """8选6：④必出、①+④保证至少2张出水、⑥最多1张、不重复"""
    pool = ["1", "2", "3", "4", "5", "6", "7", "9"]
    water_types = [k for k, v in SHOT_TYPES.items() if v["water"]]  # ["1", "4"]

    selected = ["4", "1"]  # ④必出；①可出水，满足至少2张出水
    remaining = [t for t in pool if t not in selected]
    random.shuffle(remaining)

    for t in remaining:
        if len(selected) >= 6:
            break
        if t == "6" and any(s == "6" for s in selected):
            continue  # ⑥最多1张
        selected.append(t)

    return selected[:6]


# 主体产品描述（静态，各Shot一致）
PRODUCT_BODY_CN = (
    "增压花洒，喷头形态圆润，孔位排列整齐，黑色中心模块突出，"
    "手柄比例适中，按键位置清晰，材质质感哑光磨砂。"
)
PRODUCT_BODY_EN = (
    "Boost showerhead, rounded spray head, aligned nozzle layout, "
    "prominent black center module, proportionate handle, clear button position, matte texture."
)

# 摄影风格（固定）
PHOTO_STYLE_CN = "手机纪实，真实买家图，自然光，不棚拍，不广告感。"
PHOTO_STYLE_EN = "Phone documentary, real buyer shot, natural light, no studio, no ad feel."


def _ref_lock_section_cn() -> str:
    """Shot2–Shot7：主体产品结构与外观均锁定参考图A"""
    return """【参考图锁定】
- 主体产品结构：参考图A锁定（product）
- 主体产品外观：参考图A锁定（product）
- 场景与人物：参考图B锁定（scene + model）
- 出水形态：water参考图锁定（water）
"""


def _ref_lock_section_en() -> str:
    """Shot2–Shot7: product structure & appearance both RefA"""
    return """[Reference Lock]
- Product structure: RefA (product)
- Product appearance: RefA (product)
- Scene & person: RefB (scene + model)
- Water effect: water ref lock
"""


def _product_action_cn(shot_type: str, is_water: bool) -> str:
    if is_water:
        return (
            "手持花洒出水状态，水线细密，水压稳定，黑色中心模块出水明显，"
            "水束均匀连续，喷头45°侧向出水，不朝向人物面部。"
        )
    return "手持/静置展示，当前画面静态。"


def _product_action_en(shot_type: str, is_water: bool) -> str:
    if is_water:
        return (
            "Showerhead spraying, fine water streams, stable pressure, "
            "black center module water flow visible, uniform continuous spray, "
            "45° side angle, not toward face."
        )
    return "Hand-held or static display, current frame static."


def _camera_and_focus_cn(shot_type: str) -> tuple:
    m = {
        "1": ("半身中景，平视", "35mm，f/2.8"),
        "2": ("手部特写，略微俯拍", "50mm，f/2.0"),
        "3": ("喷头正面微距", "60mm macro，f/2.8"),
        "4": ("侧面中景，捕捉出水", "35mm，f/2.8"),
        "5": ("挂架安装俯拍", "28mm，f/4"),
        "6": ("空间远景，平视", "24mm，f/5.6"),
        "7": ("台面俯拍45°", "35mm，f/2.8"),
        "9": ("侧面轮廓平视", "50mm，f/2.8"),
    }
    return m.get(shot_type, ("中景平视", "35mm，f/2.8"))


def _camera_and_focus_en(shot_type: str) -> tuple:
    m = {
        "1": ("Half-body medium shot, eye level", "35mm, f/2.8"),
        "2": ("Hand close-up, slight high angle", "50mm, f/2.0"),
        "3": ("Spray head front macro", "60mm macro, f/2.8"),
        "4": ("Side medium shot, capture water", "35mm, f/2.8"),
        "5": ("Wall mount top-down", "28mm, f/4"),
        "6": ("Wide space shot, eye level", "24mm, f/5.6"),
        "7": ("Tabletop 45° angle", "35mm, f/2.8"),
        "9": ("Side profile eye level", "50mm, f/2.8"),
    }
    return m.get(shot_type, ("Medium eye level", "35mm, f/2.8"))


def build_v32_prompt_cn(
    shot_key: str,
    shot_type: str,
    role_map: Dict[str, List[str]],
    flags: Dict[str, bool],
) -> str:
    st = SHOT_TYPES.get(shot_type, SHOT_TYPES["1"])
    is_water = st["water"]
    cam, focus = _camera_and_focus_cn(shot_type)
    action = _product_action_cn(shot_type, is_water)

    return f"""{_ref_lock_section_cn()}产品动作：
{action}

主体产品：（参考图A锁定）
{PRODUCT_BODY_CN}

人物特征：（参考图B锁定）
人物姿态：
人物装饰与服饰：（参考图B锁定）
场景：（参考图B锁定）
场景装饰与道具：（参考图B锁定）
摄像机角度：
{cam}

焦距与光圈：
{focus}

灯光：
自然光，柔和漫反射。

摄影风格与品质：
{PHOTO_STYLE_CN}
"""


def build_v32_prompt_en(
    shot_key: str,
    shot_type: str,
    role_map: Dict[str, List[str]],
    flags: Dict[str, bool],
) -> str:
    st = SHOT_TYPES.get(shot_type, SHOT_TYPES["1"])
    is_water = st["water"]
    cam, focus = _camera_and_focus_en(shot_type)
    action = _product_action_en(shot_type, is_water)

    return f"""{_ref_lock_section_en()}Product action:
{action}

Main product: (RefA lock)
{PRODUCT_BODY_EN}

Person features: (RefB lock)
Pose:
Costume: (RefB lock)
Scene: (RefB lock)
Props: (RefB lock)
Camera angle:
{cam}

Focal length & aperture:
{focus}

Lighting:
Natural light, soft diffuse.

Style & quality:
{PHOTO_STYLE_EN}
"""


def build_shot2to7_prompts_v32(
    role_map: Dict[str, List[str]],
    flags: Dict[str, bool],
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """返回 (prompts_cn_dict, prompts_en_dict)"""
    types = _pick_shot_types()
    prompts_cn = {}
    prompts_en = {}
    for i, shot_type in enumerate(types):
        shot_key = f"shot{i + 2}"
        prompts_cn[shot_key] = build_v32_prompt_cn(shot_key, shot_type, role_map, flags)
        prompts_en[shot_key] = build_v32_prompt_en(shot_key, shot_type, role_map, flags)
    return prompts_cn, prompts_en
