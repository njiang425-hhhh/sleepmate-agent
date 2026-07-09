# SleepMate Agent — 项目规格设计 (Phase 0, v2)

## 项目定位

个人可用的 AI Agent 助眠助手 + 简历展示项目。

## MVP 功能范围

| 模块 | 功能 | 阶段 |
|------|------|------|
| 项目骨架 | Next.js + FastAPI + Docker Compose + health check | Phase 1 |
| Check-in | 睡前状态录入页面和 API | Phase 2 |
| 睡眠日志 | 睡眠数据 CRUD | Phase 3 |
| 评分与 Dashboard | 综合评分算法 + 可视化趋势图 | Phase 4 |
| 助眠计划 | LLM 生成个性化助眠计划 | Phase 5 |
| LangGraph Agent | 7 节点工作流 | Phase 6 |
| RAG 知识库 | Chroma 向量库 + 助眠知识检索 | Phase 7 |
| TTS 音频 | 文本转语音 + 白噪音播放 | Phase 8 |
| E2E 测试 | Playwright 核心路径覆盖 | Phase 9 |
| 部署 | 安全审查 + README + Docker 生产配置 | Phase 10 |

## Agent 工作流

Context Loader → Sleep State Analyzer → Decision Router → Tool Calling → Safety Guard → Response Generator → Memory Update

## 数据库表

- `user_preferences` — 用户偏好（单用户）
- `checkins` — 睡前状态记录
- `sleep_logs` — 睡眠日志
- `chat_messages` — 对话消息
- `sleep_plans` — 助眠计划
- `knowledge_docs` — 知识库文档

## 阶段计划

Phase 0 → Phase 1 → ... → Phase 10
