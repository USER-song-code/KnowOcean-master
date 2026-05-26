<div align="center">

<img src="https://img.shields.io/badge/Java-21-ED8B00?style=for-the-badge&logo=openjdk&logoColor=white" alt="Java 21"/>
<img src="https://img.shields.io/badge/Spring_Boot-3.5.0-6DB33F?style=for-the-badge&logo=springboot&logoColor=white" alt="Spring Boot 3.5"/>
<img src="https://img.shields.io/badge/Vue-3.5-4FC08D?style=for-the-badge&logo=vuedotjs&logoColor=white" alt="Vue 3.5"/>
<img src="https://img.shields.io/badge/Vite-8.0-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite 8"/>
<img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL 16"/>
<img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License MIT"/>

</div>

<br/>

<h1 align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/KnowOcean-知识海洋平台-4A90D9?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iOSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIxLjUiLz48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSI0IiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjEuNSIvPjwvc3ZnPg==&logoColor=white&labelColor=2a6cb6"/>
    <img src="https://img.shields.io/badge/KnowOcean-知识海洋平台-4A90D9?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iOSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIxLjUiLz48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSI0IiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjEuNSIvPjwvc3ZnPg==&logoColor=white&labelColor=2a6cb6" alt="KnowOcean"/>
  </picture>
</h1>

<p align="center">
  <strong>融合 RAG 与 AI Agent 技术的企业级智能知识平台</strong>
</p>

<p align="center">
  <a href="#-核心亮点">核心亮点</a> ·
  <a href="#-系统架构">系统架构</a> ·
  <a href="#-功能模块">功能模块</a> ·
  <a href="#-技术栈">技术栈</a> ·
  <a href="#-快速开始">快速开始</a> ·
  <a href="#-api-概览">API 概览</a> ·
  <a href="#-项目结构">项目结构</a>
</p>

<br/>

---

## ✨ 为什么选择 KnowOcean？

**KnowOcean** 不只是另一个"套壳 ChatGPT"。它是一个从底层构建的 **RAG（检索增强生成）+ AI Agent 知识库平台**，解决 LLM 在垂直领域应用中的三大核心痛点：

| 痛点 | KnowOcean 的解决方案 |
|------|-----------------|
| 🔮 幻觉编造 | 混合检索 + 四级证据评估 + 拒答机制，回答基于真实文档，无法回答时主动拒答 |
| 📚 知识割裂 | 完整 ETL 流水线——文档解析 → 结构感知切片 → 双路索引，打通"文件→知识"全链路 |
| 🧠 无记忆对话 | ReactAgent + 三级短期记忆压缩，跨轮次上下文感知，200 轮以上长对话不丢失关键信息 |

---

## 🔥 核心亮点

<table>
<tr>
<td width="50%">

### 🎯 RAG 全链路闭环

自研完整 RAG 流水线，每一个环节都是可控的：

```
文档上传 → 智能解析 → 结构感知切片
    ↓
向量嵌入 (PGvector HNSW) + 关键词索引 (ES IK)
    ↓
用户提问 → 查询规划 (LLM) → 混合检索 (RRF 融合)
    ↓
证据评估 (四级充分度) → LLM 生成 → 引用溯源
```

**不是简单的"搜索 + GPT 包装"**——查询规划、RRF 融合排序、四级证据评估均为自研实现。

</td>
<td width="50%">

### 🤖 AI Agent 对话引擎

基于 **Spring AI Alibaba ReactAgent** 图执行引擎：

- **双模式切换**：CHAT（纯对话）/ KB_SEARCH（知识库检索），同会话内动态切换
- **工具编排**：Agent 自主决定是否调用检索工具，每轮最多一次防止 token 浪费
- **SSE 流式输出**：逐字推送到前端，打字机效果，< 200ms 首字延迟
- **短期记忆**：三级渐进压缩，在有限的上下文窗口内维持超长对话

</td>
</tr>
<tr>
<td width="50%">

### 🔍 混合检索架构

**向量语义检索 + 关键词全文检索** 双通道并行，RRF 融合排序：

- **语义匹配**：PGvector + HNSW 索引 + COSINE_DISTANCE
- **精确匹配**：Elasticsearch + IK 中文分词 + BM25
- **证据增强**：类簇聚合 + 邻居窗口扩展，避免碎片化

</td>
<td width="50%">

### 🛡️ 企业级安全

- **三级角色权限**：Admin / Group Owner / Member
- **JWT 双令牌**：Access Token (30min) + Refresh Token (14天，httpOnly Cookie)
- **Refresh Token Rotation**：原子吊销 + 重放检测
- **BCrypt 密码加密** + 强制改密策略
- **群组数据隔离**：所有检索强制附加 groupId 过滤
- **AOP 操作日志**：关键操作全程留痕

</td>
</tr>
</table>

---

## 🏗️ 系统架构

```
┌──────────────────────────────────────────────────┐
│                    前端层                          │
│     Vue 3 SPA · Element Plus · Pinia · Axios      │
└──────────────────┬───────────────────────────────┘
                   │ HTTP (JWT Bearer) / SSE
┌──────────────────▼───────────────────────────────┐
│                  JWT 认证过滤器                     │
│          Access Token 解析 + 角色提取               │
└──────────────────┬───────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────┐
│                   业务服务层                        │
│  ┌──────────┐ ┌────────┐ ┌──────────┐             │
│  │ 认证授权  │ │文档管理│ │ ETL 流水线│             │
│  │ 注册/登录 │ │分片上传│ │ 解析→切片 │             │
│  │ 令牌刷新  │ │秒传下载│ │ 向量→ES  │             │
│  └──────────┘ └────────┘ └──────────┘             │
│  ┌──────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │ 群组协作  │ │ 知识库问答    │ │   AI 助手     │   │
│  │ 邀请/审批 │ │ RRF 混合检索 │ │ ReactAgent   │   │
│  │ 成员管理  │ │ 证据评估/溯源 │ │ 记忆管理/SSE │   │
│  └──────────┘ └──────────────┘ └──────────────┘   │
└──────────────────┬───────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────┐
│               数据与检索引擎层                       │
│  ┌──────────┐ ┌────────────┐ ┌────────────────┐   │
│  │PostgreSQL│ │Elasticsearch│ │     MinIO       │   │
│  │+ pgvector│ │  + IK 分词  │ │   对象存储       │   │
│  │HNSW 索引 │ │ BM25 检索   │ │  分片合并       │   │
│  └──────────┘ └────────────┘ └────────────────┘   │
└──────────────────┬───────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────┐
│                  AI 模型层                         │
│     DashScope deepseek-v4-pro (Chat)              │
│     DashScope text-embedding-v3 (Embedding)       │
└──────────────────────────────────────────────────┘
```

---

## 📦 功能模块

### 🔐 用户认证与群组协作

- JWT 双令牌认证、BCrypt 密码加密、角色权限（ADMIN / USER）
- 创建知识库群组、邀请成员（邀请码机制）、加入申请与审批
- 群组内 OWNER / MEMBER 角色，细粒度权限控制

### 📄 文档全生命周期

- **分片上传协议**：init → chunk upload → complete 三阶段，支持断点续传、SHA-256 秒传
- **多格式解析**：PDF (PDFBox) / DOCX (POI) / Markdown / TXT，自动编码检测
- **ETL 异步流水线**：Spring Event + `@Async` + 重试机制，7 步全自动
- **MinIO 对象存储**：S3 兼容，composeObject 合并分片

### 🧠 知识库问答 (RAG)

- **LLM 查询规划**：自动判断 DIRECT / REWRITE / DECOMPOSE 策略
- **双通道混合检索**：向量 + 关键词 → RRF 融合排序 → 类簇聚合扩展
- **四级证据评估**：NONE → WEAK → PARTIAL → SUFFICIENT，不足时主动拒答
- **引用溯源**：每条回答附带引用片段、来源文档、相关度评分

### 🤖 AI 智能助手

- **ReactAgent 图引擎**："思考 → 工具调用 → 生成回复"完整链路
- **双模式**：CHAT / KB_SEARCH，同会话动态切换
- **BEFORE_MODEL Hook**：模型调用前自动注入上下文记忆
- **三级记忆压缩**：
  - L1 会话记忆（增量 LLM 摘要）
  - L2 紧凑摘要（精炼历史压缩）
  - L3 运行时截断（超 50000 token 的最后防线）
- **SSE 流式输出**：逐字推送，含 delta 去重

### 📊 LLM 用量统计

- 自动采集每次 LLM 调用的 token 消耗、延迟、费用
- 支持按用户/群组/模块/时间维度的统计分析
- 仪表盘概览 + 趋势图 + 排行榜

---

## 🛠️ 技术栈

### 后端

| 层次 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 语言 | **Java** | 21 | Records, Pattern Matching, Virtual Threads |
| 框架 | **Spring Boot** | 3.5.0 | Spring MVC, Jakarta EE |
| ORM | **MyBatis-Plus** | 3.5.15 | Lambda 类型安全查询 + BaseMapper |
| 数据库 | **PostgreSQL + pgvector** | 16+ | HNSW 向量索引, COSINE_DISTANCE |
| 搜索引擎 | **Elasticsearch** | 8.x | IK 中文分词 + BM25 关键词检索 |
| 对象存储 | **MinIO** | 8.5 | S3 兼容，分片合并 |
| AI Chat | **Spring AI Alibaba** | 1.1.2 | DashScope 原生集成 |
| AI Agent | **Spring AI Alibaba Agent** | 1.1.2 | ReactAgent 图执行引擎 |
| Embedding | **Spring AI OpenAI** | 1.1.2 | 兼容模式走 DashScope |
| 认证 | **JJWT** | 0.12.6 | HMAC-SHA256 JWT |
| 文档解析 | **PDFBox / POI** | 2.0.31 / 5.2.5 | PDF + DOCX 文本提取 |
| API 文档 | **Knife4j + SpringDoc** | 4.5.0 | /doc.html 在线调试 |

### 前端

| 层次 | 技术 | 版本 |
|------|------|------|
| 语言 | **TypeScript** | 6.0 |
| 框架 | **Vue 3** (Composition API) | 3.5 |
| 构建 | **Vite** | 8.0 |
| 路由 | **Vue Router** | 5.0 |
| 状态管理 | **Pinia** | 3.0 |
| UI 组件 | **Element Plus** | 2.14 |
| HTTP | **Axios** | 1.16 |
| Markdown | **marked** | 18.0 |

### 基础设施

| 组件 | 用途 | 关键配置 |
|------|------|---------|
| **PostgreSQL 16 + pgvector** | 主存储 + 向量索引 | 512维, HNSW, COSINE_DISTANCE |
| **Elasticsearch 8.x** | 全文关键词检索引擎 | IK 中文分词, BM25 |
| **MinIO** | 对象存储 (文档持久化) | S3 兼容，分片合并 |
| **DashScope** | LLM Chat + Embedding | deepseek-v4-pro + text-embedding-v3 |

---

## 🚀 快速开始

### 环境要求

| 组件 | 版本 | 说明 |
|------|------|------|
| JDK | **21** | Record 语法、虚拟线程 |
| Node.js | **≥ 20.19** | 前端构建 |
| PostgreSQL | **16+** | 需安装 `pgvector` 扩展 |
| Elasticsearch | **8.x** | 需安装 IK 中文分词器插件 |
| MinIO | **latest** | 对象存储（Docker 快速部署） |
| DashScope API Key | — | LLM Chat + Embedding 共用 |

### 1️⃣ 初始化中间件

<details>
<summary><b>PostgreSQL + pgvector</b></summary>

```bash
# 安装 pgvector 扩展
psql -h <host> -U <user> -d <database> -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 执行建表脚本
psql -h <host> -U <user> -d <database> -f sql/schema.sql
```
</details>

<details>
<summary><b>MinIO (Docker)</b></summary>

```bash
docker run -d --name minio \
  -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ":9001"

# 访问 http://localhost:9001 创建 Bucket（默认名称：knowocean-rag-documents）
```
</details>

<details>
<summary><b>Elasticsearch + IK 分词器</b></summary>

```bash
docker run -d --name elasticsearch \
  -p 9200:9200 -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  elasticsearch:8.x

# 安装 IK 分词器
docker exec -it elasticsearch bin/elasticsearch-plugin install \
  https://github.com/medcl/elasticsearch-analysis-ik/releases/download/v8.x/elasticsearch-analysis-ik-8.x.zip
docker restart elasticsearch
```
</details>

### 2️⃣ 配置环境

编辑 `KnowOcean-backend/src/main/resources/application-local.yml`，填写配置：

```yaml
# 数据库连接
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/dd_rag
    username: your_username
    password: your_password

# AI 模型 (Chat 使用 DashScope 原生，Embedding 通过 OpenAI 兼容模式)
spring.ai.dashscope.api-key: ${DASHSCOPE_API_KEY}
spring.ai.openai.api-key: ${DASHSCOPE_API_KEY}

# MinIO 对象存储
storage:
  minio:
    endpoint: http://localhost:9000
    access-key: minioadmin
    secret-key: minioadmin

# Elasticsearch
elasticsearch:
  host: localhost
  port: 9200

# JWT 密钥 (生产环境务必修改)
rag.auth.jwt-secret: your-32byte-production-secret
```

### 3️⃣ 启动后端

```bash
# 设置 JDK 21
export JAVA_HOME="/path/to/jdk-21"

cd KnowOcean-backend

# 编译
./mvnw clean compile

# 启动 (默认 local 环境，端口 10001)
./mvnw spring-boot:run

# Swagger 文档 → http://localhost:10001/doc.html
```

### 4️⃣ 启动前端

```bash
cd KnowOcean-frontend

npm install
npm run dev

# 访问 → http://localhost:5173
```

### 🔑 默认管理员账户

开发环境（`profile: dev`）自动创建管理员账户：

| 字段 | 值 |
|------|-----|
| 用户名 | `admin` |
| 密码 | `Admin123456` |
| 角色 | ADMIN（系统管理员） |

> 可通过 `application-dev.yml` 中的 `rag.dev-admin.*` 配置项自定义。

---

## 📡 API 概览

### 认证 · `/api/auth`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 登录 (返回 Access + Refresh Token) |
| POST | `/api/auth/refresh` | 刷新令牌 (Cookie 中的 Refresh Token) |
| POST | `/api/auth/logout` | 登出 (吊销 Refresh Token) |
| GET | `/api/auth/me` | 获取当前用户信息 |

### 群组协作 · `/api/groups`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/groups` | 创建群组 (自动成为 Owner) |
| GET | `/api/groups/my` | 我的群组列表 + 待处理邀请 |
| GET | `/api/groups/{id}/members` | 查看群组成员 |
| POST | `/api/groups/{id}/invitations` | 邀请用户加入 (Owner 权限) |
| POST | `/api/groups/join-requests` | 通过群组编码申请加入 |
| POST | `/api/groups/{id}/join-requests/{reqId}/approve` | 审批通过加入申请 |

### 文档管理 · `/api/documents`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/documents/upload/init` | 初始化分片上传 (含秒传/续传检测) |
| POST | `/api/documents/upload/chunks` | 上传单个分片 |
| POST | `/api/documents/upload/{uploadId}/complete` | 完成上传，合并分片并触发 ETL |
| POST | `/api/documents/upload` | 小文件直传 (≤10MB) |
| GET | `/api/documents` | 文档列表 (多条件筛选) |
| GET | `/api/documents/{id}/preview` | 预览文档全文 |
| GET | `/api/documents/{id}/download` | 下载原始文件 |
| DELETE | `/api/documents/{id}` | 软删除文档 |
| POST | `/api/documents/{id}/retry-ingestion` | 重新处理失败文档 |

### 知识库问答 · `/api/qa`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/qa/ask` | 提交问题，获取 AI 回答 + 引用溯源 |
| POST | `/api/qa/stream-ask` | 流式提问 (SSE，逐 token 推送) |

<details>
<summary><b>请求 / 响应示例</b></summary>

**POST /api/qa/ask**
```json
// 请求
{ "groupId": 1, "question": "如何开始使用文档上传功能？上传失败后怎么重试？" }

// 成功响应
{
  "answered": true,
  "answer": "您可以通过以下步骤上传文档：1. 登录后进入文档管理页面...",
  "citations": [
    {
      "documentId": 1,
      "chunkId": 15,
      "fileName": "使用手册.pdf",
      "score": 0.97,
      "snippet": "点击上传按钮选择文档..."
    }
  ]
}

// 拒答响应
{
  "answered": false,
  "reasonCode": "INSUFFICIENT_EVIDENCE",
  "reasonMessage": "检索到的有效证据不足，暂不回答。",
  "citations": []
}
```
</details>

### AI 助手 · `/api/assistant`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/assistant/sessions` | 创建新会话 |
| GET | `/api/assistant/sessions` | 获取会话列表 |
| GET | `/api/assistant/sessions/{id}` | 获取会话详情 |
| PATCH | `/api/assistant/sessions/{id}` | 重命名会话 |
| DELETE | `/api/assistant/sessions/{id}` | 删除会话 |
| GET | `/api/assistant/sessions/{id}/context` | 获取会话上下文 (摘要 + 最近消息) |
| POST | `/api/assistant/chat` | 同步聊天 (CHAT / KB_SEARCH) |
| POST | `/api/assistant/chat/stream` | 流式聊天 (SSE，逐字推送) |

### 管理后台 · `/api/admin`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/users` | 用户列表 (仅 ADMIN) |
| GET | `/api/admin/users/{id}` | 用户详情 |
| PATCH | `/api/admin/users/{id}/status` | 修改用户状态 (启用/禁用) |
| GET | `/api/admin/metrics/overview` | 仪表盘概览 |
| GET | `/api/admin/metrics/platform` | 平台整体统计 |
| GET | `/api/admin/metrics/trend` | 趋势数据 |
| GET | `/api/admin/metrics/rank/users` | 用户用量排行 |

---

## 📁 项目结构

```
KnowOcean/
├── KnowOcean-backend/                    # Spring Boot 后端
│   ├── src/main/java/com/knowOcean/rag/
│   │   ├── auth/                     # 认证授权 (JWT 双令牌 + BCrypt)
│   │   ├── user/                     # 用户管理 (CRUD + 密码策略)
│   │   ├── group/                    # 群组协作 (邀请/审批/成员/角色)
│   │   ├── document/                 # 文档管理 (分片上传/秒传/预览/下载)
│   │   ├── ingestion/                # ETL 流水线
│   │   │   └── service/pipeline/
│   │   │       ├── reader/           #   对象存储文档读取
│   │   │       ├── parser/           #   PDF/DOCX/MD/TXT 多格式解析
│   │   │       └── transformer/      #   文本清洗 + 结构感知切片
│   │   ├── qa/                       # 知识库问答
│   │   │   ├── rag/                  #   混合检索 + 查询改写
│   │   │   ├── service/              #   问答编排 + 证据评估
│   │   │   └── support/              #   引用组装 + 回答解析
│   │   ├── assistant/                # AI 助手
│   │   │   ├── agent/                #   ReactAgent 工厂 + KB 检索工具
│   │   │   ├── memory/               #   三级短期记忆压缩
│   │   │   ├── controller/           #   会话/聊天/上下文 API
│   │   │   └── service/              #   对话编排 + SSE 发射器
│   │   ├── engine/                   # 基础设施
│   │   │   ├── elasticsearch/        #   ES 索引服务
│   │   │   ├── pgvector/             #   PGvector 检索适配器
│   │   │   └── storage/              #   MinIO 对象存储
│   │   ├── metrics/                  # LLM 用量统计 + 成本计算
│   │   └── common/                   # 公共基础设施
│   │       ├── api/ApiResponse       #   统一响应 record
│   │       ├── enums/                #   系统枚举
│   │       └── exception/            #   异常体系 + 全局异常处理
│   └── src/main/resources/
│       ├── mappers/                  # MyBatis XML (12 个)
│       └── prompts/                  # LLM 提示词模板 (StringTemplate)
│           ├── qa/                   #   QA 问答提示词 (3 个)
│           ├── assistant/            #   助手记忆提示词 (3 个)
│           └── query-planning/       #   查询规划提示词 (1 个)
│
├── KnowOcean-frontend/                   # Vue 3 前端
│   └── src/
│       ├── api/                      # Axios HTTP 封装 (8 个模块)
│       ├── views/                    # 页面组件
│       │   ├── HomeView.vue          #   产品首页 (Feature/流程/Case)
│       │   ├── LoginView.vue         #   登录页
│       │   ├── documents/            #   文档管理
│       │   ├── qa/                   #   知识库问答 (SSE 流式)
│       │   ├── assistant/            #   AI 助手 (SSE + 记忆)
│       │   ├── groups/               #   协作小组
│       │   ├── admin/                #   用户管理 + 用量统计
│       │   └── settings/             #   系统设置
│       ├── stores/                   # Pinia 状态 (auth + app)
│       ├── router/                   # 路由 + 认证守卫
│       ├── components/               # 公共组件 (LoginModal 等)
│       └── types/                    # TypeScript 类型定义
│
├── docs/                             # 版本设计文档
│   ├── V1.0-项目文档.md              #   用户认证 + 群组管理
│   ├── V2.0-项目文档.md              #   文档上传 + ETL 流水线
│   ├── V3.0-项目文档.md              #   知识库问答 (RAG)
│   └── V4.0-项目文档.md              #   AI 助手 Agent + 流式对话
│
└── sql/
    └── schema.sql                    # 数据库建表 DDL (含注释)
```

---

## 📖 版本演进

KnowOcean 采用渐进式迭代开发，每个版本聚焦一个核心主题：

| 版本 | 主题 | 核心交付 |
|------|------|---------|
| **V1.0** | 基础设施 | JWT 双令牌认证、群组协作 (邀请/审批/角色)、统一异常处理、API 文档 |
| **V2.0** | 文档引擎 | 分片上传 (断点续传/秒传)、ETL 流水线 (解析→切片→向量→索引)、双路检索引擎 |
| **V3.0** | RAG 问答 | LLM 查询规划、RRF 混合检索融合、四级证据评估、结构化输出 + 引用溯源、SSE 流式 |
| **V4.0** | AI Agent | ReactAgent 图引擎、CHAT/KB_SEARCH 双模式、三级短期记忆压缩、会话管理 |

> 每个版本的详细设计决策参见 [`docs/`](docs/) 目录。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request。

提交 PR 前请确保：
- 后端 `./mvnw clean compile` 编译通过
- 前端 `npm run build` 构建通过
- 遵循项目现有代码风格和命名规范

---

## 📄 License

本项目采用 [MIT](LICENSE) 开源协议。

---

<p align="center">
  <sub>Made with ❤️ by KnowOcean Team · 让每一次提问都有据可查</sub>
</p>
