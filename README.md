# SleepMate Agent

个性化 AI 助眠助手 — 基于 LangGraph Agent + RAG + TTS 的助眠应用。

## 技术栈

- **Frontend**: Next.js + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python
- **Agent**: LangGraph
- **Database**: SQLite (Phase 3+)
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

## 测试

```bash
# 后端测试
cd backend && pytest -v

# 前端测试
cd frontend && npm test
```

## Docker

```bash
docker-compose up -d
```

## 项目结构

```
sleepmate-agent/
├── frontend/       # Next.js 前端
├── backend/        # FastAPI 后端
├── docs/           # 设计文档
├── scripts/        # 工具脚本
├── infra/          # 基础设施配置
└── docker-compose.yml
```

## 开发阶段

- [x] Phase 0: 项目规格设计
- [x] Phase 1: 项目骨架 + health check
- [ ] Phase 2: Check-in 页面和 API
- [ ] Phase 3: 睡眠日志数据库
- [ ] Phase 4: 睡眠评分和 Dashboard
- [ ] Phase 5: LLM 生成助眠计划
- [ ] Phase 6: LangGraph Agent 工作流
- [ ] Phase 7: RAG 知识库
- [ ] Phase 8: TTS 音频
- [ ] Phase 9: E2E 测试
- [ ] Phase 10: 安全审查、README、部署
