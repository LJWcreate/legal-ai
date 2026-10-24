# LegalAI 法律智能助手

RAG + Agent 法律 AI 应用：法律问答（带法条引用）与合同风险审查（结构化报告）。

技术栈：FastAPI + Vue 3 + PostgreSQL(pgvector) + DeepSeek API。详细设计见 `docs/设计文档.md`。

## 快速开始（本地开发）

### 1. 启动数据库

```bash
docker compose up -d db
```

### 2. 配置后端

```bash
cd backend
cp .env.example .env        # 填入 DeepSeek / embedding 的 API Key
python -m venv .venv && .venv/Scripts/activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

接口文档：<http://localhost:8000/docs>

### 3. 导入法条知识库

```bash
python scripts/ingest_laws.py data/laws.jsonl
```

JSONL 格式见脚本文件头注释。法条文本需自行从公开渠道整理，逐条核对文号与生效日期。

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev    # http://localhost:5173
```

## 生产部署

```bash
docker compose up -d --build
```

## 安全与合规要点（已内置）

- 密码 bcrypt 哈希；JWT access(30min)/refresh(7d) 双令牌。
- 上传文件按用户隔离（`uploads/{user_id}/{doc_id}/`），接口强制校验归属。
- 上传白名单（pdf/docx/doc/txt）+ 20MB 大小限制。
- RAG 防幻觉提示词：禁止编造法条，检索不到必须明说。
- 免责声明由后端统一附带（SSE `done` 事件与报告接口），前端 `<Disclaimer/>` 组件渲染。

## 开发里程碑

M1 认证（已完成骨架）→ M2 问答 → M3 合同分析 → M4 前端联调 → M5 加固部署。
