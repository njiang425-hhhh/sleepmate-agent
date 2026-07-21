# SleepMate Agent

个性化 AI 助眠助手 — 基于 LangGraph Agent + RAG + TTS 的助眠应用。

> **免责声明**：本应用仅供放松和助眠参考，不构成医疗建议、诊断或治疗方案。如有持续睡眠问题或心理健康困扰，请咨询专业医生或医疗机构。

## 技术栈

- **Frontend**: Next.js + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python
- **Agent**: LangGraph
- **Database**: SQLite + SQLAlchemy
- **RAG**: Chroma + OpenAI Embedding
- **TTS**: OpenAI TTS (gpt-4o-mini-tts) / FakeTTS

## 快速开始

```bash
# 复制环境变量
cp .env.example .env

# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

访问 http://localhost:3000

Check-in 页面: http://localhost:3000/checkin
Dashboard 页面: http://localhost:3000/dashboard
Routine 页面: http://localhost:3000/routine
API 文档: http://localhost:8000/docs

## 测试

```bash
# 后端测试 (242 tests)
cd backend && pytest -v

# 前端单元测试 (32 tests)
cd frontend && npm test

# E2E 测试 (8 tests)
cd frontend && npm run test:e2e
```

E2E 测试基于 Playwright + Chromium，全部 API 走 route mock，不依赖后端服务和外部 API。

## Docker

```bash
docker-compose up -d
```

## LLM 配置

```bash
# .env 中配置
LLM_MODE=mock      # mock: 不调用真实 API; real: 调用 OpenAI
OPENAI_API_KEY=     # real 模式必填
OPENAI_MODEL=gpt-4o-mini
LLM_TIMEOUT_SECONDS=30
```

mock 模式下无需 API key，测试和开发均可直接使用。

## TTS 音频配置

```bash
# .env 中配置
TTS_MODE=fake                         # fake: 测试用静音音频; real: 调用 OpenAI TTS
TTS_MODEL=gpt-4o-mini-tts             # OpenAI TTS 模型
TTS_VOICE=alloy                       # 语音风格: alloy/echo/fable/onyx/nova/shimmer
TTS_SPEED=0.9                         # 语速 (0.25-4.0)
TTS_RESPONSE_FORMAT=mp3               # 音频格式
TTS_INSTRUCTIONS=请用温柔、平静、缓慢的语气朗读  # 语音指令
TTS_TIMEOUT_SECONDS=60                # 超时时间
TTS_MAX_CHARS=4096                    # 最大文本长度
```

fake 模式下无需 API key，生成静音占位音频用于开发测试。
real 模式需要有效的 `OPENAI_API_KEY`，调用 OpenAI `gpt-4o-mini-tts` 生成真实语音。
相同文本 + 相同配置会缓存音频文件，避免重复调用 API。

## RAG 知识库配置

```bash
# .env 中配置
RAG_ENABLED=false                    # 启用 RAG 知识库检索
EMBEDDING_PROVIDER=fake              # fake: 测试用; openai: 使用 OpenAI embedding
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
CHROMA_PERSIST_DIR=chroma_db
CHROMA_COLLECTION_NAME=sleepmate_knowledge
KNOWLEDGE_BASE_DIR=data/knowledge_base
RAG_TOP_K=3
RAG_MAX_CONTEXT_TOKENS=1500
```

### 导入知识库

```bash
cd backend
python -m scripts.ingest_knowledge
```

### 查询知识库

```bash
cd backend
python -m scripts.query_knowledge "高压力放松呼吸"
```

## 项目结构

```
sleepmate-agent/
├── frontend/
│   ├── e2e/
│   │   ├── fixtures/
│   │   │   ├── mock-data.ts
│   │   │   └── mock-api.ts
│   │   ├── full-flow.spec.ts
│   │   └── tts.spec.ts
│   ├── playwright.config.ts
│   └── src/
│       ├── app/
│       │   ├── checkin/
│       │   ├── dashboard/
│       │   └── routine/
│       │       └── components/
│       │           ├── AudioPlayer.tsx
│       │           └── RoutineCard.tsx
│       ├── types/
│       │   ├── checkin.ts
│       │   └── routine.ts
│       └── lib/
│           ├── routine-api.ts
│           └── audio-api.ts
├── backend/
│   ├── data/
│   │   └── knowledge_base/
│   │       ├── sleep_hygiene.md
│   │       ├── breathing_exercises.md
│   │       ├── mindfulness_scripts.md
│   │       └── relaxation_templates.md
│   ├── scripts/
│   │   ├── ingest_knowledge.py
│   │   └── query_knowledge.py
│   ├── static/
│   │   └── audio/
│   │       └── .gitkeep
│   └── app/
│       ├── api/
│       │   ├── health.py
│       │   ├── checkin.py
│       │   ├── sleep_log.py
│       │   ├── dashboard.py
│       │   ├── routine.py
│       │   └── audio.py
│       ├── agents/
│       │   ├── state.py
│       │   ├── runtime.py
│       │   ├── graph.py
│       │   ├── nodes.py
│       │   └── domain/
│       │       ├── crisis_detector.py
│       │       ├── safety_validator.py
│       │       └── history_analyzer.py
│       ├── core/
│       │   ├── config.py
│       │   └── database.py
│       ├── models/
│       │   └── sleep_log.py
│       ├── schemas/
│       │   ├── checkin.py
│       │   ├── sleep_log.py
│       │   ├── dashboard.py
│       │   ├── knowledge.py
│       │   ├── routine.py
│       │   └── audio.py
│       ├── repositories/
│       │   └── sleep_log_repo.py
│       └── services/
│           ├── checkin_service.py
│           ├── sleep_log_service.py
│           ├── sleep_score_service.py
│           ├── dashboard_service.py
│           ├── llm_provider.py
│           ├── llm_service.py
│           ├── routine_service.py
│           ├── safety_resources.py
│           ├── embedding_provider.py
│           ├── embedding_service.py
│           ├── rag_service.py
│           ├── tts_provider.py
│           ├── tts_service.py
│           └── audio_storage.py
│   └── tests/
│       ├── conftest.py
│       ├── test_health.py
│       ├── test_checkin.py
│       ├── test_sleep_log.py
│       ├── test_sleep_score.py
│       ├── test_dashboard.py
│       ├── test_routine.py
│       ├── test_graph.py
│       ├── test_embedding_provider.py
│       ├── test_rag_service.py
│       ├── test_ingest_knowledge.py
│       ├── test_knowledge_node.py
│       └── test_tts.py
├── docs/
├── scripts/
├── infra/
└── docker-compose.yml
```

## 开发阶段

- [x] Phase 0: 项目规格设计
- [x] Phase 1: 项目骨架 + health check
- [x] Phase 2: Check-in 页面和 API
- [x] Phase 3: 睡眠日志数据库
- [x] Phase 4: 睡眠评分和 Dashboard
- [x] Phase 5: LLM 生成助眠计划
- [x] Phase 6: LangGraph Agent 工作流
- [x] Phase 7: RAG 知识库 — Chroma 向量存储 + OpenAI Embedding + 睡眠知识文档。Agent 新增 retrieve_sleep_knowledge_node，从知识库检索相关内容辅助生成助眠计划。支持优雅降级，RAG 不可用时不影响核心功能。222 测试全部通过。
- [x] Phase 8: TTS 音频 — 按需生成语音引导，支持 Fake/Real 模式，SHA256 缓存，原子写入，242 后端测试 + 32 前端测试全部通过。
- [x] Phase 9: E2E 测试 — Playwright 8 条用例：完整用户流程 + TTS 生成/降级/防抖，全部 API route mock
- [ ] Phase 10: 安全审查、README、部署
