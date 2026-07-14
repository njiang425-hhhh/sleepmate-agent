# SleepMate Agent

个性化 AI 助眠助手 — 基于 LangGraph Agent + RAG + TTS 的助眠应用。

## 技术栈

- **Frontend**: Next.js + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python
- **Agent**: LangGraph
- **Database**: SQLite + SQLAlchemy
- **RAG**: Chroma (Phase 7+)
- **TTS**: (Phase 8+)

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
API 文档: http://localhost:8000/docs

## 测试

```bash
# 后端测试 (181 tests)
cd backend && pytest -v

# 前端测试 (19 tests)
cd frontend && npm test
```

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

## 项目结构

```
sleepmate-agent/
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── checkin/
│       │   ├── dashboard/
│       │   └── routine/
│       ├── types/
│       │   ├── checkin.ts
│       │   └── routine.ts
│       └── lib/
│           └── routine-api.ts
├── backend/
│   └── app/
│       ├── api/
│       │   ├── health.py
│       │   ├── checkin.py
│       │   ├── sleep_log.py
│       │   ├── dashboard.py
│       │   └── routine.py
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
│       │   └── routine.py
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
│           └── safety_resources.py
│   └── tests/
│       ├── test_health.py
│       ├── test_checkin.py
│       ├── test_sleep_log.py
│       ├── test_sleep_score.py
│       ├── test_dashboard.py
│       ├── test_routine.py
│       └── test_graph.py
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
- [x] Phase 6: LangGraph Agent 工作流 — 使用 LangGraph 重构助眠计划生成，包含安全分析、条件分流、历史读取、计划生成、安全校验、重试/fallback 和响应组装。crisis/distress 路径不调用 LLM。默认使用 mock 模式。
- [ ] Phase 7: RAG 知识库
- [ ] Phase 8: TTS 音频
- [ ] Phase 9: E2E 测试
- [ ] Phase 10: 安全审查、README、部署
