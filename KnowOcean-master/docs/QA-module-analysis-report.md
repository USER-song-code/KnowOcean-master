# RAG 问答模块完整分析报告

## 一、API 契约

### 请求 (前端 → 后端)

```json
POST /api/qa/ask         (同步)
POST /api/qa/stream-ask  (SSE流式)

{ "groupId": <number>, "question": "<string, max 2000>" }
```

### 同步响应 (后端 → 前端) — **不走 ApiResponse 包装**

**成功时：**
```json
{
  "answered": true,
  "answer": "<string>",
  "citations": [
    {
      "documentId": <number|null>,
      "chunkId": <number|null>,
      "chunkIndex": <integer|null>,
      "fileName": "<string>",
      "score": <double>,
      "snippet": <null>        // 始终为 null
    }
  ]
}
```

**拒答时：**
```json
{
  "answered": false,
  "reasonCode": "INSUFFICIENT_EVIDENCE | ANSWER_FORMAT_ERROR",
  "reasonMessage": "<string>",
  "citations": []
}
```

### SSE 流式事件 (3 种)

| 事件名 | 时机 | 数据格式 |
|--------|------|---------|
| `token` | 逐字推送 | 纯文本 (非 JSON) |
| `citations` | 流结束后一次 | JSON 数组 `[{documentId, chunkId, chunkIndex, fileName, score, snippet:null}]` |
| `error` | 出错时 | `{"message": "<string>"}` |

连接超时：5 分钟 (300,000ms)

---

## 二、完整检索流水线

### 2.1 查询规划 (QueryPlanningService)

用 LLM 分析用户问题，输出 DIRECT/REWRITE/DECOMPOSE 策略：

- **DIRECT**: queries = [原始问题]
- **REWRITE**: queries = [原始问题] + LLM改写
- **DECOMPOSE**: queries = LLM拆分的子问题

最多 3 条查询。任何异常都 fallback 到 `DIRECT + [原始问题]`。

### 2.2 双路检索

对每条 planned query 并行检索：

**pgvector**: 余弦相似度，topK=50，filter `groupId == {groupId}`
**ES**: IK 分词器 (ik_max_word 索引 + ik_smart 查询)，两阶段评分：

```
Stage 1 (bool should): 4 子句 (match_phrase/match × fileName/chunkText)
Stage 2 (rescore):    4 子句 (加 operator=and), query_weight=0.2, rescore_weight=1.0, score_mode=total
```

ES 分数归一化: `min(1.0, log1p(rawScore) / log1p(100))`

### 2.3 RRF 融合 (k=0)

**关键**: 使用 `k=0` (非标准 RRF 的 k=60)，更激进：

- `rank_score = 1 / rank` (rank1=1.0, rank2=0.5, rank3=0.333)
- 多查询、双通道的 hits **累加** rankingScore
- 归一化: `1 - e^(-rawScore)` → 映射到 [0,1)

### 2.4 聚类 + 窗口扩展

- 同一文档的连续 chunkIndex 合并为一个 cluster
- neighborWindow=1: 左右各扩展 1 个 chunk
- 窗口文本 = 拼接文档名 + 扩展区间所有 chunk 原文

### 2.5 证据评估 (四级)

| 条件 | 等级 |
|------|------|
| 无文档 | NONE |
| >=2文档 + (双来源 或 [向量+score>=0.85]) | SUFFICIENT |
| 双来源 或 >=2文档 | PARTIAL |
| 其他 | WEAK |

---

## 三、回答生成

### 系统提示词 (结构化 JSON 模式)

```
你是群组知识问答助手，只能依据给定证据回答，不得补充外部知识或猜测。
请严格输出 JSON，不要输出 Markdown 或任何额外说明。

JSON 字段要求：
{ "answered": true/false, "answer": "回答正文", "reasonCode": "...", "reasonMessage": "..." }

规则：
1. 能回答时 answered=true，answer 使用简体中文。
2. 不能回答时 answered=false，answer 置空。
3. 只能基于给定证据回答，不能补充证据之外的背景知识、常识推断或主观猜测。
4. 如果用户提示中给出了 evidenceLevel 和回答策略，必须严格遵守该策略。
5. 当证据有限时，必须明确说明"依据有限"或"仅能回答证据覆盖部分"。
```

### 用户提示词模板

```
问题：{question}
证据等级：{evidenceLevel}
回答策略：{evidenceGuidance}

执行要求：
- WEAK：谨慎回答，必须说明"依据有限"
- PARTIAL：只回答证据覆盖部分
- SUFFICIENT：正常回答，但不得超出证据
```

### 回退机制

1. 第一次LLM调用 → 解析JSON
2. JSON解析失败 → **再调一次LLM** (相同prompt) → 二次解析
3. 二次也失败 → 返回 `ANSWER_FORMAT_ERROR` 拒答

### 流式系统提示词 (纯文本模式)

```
你是群组知识问答助手，只能依据给定证据回答，不得补充外部知识或猜测。
请直接输出纯文本回答正文，使用简体中文。不要输出 JSON、Markdown 等任何格式标记。
```

---

## 四、引用组装

从 metadata 提取字段 → 按 `fileName` 去重 (保留首次出现)：

| 字段 | 来源 |
|------|------|
| documentId | metadata["documentId"] |
| chunkId | metadata["chunkId"] |
| chunkIndex | metadata["chunkIndex"] |
| fileName | metadata["fileName"] 或 metadata["documentName"] |
| score | metadata["score"] |
| snippet | 始终 null |

---

## 五、前端 QA 页面逻辑

### 组件树
```
QaView.vue (主容器)
├── QaSidebar (群组选择 + 会话历史)
├── QaTranscript (消息滚动区)
│   └── QaMessage (消息气泡)
│       └── CitationRail (引用卡片)
├── QaComposer (输入框)
└── QaEmptyHero (欢迎界面)
```

### 状态处理

| 状态 | UI 展示 |
|------|--------|
| 检索中 | 动画 thinking dots + "正在检索知识库并生成回答..." |
| 流式生成中 | Markdown 渲染 + 闪烁光标 |
| answered=true | 完整回答 + 引用卡片 |
| answered=false | 红色错误卡片 (reasonCode + reasonMessage) |
| 流中断 | answered=false, reasonCode=STREAM_ERROR |

### 群组选择器

- 从 `appStore.visibleGroups` 加载
- 通过 `v-model` 双向绑定 `selectedGroupId`
- 切换群组 → 创建新会话 (会话按群组分 scope)

---

## 六、Python 实现 vs Java 实现差距

| 特性 | Java | Python | 差距 |
|------|------|--------|------|
| API 响应包装 | 直接返回 (无ApiResponse) | 直接返回 | ✅ |
| 查询规划 | LLM DIRECT/REWRITE/DECOMPOSE | LLM DIRECT/REWRITE/DECOMPOSE | ✅ |
| RRF k值 | 0 | 0 | ✅ |
| 分数归一化 | 1-e^(-x) | 1-e^(-x) | ✅ |
| 聚类+窗口扩展 | neighborWindow=1 | neighborWindow=1 | ✅ |
| 证据四级评估 | NONE/WEAK/PARTIAL/SUFFICIENT | NONE/WEAK/PARTIAL/SUFFICIENT | ✅ |
| ES两阶段评分 | rescore + operator=and | rescore + operator=and | ✅ |
| IK分词器 | ik_max_word + ik_smart | 同 ES 配置 | ✅ |
| DB回退 | 无 (依赖已有ETL数据) | 有 (ILIKE + 宽松回退) | 新增 |
| 结构化JSON输出回退 | 二次LLM调用 | 二次LLM调用 | ✅ |
| 流式纯文本 | 单独system prompt | 单独system prompt | ✅ |
| 引用去重 | fileName首次出现 | fileName首次出现 | ✅ |
| ETL缺失时的兜底 | 无 | 三层回退 | ✅ |

**核心差距已全部消除**。Python 版本实际比 Java 多了 DB 回退机制（当群组无向量/ES数据时仍能回答）。

--

### 当前测试问题排查

用户反馈"依据有限，当前证据只提供了一个文件名称" — 这不是 bug，是**数据问题**：

- 群组 3 的测试文档内容不含"上传"相关信息
- LLM 诚实地说无法评价
- 已修复 `chunk_text` 为空时从 MinIO 读取原文

切换到群组 1（有完整 ETL 数据）验证：QA 正常返回详细回答。
