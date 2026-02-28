# Shower Agent MVP

目标：上传图片 → 生成Shot1(模板锚点) → 确认 → 生成Shot2-7(6张交付图)

## 运行步骤

### 1. 启动后端（终端一）

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

后端地址：http://localhost:8000

### 2. 启动前端（终端二）

```bash
cd frontend
npm install
npm run dev
```

前端地址：http://localhost:3000

### 3. 使用流程

1. 选择多张图片并点击「上传」
2. 选择花洒类型（Boost / LargePanel / Filter / TravelFilter / Descale）
3. 点击「生成 Shot1」→ 点击「确认 Shot1 锚点」→ 点击「生成 Shot2-7」
4. 每张卡片支持「重新生成」

## 项目结构

```
shower-agent-mvp/
├── backend/           # FastAPI
│   ├── main.py
│   ├── requirements.txt
│   └── uploads/       # 上传图片存储
├── frontend/          # Next.js (TypeScript)
│   ├── app/
│   ├── lib/
│   └── public/mock/   # 可放本地 mock 图
├── shared/            # 共享逻辑
│   └── prompt_builder.ts  # PromptBuilder 占位
└── README.md
```

## API 说明

| 接口 | 说明 |
|------|------|
| POST /api/upload | 接收多张图片，存到 uploads/ |
| POST /api/generate/shot1 | 返回 mock Shot1 图片 URL |
| POST /api/generate/shot2to7 | 返回 6 个 mock Shot2-7 图片 URL |
| POST /api/confirm/shot1 | 确认 Shot1 锚点 |

当前使用 placehold.co 占位图，可将 mock 图放入 `frontend/public/mock/` 后修改后端返回对应路径。
