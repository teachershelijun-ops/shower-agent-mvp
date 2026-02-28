"""
Shower Agent MVP - FastAPI Backend (Session Locked Version)
"""
import os
import re
import uuid
import json
from pathlib import Path
from typing import Dict, List, Tuple

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from prompt_v32 import build_shot2to7_prompts_v32

app = FastAPI(title="Shower Agent MVP API")

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Upload Folder
# =========================
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# =========================
# Skill Library Loader
# =========================
SKILL_PATH = (Path(__file__).resolve().parent.parent /
              "ShowerSkillLibrary_v1.0.json").resolve()

SKILL_LIB = {"version": "1.0", "skills": []}

def load_skill_lib():
    global SKILL_LIB
    if SKILL_PATH.exists():
        try:
            with open(SKILL_PATH, "r", encoding="utf-8") as f:
                SKILL_LIB = json.load(f)
        except Exception as e:
            print(f"[SkillLibrary] Failed to load: {e}")
            SKILL_LIB = {"version": "1.0", "skills": []}

load_skill_lib()

def get_skill(skill_key: str):
    for s in SKILL_LIB.get("skills", []):
        if s.get("type") == skill_key or s.get("id") == skill_key:
            return s
    return None

# =========================
# Session Storage (In-Memory)
# =========================
SESSIONS = {}
# session_id -> {
#   file_urls: [],
#   shot1_confirmed: bool
# }

# =========================
# Response Models
# =========================
class UploadResponse(BaseModel):
    success: bool
    session_id: str
    file_urls: List[str]
    message: str = ""


class GenerateShot1Response(BaseModel):
    success: bool
    image_url: str


class GenerateShot2to7Response(BaseModel):
    success: bool
    image_urls: List[str]
    prompts_cn: Dict[str, str]  # {"shot2": "...", ..., "shot7": "..."}
    prompts_en: Dict[str, str]
    skill_used: str
    role_map: Dict[str, List[str]] = {}
    images_used: List[str] = []
    select_mode: str = "S1"


class ConfirmShot1Response(BaseModel):
    success: bool
    message: str


class ReloadSkillResponse(BaseModel):
    success: bool
    count: int
    path: str


# =========================
# Helpers
# =========================
MOCK_SHOT1_URL = "https://placehold.co/400x300/1a1a2e/eee?text=Shot1+Anchor"
MOCK_SHOT2_7_URLS = [
    "https://placehold.co/400x300/16213e/eee?text=Shot2",
    "https://placehold.co/400x300/0f3460/eee?text=Shot3",
    "https://placehold.co/400x300/533483/eee?text=Shot4",
    "https://placehold.co/400x300/e94560/eee?text=Shot5",
    "https://placehold.co/400x300/1a1a2e/eee?text=Shot6",
    "https://placehold.co/400x300/16213e/eee?text=Shot7",
]

ROLE_RE = re.compile(r"^(?P<role>[a-z_]+)__(?P<idx>\d+)__")


def parse_role_from_url(url: str) -> Tuple[str, int]:
    name = os.path.basename(url)
    m = ROLE_RE.match(name)
    if not m:
        return ("unknown", 9999)
    return (m.group("role"), int(m.group("idx")))


def build_role_map(file_urls: List[str]) -> Dict[str, List[str]]:
    tmp: Dict[str, List[Tuple[int, str]]] = {}
    for u in file_urls:
        role, idx = parse_role_from_url(u)
        tmp.setdefault(role, []).append((idx, u))
    return {
        role: [u for _, u in sorted(items, key=lambda x: x[0])]
        for role, items in tmp.items()
    }


def select_images(
    role_map: dict, flags: dict, mode: str = "S1"
) -> List[str]:
    def first(role: str):
        arr = role_map.get(role, [])
        return arr[0] if arr else None

    if mode == "S2":
        roles = ["product", "scene", "model", "water", "travel_bag", "filter_core"]
        out = []
        for r in roles:
            out.extend(role_map.get(r, []))
        return out

    out = []
    for r in ["product", "scene", "water"]:
        u = first(r)
        if u:
            out.append(u)
    m = first("model")
    if m:
        out.append(m)
    if flags.get("travelFilter"):
        t = first("travel_bag")
        if t:
            out.append(t)
    if flags.get("filter"):
        f = first("filter_core")
        if f:
            out.append(f)
    return out


def pick_shot_prompt(skill: dict, shot_no: int):
    cn, en = "", ""
    shots = skill.get("shots", {})
    key = f"shot{shot_no}"

    if isinstance(shots, dict) and key in shots:
        cn = shots[key].get("cn", "")
        en = shots[key].get("en", "")

    if not cn:
        cn = f"（待配置）Shot{shot_no} 中文提示词"
    if not en:
        en = f"(TODO) Shot{shot_no} English prompt"

    return cn, en


def require_session(session_id: str):
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session 不存在，请重新上传图片")
    return SESSIONS[session_id]


# =========================
# API Endpoints
# =========================

@app.post("/api/reload_skills", response_model=ReloadSkillResponse)
async def reload_skills():
    load_skill_lib()
    return ReloadSkillResponse(
        success=True,
        count=len(SKILL_LIB.get("skills", [])),
        path=str(SKILL_PATH)
    )


@app.post("/api/upload", response_model=UploadResponse)
async def upload_images(files: List[UploadFile] = File(...)):
    session_id = uuid.uuid4().hex[:12]

    IMAGE_EXT = {"jpg", "jpeg", "png", "gif", "webp", "bmp", "heic"}
    saved_paths = []
    for f in files:
        ext = (f.filename or "").split(".")[-1].lower() if f.filename else ""
        is_image = (f.content_type and f.content_type.startswith("image/")) or (ext in IMAGE_EXT)
        if not is_image:
            continue

        ext = ext or "jpg"
        orig = (f.filename or "").strip()
        if ROLE_RE.match(os.path.basename(orig)):
            prefix = orig.rsplit(".", 1)[0] if "." in orig else orig
            safe = "".join(c for c in prefix[:80] if c.isalnum() or c in "._-")
            name = f"{safe}.{ext}" if safe else f"{uuid.uuid4().hex[:10]}.{ext}"
        else:
            name = f"{uuid.uuid4().hex[:10]}.{ext}"
        name = name or f"{uuid.uuid4().hex[:10]}.{ext}"
        path = UPLOAD_DIR / name

        content = await f.read()
        path.write_bytes(content)

        saved_paths.append(f"/uploads/{name}")

    if len(saved_paths) == 0:
        raise HTTPException(status_code=400, detail="未上传有效图片")

    # 创建 session
    SESSIONS[session_id] = {
        "file_urls": saved_paths,
        "shot1_confirmed": False,
    }

    return UploadResponse(
        success=True,
        session_id=session_id,
        file_urls=saved_paths,
        message=f"上传成功，创建 session={session_id}"
    )


@app.post("/api/generate/shot1", response_model=GenerateShot1Response)
async def generate_shot1(session_id: str = Form(...)):
    session = require_session(session_id)

    # mock anchor
    return GenerateShot1Response(success=True, image_url=MOCK_SHOT1_URL)


@app.post("/api/confirm/shot1", response_model=ConfirmShot1Response)
async def confirm_shot1(session_id: str = Form(...)):
    session = require_session(session_id)

    session["shot1_confirmed"] = True

    return ConfirmShot1Response(success=True, message="Shot1 锚点已确认")


@app.post("/api/generate/shot2to7", response_model=GenerateShot2to7Response)
async def generate_shot2to7(
    session_id: str = Form(...),
    skill_type: str = Form("Boost")
):
    session = require_session(session_id)

    if not session["shot1_confirmed"]:
        raise HTTPException(status_code=400, detail="Shot1 未确认，禁止生成 Shot2–7")

    skill = get_skill(skill_type) or {}

    # Role map & select images
    file_urls = session.get("file_urls") or []
    role_map = build_role_map(file_urls)
    flags = session.get("flags") or {}
    if not flags:
        flags = {
            "travelFilter": skill_type == "TravelFilter",
            "filter": skill_type == "Filter",
        }

    # V3.2 执行级 Prompt（10段式 + 参考图锁定）
    prompts_cn, prompts_en = build_shot2to7_prompts_v32(role_map, flags)
    select_mode = "S1"
    images_used = select_images(role_map, flags, mode=select_mode)

    use_real_model = os.environ.get("USE_REAL_MODEL", "0") == "1"
    if use_real_model:
        # TODO: call_model(images_used, prompts_cn, prompts_en, ...)
        pass

    session["prompts_cn"] = prompts_cn
    session["prompts_en"] = prompts_en
    session["image_urls"] = MOCK_SHOT2_7_URLS

    return GenerateShot2to7Response(
        success=True,
        image_urls=MOCK_SHOT2_7_URLS,
        prompts_cn=prompts_cn,
        prompts_en=prompts_en,
        skill_used=skill_type,
        role_map=role_map,
        images_used=images_used,
        select_mode=select_mode,
    )


# =========================
# Modify Shot (mock)
# =========================
class ModifyShotRequest(BaseModel):
    session_id: str
    shot: str
    instruction: str | None = None
    edited_cn: str | None = None
    edited_en: str | None = None


class ModifyShotResponse(BaseModel):
    prompt_cn: str
    prompt_en: str
    image_url: str
    skill_used: List[str] | None = None


@app.post("/api/modify/shot", response_model=ModifyShotResponse)
async def modify_shot(req: ModifyShotRequest):
    session = require_session(req.session_id)
    shot_id = req.shot.strip().lower()
    if not shot_id.startswith("shot") or shot_id not in [f"shot{i}" for i in range(2, 8)]:
        raise HTTPException(status_code=400, detail="shot 必须是 shot2..shot7")

    idx = int(shot_id.replace("shot", ""))
    shot_index = idx - 2  # 0..5
    prompts_cn = session.get("prompts_cn") or {}
    prompts_en = session.get("prompts_en") or {}
    # 兼容 list/dict
    def get_prompt(prompts, i):
        key = f"shot{i + 2}"
        if isinstance(prompts, dict):
            return prompts.get(key, "")
        return prompts[i] if i < len(prompts) else ""

    prompt_cn = req.edited_cn or get_prompt(prompts_cn, shot_index) or "（待配置）"
    prompt_en = req.edited_en or get_prompt(prompts_en, shot_index) or "(TODO)"

    image_urls = session.get("image_urls") or MOCK_SHOT2_7_URLS
    image_url = image_urls[shot_index] if shot_index < len(image_urls) else MOCK_SHOT2_7_URLS[shot_index]

    modified = session.setdefault("modified_shots", {})
    modified[shot_id] = {"prompt_cn": prompt_cn, "prompt_en": prompt_en, "image_url": image_url}

    return ModifyShotResponse(
        prompt_cn=prompt_cn,
        prompt_en=prompt_en,
        image_url=image_url,
        skill_used=None,
    )


@app.post("/api/generate/shot/{shot_index}", response_model=GenerateShot1Response)
async def regenerate_shot(
    shot_index: int,
    session_id: str = Form(...)
):
    session = require_session(session_id)

    if shot_index == 1:
        return GenerateShot1Response(success=True, image_url=MOCK_SHOT1_URL)

    if 2 <= shot_index <= 7:
        return GenerateShot1Response(
            success=True,
            image_url=MOCK_SHOT2_7_URLS[shot_index - 2]
        )

    raise HTTPException(status_code=400, detail="shot_index 必须在 1–7")
