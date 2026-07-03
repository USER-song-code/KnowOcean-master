# KnowOcean 代码重构规划方案

> 文档版本: v1.0
> 创建日期: 2026-05-30
> 分析范围: 全栈代码 (Spring Boot 后端 + Vue 3 前端 + PostgreSQL + Elasticsearch + MinIO)
> 分析方法: 三个维度并行深度扫描 (后端 Java 106 文件 / 前端 TS/Vue 73 文件 / 数据库+架构+配置)

---

## 目录

1. [总览与优先级矩阵](#一总览与优先级矩阵)
2. [安全修复 (CRITICAL)](#二安全修复-critical)
3. [后端重构](#三后端重构)
4. [前端重构](#四前端重构)
5. [数据库与基础设施](#五数据库与基础设施)
6. [架构层面改进](#六架构层面改进)
7. [测试体系建设](#七测试体系建设)
8. [实施路线图](#八实施路线图)
9. [附录: 完整问题清单](#九附录-完整问题清单)

---

## 一、总览与优先级矩阵

### 1.1 问题分布概览

| 维度 | CRITICAL | HIGH | MEDIUM | LOW | 合计 |
|------|----------|------|--------|-----|------|
| 安全 | 2 | 2 | 2 | 1 | 7 |
| 后端代码质量 | 0 | 3 | 6 | 5 | 14 |
| 前端代码质量 | 0 | 3 | 7 | 6 | 16 |
| 数据库/基础设施 | 0 | 2 | 4 | 3 | 9 |
| 架构/测试 | 0 | 1 | 3 | 2 | 6 |
| **合计** | **2** | **11** | **22** | **17** | **52** |

### 1.2 优先级定义

| 级别 | 含义 | 响应时间 |
|------|------|----------|
| **CRITICAL** | 安全漏洞，必须立即修复 | 24 小时内 |
| **HIGH** | 数据完整性/重大性能/用户可见缺陷 | 当前迭代 |
| **MEDIUM** | 代码可维护性、一致性改进 | 下个迭代 |
| **LOW** | 体验优化、技术债务清理 | 持续改进 |

---

## 二、安全修复 (CRITICAL)

### 2.1 [CRITICAL] 硬编码 API Key 已提交到版本控制

- **文件**: `KnowOcean-backend/src/main/resources/application-dev.yml` (第 25、30 行)
- **问题**: `sk-389dcbf5dbca4f4ba8e39f33a7c66ca6` 作为 DashScope 和 OpenAI 的默认 API Key 直接写在 YAML 中
- **风险**: 任何有仓库访问权限的人都能获取该 Key，可被滥用于消耗 API 额度
- **修复方案**:
  1. 立即在阿里云控制台**轮换该 API Key**
  2. 删除 YAML 中的默认值，改为仅使用环境变量: `api-key: ${DASHSCOPE_API_KEY}`
  3. 使用 `git filter-branch` 或 BFG 清理历史记录中的敏感信息
- **预估工时**: 1 小时 (轮换 + 清理)

### 2.2 [CRITICAL] JWT 密钥明文硬编码

- **文件**: 所有 profile YAML (`application-{dev,local,test}.yml`)
- **问题**: JWT 签名密钥以明文形式存在于配置文件中，且 Dev 环境使用可猜测的英文短语
- **风险**: 攻击者获取密钥后可以伪造任意用户的 JWT Token
- **修复方案**:
  1. 生成真随机 32 字节密钥: `openssl rand -base64 32`
  2. 所有环境的 JWT 密钥**仅通过环境变量注入**，不提供默认值
  3. 敏感配置使用 `application-secret.yml` 并加入 `.gitignore`
- **预估工时**: 0.5 天

### 2.3 [HIGH] 文件哈希计算失败时静默回退到 UUID

- **文件**: `DocumentUploadService.java` 第 763-778 行
- **问题**: `computeFileHash()` 在 SHA-256 计算失败时返回随机 UUID，导致:
  - 文件去重 (秒传) 机制完全失效
  - 恶意用户可能利用此缺陷绕过重复文件检测
- **修复方案**:
  - `NoSuchAlgorithmException` → 致命错误，应阻止应用启动
  - `IOException` → 抛出 `BusinessException`，通知用户上传失败
  - 移除 UUID 回退逻辑
- **预估工时**: 0.5 天

### 2.4 [HIGH] Dev 管理员密码硬编码

- **文件**: `DevAdminInitializer.java` 第 41 行
- **问题**: 默认密码 `Admin@123456` 写在源码中
- **风险**: 若 dev profile 被误部署到非开发环境，攻击者可直接以管理员身份登录
- **修复方案**: Dev profile 启动时生成随机密码并打印到日志，或强制要求配置
- **预估工时**: 0.5 天

### 2.5 [MEDIUM] SSE 流式响应泄漏原始异常消息

- **文件**: `AssistantChatController.java` 第 102-109 行
- **问题**: `exception.getMessage()` 直接发送给前端，可能泄露数据库连接串、文件路径、堆栈信息
- **修复方案**: 对 SSE 错误事件也使用统一的 sanitize 处理，生产环境返回 `"服务器内部错误"`
- **预估工时**: 0.5 天

### 2.6 [MEDIUM] 缺少 CORS 配置

- **问题**: 全代码库搜不到 `@CrossOrigin`、`CorsFilter`、`addCorsMappings`，若前后端不同源则浏览器拦截所有请求
- **修复方案**: 添加 `WebMvcConfigurer` Bean 配置 CORS，仅允许已知前端 Origin
- **预估工时**: 0.5 天

### 2.7 [LOW] 缺少 API 频率限制

- **问题**: 登录、注册、文件上传等接口无任何频率限制，容易被暴力破解或 DDoS
- **修复方案**: 对 `/api/auth/login`、`/api/auth/register`、`/api/documents/upload` 添加令牌桶限流 (Resilience4j 或 Bucket4j)
- **预估工时**: 1 天

---

## 三、后端重构

### 3.1 代码重复 (HIGH→MEDIUM)

#### 3.1.1 [HIGH] Token 估算逻辑在 3 处重复

- **文件**: `AssistantService.java:50`, `AssistantSessionSummaryService.java:31`, `AssistantShortTermMemoryMaintenanceService.java:29`
- **问题**: `text.length() / 4` 估算算法完全相同，三处独立维护
- **修复**: 抽取 `TokenEstimator` 工具类至 `common/`
- **预估工时**: 0.5 天

#### 3.1.2 [HIGH] ID 验证逻辑在 6+ 个 Service 中重复

- **文件**: `AssistantConversationService`, `AssistantSessionService`, `AdminUserService`, `GroupMembershipService`, `DocumentUploadService`
- **问题**: `if (id == null || id <= 0)` 模式在至少 6 个类中重复，命名不一致 (`requireUserId` vs `requirePositiveUserId`)
- **修复**: 创建 `common/validation/Assert.java` 统一工具类
- **预估工时**: 1 天

#### 3.1.3 [MEDIUM] 文本标准化逻辑在 4 个类中重复

- **文件**: `AssistantConversationService`, `AssistantMemorySummarizer`, `AssistantSessionSummaryService`, `AssistantSessionService`
- **问题**: `trim()` + 空白字符压缩 + 截断 逻辑各写各的
- **修复**: 抽取 `TextUtils` 工具类至 `common/`
- **预估工时**: 0.5 天

### 3.2 God Class 拆分 (HIGH)

#### 3.2.1 [HIGH] DocumentUploadService (877 行, 14 项职责)

- **文件**: `DocumentUploadService.java`
- **职责过载**: 分片上传 + 直传 + 秒传 + 补偿逻辑 + Hash 计算 + 元数据持久化 + 事件发布 + Key 构造
- **拆分方案**:
  ```
  DocumentUploadService (Facade, ~150 行)
  ├── ChunkedUploadService   (~200 行, init/chunk/complete/status)
  ├── DirectUploadService    (~100 行, 直传 + 秒传)
  └── UploadValidationService (~80 行, 所有参数校验)
  ```
- **预估工时**: 2 天

#### 3.2.2 [HIGH] AssistantConversationService (358 行, 8 个构造注入)

- **文件**: `AssistantConversationService.java`
- **职责过载**: 消息持久化 + 上下文加载 + 记忆维护 + 所有权验证 + 实体-VO 映射
- **拆分方案**:
  ```
  MessagePersistenceService   → 消息保存逻辑
  ConversationContextLoader   → 上下文加载 + 摘要生成触发
  (原服务变为薄调度层)
  ```
- **预估工时**: 1.5 天

### 3.3 不一致性修复 (MEDIUM)

#### 3.3.1 [MEDIUM] 枚举存储策略不一致

- **问题**: `User.systemRole` 等使用 Java Enum 类型 (由 MyBatis-Plus `EnumTypeHandler` 自动转换)，而 `AssistantMessageEntity.role`、`DocumentEntity.status` 等使用 `String` + 手动 `valueOf()`
- **影响**: 手动 `valueOf()` 可能抛出 `IllegalArgumentException` 导致 500 错误
- **修复**: 将所有实体的枚举字段改为实际 Enum 类型，统一使用 `EnumTypeHandler`
- **预估工时**: 1 天
- **涉及文件**: `AssistantMessageEntity`, `AssistantSessionEntity`, `DocumentEntity`, `IngestionJobEntity`, `DocumentUploadSessionEntity`

#### 3.3.2 [MEDIUM] @Slf4j 使用不一致

- **问题**: 大部分 Service 使用 `@Slf4j`，但 `AssistantAgentFacade`、`AssistantService`、`AssistantShortTermMemoryHook` 手动实例化 `LoggerFactory.getLogger()`
- **修复**: 统一使用 `@Slf4j`
- **预估工时**: 0.5 天

#### 3.3.3 [MEDIUM] DTO 类型不一致 — Record vs Class

- **问题**: 大部分 DTO 使用 Java `record`，唯独 `CreateAssistantSessionRequest` 使用手写 getter/setter 的普通类
- **修复**: 改为 `record CreateAssistantSessionRequest(String initialMessage) {}`
- **预估工时**: 0.5 天

#### 3.3.4 [MEDIUM] 日志语言混用

- **问题**: 部分日志用中文 (`"用户登录成功"`)，部分用英文、还有混用的 (`"refresh token 重放攻击"`)
- **建议**: 日志统一用英文 (方便日志聚合工具)，用户可见的错误消息保留中文
- **预估工时**: 1 天 (批量替换)

### 3.4 事务管理修复 (HIGH)

#### 3.4.1 [HIGH] @Transactional 自调用绕过代理

- **文件**: `AssistantService.java` 第 137-143 行
- **问题**: `streamChat(3-param)` 内部调用 `streamChat(4-param)`，Spring AOP 代理被绕过，内层 `@Transactional` 失效
- **修复**: 提取共享逻辑到 `private` 方法，或使用 `AopContext.currentProxy()`
- **预估工时**: 0.5 天

#### 3.4.2 [HIGH] 事务边界跨越外部服务调用

- **文件**: `DocumentUploadService.java` — `uploadChunk()`、`completeUpload()`、`uploadDocument()`
- **问题**: MinIO 对象存储操作与数据库操作在同一个 `@Transactional` 中，MinIO 成功但 DB 回滚时产生孤儿对象
- **修复**: 先上传 MinIO (事务外)，再写数据库 (事务内)；或实现补偿模式 (Saga)
- **预估工时**: 1.5 天

### 3.5 耦合度改善 (MEDIUM)

#### 3.5.1 [MEDIUM] 构造注入参数过多

- **文件**: `AssistantService` (7 个参数)、`AssistantConversationService` (8 个参数)
- **问题**: 交叉关注点 (LLM 用量收集、成本计算) 应该通过 AOP/事件方式解耦
- **修复**: 将 `LlmUsageCollector` + `LlmCostCalculator` 改为 Spring Event Listener 模式
- **预估工时**: 1 天

#### 3.5.2 [MEDIUM] 跨模块直接服务依赖

- **问题**: `assistant` 和 `document` 模块直接依赖 `group` 模块的 `GroupMembershipService`
- **修复**: 在 `common/` 中定义 `GroupAccessControl` 接口，`GroupMembershipService` 实现它，其他模块依赖接口
- **预估工时**: 1 天

### 3.6 实体映射改进 (MEDIUM)

#### 3.6.1 [MEDIUM] 多处手动 Map<String, Object> 解析

- **文件**: `GroupMembershipService.java` 第 129-158 行
- **问题**: `toVisibleGroup()`、`toPendingInvitationItem()` 使用不安全的 `(Number) row.get("groupId")` 强制转换
- **修复**: 使用 MyBatis `@Result` 注解映射到类型安全 DTO
- **预估工时**: 1 天

#### 3.6.2 [MEDIUM] 缺少统一的 Entity→VO 映射

- **问题**: 所有 Service 手动编写 `toVo()` / `toDto()` 方法，容易遗漏字段
- **修复**: 引入 MapStruct 进行编译期类型安全映射
- **预估工时**: 1 天

### 3.7 N+1 查询优化 (HIGH)

#### 3.7.1 [HIGH] 群组列表关联子查询

- **文件**: `GroupMembershipMapper.xml` `selectOwnedGroupsByUserId`
- **问题**: 每个群组执行一次 `SELECT COUNT(1) FROM group_join_requests` 关联子查询
- **修复**: 改为 `LEFT JOIN` + `GROUP BY`
- **预估工时**: 0.5 天

#### 3.7.2 [HIGH] 会话上下文加载 4-5 次顺序查库

- **文件**: `AssistantConversationService.java:130-157` (`loadConversationContext`)
- **问题**: 一次上下文加载顺序执行 5 次数据库查询，且最坏情况加载全部消息
- **修复**: 合并 `countBySessionId` + `selectRecentBySessionId` 为一条 SQL；全量消息查询添加 LIMIT
- **预估工时**: 1 天

### 3.8 清理工作 (LOW)

- **[LOW] 单值枚举**: `GroupStatus` (仅 `ACTIVE`)、`IngestionJobType` (仅 `INGEST_DOCUMENT`) — 添加注释说明或删除
- **[LOW] 更新 CLAUDE.md**: Lombok 实际使用情况与文档不符
- **[LOW] `AssistantShortTermMemoryHook`** 兼容旧框架的 `beforeModel(Object)` 无操作方法添加 `@Deprecated`
- **[LOW] Swagger Bearer Auth**: `OpenApiConfiguration` 缺少 `SecurityScheme` 配置

---

## 四、前端重构

### 4.1 God Component 拆分 (HIGH)

#### 4.1.1 [HIGH] AssistantView.vue (479 行 script + 模板/样式 ≈ 960 行)

- **文件**: `AssistantView.vue`
- **职责过载**: 会话管理 + 流式处理 + 群组加载 + 引用预览 + 重试 + 提示词 — 全部在一个组件
- **拆分方案**:
  - 抽取 `useAssistantSessions` composable — 会话 CRUD
  - 抽取 `useAssistantStream` composable — SSE 流管理
  - 原组件变为薄编排层 (≤150 行 script)
- **预估工时**: 1.5 天

#### 4.1.2 [HIGH] HomeView.vue (~1460 行)

- **文件**: `HomeView.vue`
- **问题**: 整个着陆页 (导航、Hero、特性、流程、案例、CTA、Footer) 全部在一个组件
- **拆分方案**: `LandingNavbar`、`LandingHero`、`LandingFeatures`、`LandingWorkflow`、`LandingCases`、`LandingCta`、`LandingFooter` — 7 个子组件
- **预估工时**: 1 天

#### 4.1.3 [MEDIUM] DefaultLayout.vue (799 行)

- **文件**: `DefaultLayout.vue`
- **拆分方案**: 抽取 `AppSidebar.vue` + `UserDropdown.vue`
- **预估工时**: 1 天

### 4.2 代码重复消除 (MEDIUM)

#### 4.2.1 [MEDIUM] SSE 流解析完全重复

- **文件**: `api/qa.ts` vs `api/assistant.ts`
- **问题**: 100+ 行重复代码 — Stream 读取循环、buffer 管理、`\n\n` 分割、`event:`/`data:` 解析完全相同
- **修复**: 创建 `src/api/sse.ts` 提供通用 `streamSSE()` 函数
- **预估工时**: 1 天

#### 4.2.2 [MEDIUM] `unwrapApiResponse` 在 4 个模块中各自定义

- **文件**: `api/auth.ts`、`api/admin-user.ts`、`api/metrics.ts`、`api/document.ts`
- **修复**: 从 `http.ts` 统一导出，所有模块引用同一实现
- **预估工时**: 0.5 天

#### 4.2.3 [MEDIUM] `formatDate` 在 3 个 Tab 组件中重复

- **文件**: `InvitationsTab.vue`、`OwnedGroupsTab.vue`、`JoinedGroupsTab.vue`
- **修复**: 抽取 `src/utils/dateFormat.ts`
- **预估工时**: 0.5 天

#### 4.2.4 [MEDIUM] Markdown 渲染 CSS 完全重复 (~140 行)

- **文件**: `QaMessage.vue` vs `AssistantMessage.vue`
- **问题**: h1-h4、code、pre、blockquote、table、img 样式完全相同
- **修复**: 抽取 `src/assets/markdown.css`，两个组件共同引用
- **预估工时**: 0.5 天

#### 4.2.5 [MEDIUM] 引用展示组件近乎相同

- **文件**: `qa/components/CitationRail.vue` vs `assistant/components/AssistantCitationBar.vue`
- **问题**: `formatScore`、`fileTag`/`fileIcon`、`tagClass`/`iconClass` 逻辑完全一致，仅布局方式不同
- **修复**: 创建通用 `CitationList.vue`，通过 `layout` prop 控制排列方式
- **预估工时**: 1 天

#### 4.2.6 [MEDIUM] 侧边栏组件结构近乎相同

- **文件**: `QaSidebar.vue` (525 行) vs `AssistantSidebar.vue` (612 行)
- **修复**: 抽取通用 `ChatSidebar.vue`，QA/Assistant 通过 slot 注入差异内容
- **预估工时**: 1.5 天

#### 4.2.7 [MEDIUM] 装饰背景 CSS 完全重复

- **文件**: `QaEmptyHero.vue` vs `AssistantEmpty.vue`
- **修复**: 抽取 `<DecorativeBackground>` 组件
- **预估工时**: 0.5 天

### 4.3 Composable 抽取 (MEDIUM)

以下模式在多个组件中重复，应抽取为 composable:

| Composable | 当前重复位置 | 预估工时 |
|------------|-------------|----------|
| `useGroupLoader` | `DocumentListView`、`QaView`、`AssistantView` | 0.5 天 |
| `useScrollToBottom` | `QaTranscript`、`AssistantTranscript` | 0.5 天 |
| `useFileDownload` | `DocumentListView` | 0.5 天 |
| `usePasswordValidation` | `SettingsView`、`AccountPasswordForm` | 0.5 天 |

### 4.4 类型安全修复 (MEDIUM)

- **[MEDIUM]** `InvitationsTab.vue:47` — `as any` 强制类型转换绕过 TypeScript 检查，应为 `PendingInvitationItem` 添加 `createdAt` 字段
- **[MEDIUM]** `DocumentStatus` 定义为 `string` 而非联合类型 — 改为 `type DocumentStatus = 'PROCESSING' | 'READY' | 'FAILED' | 'UPLOADED'`
- **[LOW]** `document.ts` 中 `readString`/`readNumber`/`readNumberArray` (~140 行规范化代码) 是因为后端 API 不一致产生的技术债，标记为待后端 API 标准化后移除

### 4.5 CSS 优化 (LOW)

- **[LOW]** `@keyframes spin` 在 8+ 个文件中重复定义 → 移至 `main.css` 全局定义
- **[LOW]** `groups-page.css:24-25` — `.primary-button` 存在无效 CSS 属性 `text` (无值) → 修复或移除
- **[LOW]** 渐变按钮样式在 8+ 个组件中重复 → 创建 `.btn-primary-gradient` 全局工具类
- **[LOW]** 输入框聚焦样式在 4+ 个组件中重复 → 创建 `.input-modern` 全局工具类

### 4.6 性能优化 (MEDIUM→LOW)

- **[MEDIUM]** 完整导入 Element Plus (~2MB) 而非按需加载 → 使用 `unplugin-element-plus`
- **[MEDIUM]** Google Fonts 通过 CSS `@import` 阻塞渲染 → 改用 `<link rel="preconnect">` + 异步加载
- **[MEDIUM]** 所有列表无分页 (文档、用户、会话、加入请求) → 实现分页 API + `usePagination` composable
- **[LOW]** `HomeView.vue` `IntersectionObserver` 未 disconnect → 在 `onBeforeUnmount` 中清理
- **[LOW]** `marked.setOptions()` 在 3 个组件中重复调用 → 在 `main.ts` 统一配置一次

### 4.7 其他清理 (LOW)

- **[LOW]** `AccountPasswordForm.vue` — 从未被使用的死代码，删除或用其替代 `SettingsView.vue` 内联表单
- **[LOW]** 登录表单逻辑在 `LoginModal.vue` 和 `LoginView.vue` 中完全重复 → 抽取 `<LoginForm>`
- **[LOW]** 404 路由重定向到 `/app/groups` 而不是显示 404 页面 → 添加 `NotFoundView`
- **[LOW]** `meta.requireAdmin` 已定义但路由守卫未显式检查 → 添加 `if (to.meta.requireAdmin)` 守卫
- **[LOW]** Home 页 Footer 所有链接 `href="#"`、Hero 段虚假指标数据 → 移除或接入真实数据

---

## 五、数据库与基础设施

### 5.1 缺失索引 (HIGH)

当前数据库存在多处缺少索引导致全表扫描的风险:

```sql
-- 1. users 表 - 按用户编码查询无索引
CREATE INDEX idx_users_user_code ON users (user_code);

-- 2. users 表 - 按状态筛选无索引
CREATE INDEX idx_users_status ON users (status);

-- 3. groups 表 - 按群组状态筛选无索引 (几乎所有群组查询都带 status 条件)
CREATE INDEX idx_groups_status ON groups (status);

-- 4. group_invitations 表 - 按群组+状态查询无独立索引
CREATE INDEX idx_invitations_group_status ON group_invitations (group_id, status);

-- 5. llm_usage_records 表 - 按用户+时间查询缺少最佳复合索引
CREATE INDEX idx_llm_usage_user_created ON llm_usage_records (user_id, created_at);
```

**预估工时**: 0.5 天

### 5.2 [HIGH] 配置 YAML 85% 重复

- **文件**: `application-{local,dev,test}.yml`
- **问题**: 三个 profile 文件 85% 内容完全相同，唯一的差异是连接地址和 API Key
- **影响**: 修改一个公共配置需要在三个文件中同步更新，极易遗漏
- **修复**: 将所有公共配置提升到 `application.yml`，profile 文件仅保留环境特定的覆盖 (≤20 行)
- **预估工时**: 1 天

### 5.3 数据库设计改进 (MEDIUM)

#### 5.3.1 [MEDIUM] 缺少外键级联规则

- **问题**: 所有 `FOREIGN KEY` 均无 `ON DELETE` 行为
- **影响**: 删除 Session 时如果中途崩溃，`assistant_messages` 和 `assistant_session_contexts` 残留孤儿行
- **修复**: 对逻辑删除的表添加 `ON DELETE CASCADE` 或确保 Service 层事务原子性

#### 5.3.2 [MEDIUM] 时间戳与时区

- **问题**: 所有 `TIMESTAMP` 列使用无时区的 `TIMESTAMP` 而非 `TIMESTAMPTZ`
- **修复**: 逐步迁移到 `TIMESTAMPTZ` (需要应用层配合)

#### 5.3.3 [MEDIUM] 缺少值约束

- **问题**: `system_role`、`status` 等列使用 `VARCHAR` 无 CHECK 约束，数据库层面允许任意值
- **修复**:
  ```sql
  ALTER TABLE users ADD CONSTRAINT chk_users_system_role
    CHECK (system_role IN ('ADMIN', 'USER'));
  ALTER TABLE users ADD CONSTRAINT chk_users_status
    CHECK (status IN ('ACTIVE', 'DISABLED'));
  ```

### 5.4 可观测性缺失 (MEDIUM)

- **[MEDIUM]** 无自定义健康检查 — 添加 `MinioHealthIndicator`、`ElasticsearchHealthIndicator`、`PgVectorHealthIndicator`
- **[MEDIUM]** `GlobalExceptionHandler` — 4xx 异常 (业务异常、权限异常) 完全不记录日志，运维排障完全盲区
- **[MEDIUM]** `LogAop` 参数日志无脱敏 — 密码、Token 等敏感信息可能被记录
- **[MEDIUM]** `Actuator` 已引入但未配置任何 endpoint — 配置 `health`、`metrics`、`prometheus` 端点
- **[LOW]** 无请求追踪 — 添加 `TraceIdFilter` 生成 UUID 并注入 MDC，实现全链路日志关联

### 5.5 依赖管理 (LOW)

- **[LOW]** `pom.xml` 缺少 `maven-enforcer-plugin` 检查依赖版本冲突
- **[LOW]** `pdfbox 2.0.31` 已过时，可升级到 3.x
- **[LOW]** MinIO SDK 排除了 `commons-io`，可能与其他依赖产生版本冲突

---

## 六、架构层面改进

### 6.1 安全基础设施 (HIGH)

- **添加 CORS 配置**: `WebMvcConfigurer.addCorsMappings()`
- **添加全局速率限制**: 登录/注册/上传接口 (Bucket4j + Redis)
- **Refresh Token Cookie 安全**: `local` profile 设置 `secure=false`，其他环境 `secure=true`

### 6.2 代码组织改进 (MEDIUM)

- **共享用户身份记录**: 当前有 5 个不同记录携带相同用户数据 (`AuthenticatedUser`、`CurrentUser`、`TokenSubject`、`AccessTokenClaims`、`CurrentUserProfileResponse`)，建议统一为 `UserIdentity`
- **跨模块访问控制接口**: 在 `common/` 定义 `GroupAccessControl` 接口，供 `assistant` 和 `document` 模块依赖而非直接依赖实现类

### 6.3 API 标准化 (MEDIUM)

- **前端 `document.ts`** 中 140 行数据规范化代码 (`readString`/`readNumber`/`readNumberArray`) 是后端文档 API 返回格式不一致的体现 — 标准化文档列表 API 的响应格式
- **`AssistantConversationController`** 返回原生的 VO 而非 `ApiResponse<T>` 包裹，与其他 Controller 不一致

---

## 七、测试体系建设

### 7.1 现状

| 维度 | 覆盖 |
|------|------|
| 后端测试 | 仅 1 个 `@WebMvcTest` (`QaControllerTest`)，覆盖率 ≈ 2% |
| 前端测试 | 0 个 |
| 集成测试 | 0 个 |
| E2E 测试 | 0 个 |

### 7.2 测试建设计划

#### 第一阶段: 关键路径单元测试 (HIGH)

| 测试目标 | 类型 | 预估工时 |
|----------|------|----------|
| `AuthService` — 登录/注册/刷新/登出 | `@ExtendWith(MockitoExtension.class)` | 1 天 |
| `JwtAccessTokenService` — Token 签发/验证/过期 | 单元测试 | 0.5 天 |
| `PasswordHasher` — BCrypt 哈希/验证 | 单元测试 | 0.5 天 |
| `GroupMembershipService` — 权限校验 | 单元测试 | 0.5 天 |
| `DocumentUploadService` — 上传流程 | 单元测试 | 1 天 |

#### 第二阶段: 集成测试 (MEDIUM)

| 测试目标 | 类型 | 预估工时 |
|----------|------|----------|
| 认证完整流程 | `@SpringBootTest` + Testcontainers | 1 天 |
| 文档 ETL 管线 | `@SpringBootTest` + Testcontainers | 1.5 天 |
| QA 问答检索 | `@SpringBootTest` + Mock AI | 1 天 |

#### 第三阶段: 前端测试 (MEDIUM)

| 测试目标 | 类型 | 预估工时 |
|----------|------|----------|
| Pinia Store (`auth.ts`, `app.ts`) | Vitest 单元测试 | 1 天 |
| API 层 (`http.ts`, 各模块) | Vitest + MSW | 1.5 天 |
| 关键组件 (`LoginModal`, `AssistantComposer`) | Vitest + Vue Test Utils | 1.5 天 |

**测试建设总预估工时**: ~10 天

---

## 八、实施路线图

### 8.1 阶段划分

```
第 1 周: 安全修复 + 配置清理
第 2 周: 后端 God Class 拆分 + N+1 优化
第 3 周: 后端一致性修复 + 事务修复
第 4 周: 前端 God Component 拆分 + 重复消除
第 5-6 周: 前端 Composable 抽取 + 基础设施改进
第 7-8 周: 测试体系建设
```

### 8.2 详细排期

#### Sprint 1 — 安全与基础设施 (5 天)

| 任务 | 优先级 | 工时 | 依赖 |
|------|--------|------|------|
| 轮换并移除硬编码 API Key | CRITICAL | 0.5d | — |
| JWT 密钥环境变量化 | CRITICAL | 0.5d | — |
| 移除 Hash 计算 UUID 回退 | HIGH | 0.5d | — |
| Dev Admin 密码随机化 | HIGH | 0.5d | — |
| SSE 错误消息脱敏 | MEDIUM | 0.5d | — |
| 添加 CORS 配置 | MEDIUM | 0.5d | — |
| YAML 配置去重合并 | HIGH | 1d | — |
| 添加缺失数据库索引 | HIGH | 0.5d | — |
| 配置 Actuator 前端点 | MEDIUM | 0.5d | — |

#### Sprint 2 — 后端核心重构 (5 天)

| 任务 | 优先级 | 工时 | 依赖 |
|------|--------|------|------|
| DocumentUploadService 拆分为 3 个类 | HIGH | 2d | — |
| AssistantConversationService 拆分 | HIGH | 1.5d | — |
| @Transactional 自调用修复 | HIGH | 0.5d | Sprint 1 |
| MinIO 事务边界修复 | HIGH | 1.5d | Sprint 1 |
| N+1 查询优化 (2处) | HIGH | 1.5d | — |
| 枚举存储策略统一 | MEDIUM | 1d | — |

#### Sprint 3 — 后端一致性 + 前端核心 (5 天)

| 任务 | 优先级 | 工时 | 依赖 |
|------|--------|------|------|
| Token 估算逻辑抽取 | HIGH | 0.5d | — |
| ID 验证工具类抽取 | HIGH | 0.5d | — |
| @Slf4j 统一 | MEDIUM | 0.5d | — |
| LLM 用量收集解耦 (事件模式) | MEDIUM | 1d | Sprint 2 |
| 跨模块接口抽象 | MEDIUM | 1d | Sprint 2 |
| 手动 Map 解析改为类型安全映射 | MEDIUM | 1d | — |
| HomeView 拆分为 7 个子组件 | HIGH | 1d | — |
| AssistantView 抽取 2 个 composable | HIGH | 1.5d | — |

#### Sprint 4 — 前端重复消除 (5 天)

| 任务 | 优先级 | 工时 |
|------|--------|------|
| SSE 通用解析函数提取 | MEDIUM | 1d |
| `unwrapApiResponse` 统一导出 | MEDIUM | 0.5d |
| Markdown CSS 共享 | MEDIUM | 0.5d |
| CitationList 统一组件 | MEDIUM | 1d |
| ChatSidebar 通用化 | MEDIUM | 1.5d |
| Composable 抽取 (4个) | MEDIUM | 2d |
| 类型安全修复 (3处) | MEDIUM | 0.5d |
| CSS 重复消除 | LOW | 0.5d |
| 性能优化 (Element Plus 按需加载等) | MEDIUM | 0.5d |

#### Sprint 5-6 — 测试 + 基础设施完善 (10 天)

| 任务 | 工时 |
|------|------|
| 认证/授权单元测试 (5 类) | 3d |
| 关键路径集成测试 (3 类) | 3.5d |
| 前端 Store/API/组件测试 | 4d |
| 健康检查 + 请求追踪 | 1d |
| 速率限制 | 1d |
| 前端分页实现 | 1.5d |
| 日志标准化 + 脱敏 | 1d |
| 文档更新 (CLAUDE.md 等) | 0.5d |

### 8.3 工时汇总

| 维度 | 工时 |
|------|------|
| 安全修复 (CRITICAL + HIGH) | 3.5 天 |
| 后端重构 | 14 天 |
| 前端重构 | 14.5 天 |
| 数据库/基础设施 | 5.5 天 |
| 测试建设 | 10 天 |
| 其他 (文档、清理) | 2 天 |
| **合计** | **~50 人天** |

> 注: 以上为单人估算。多人在不同模块可并行推进，实际日历时间可压缩到 5-6 周。

---

## 九、附录: 完整问题清单

### 后端问题清单 (26 项)

| # | 问题 | 文件 | 优先级 | 状态 |
|---|------|------|--------|------|
| 1 | API Key 硬编码 | `application-dev.yml:25,30` | CRITICAL | [ ] |
| 2 | JWT 密钥明文 | `application-*.yml` | CRITICAL | [ ] |
| 3 | Hash 失败静默回退 UUID | `DocumentUploadService.java:763` | HIGH | [ ] |
| 4 | Dev Admin 密码硬编码 | `DevAdminInitializer.java:41` | HIGH | [ ] |
| 5 | SSE 泄漏原始异常消息 | `AssistantChatController.java:102` | MEDIUM | [ ] |
| 6 | 缺少 CORS 配置 | 全局 | MEDIUM | [ ] |
| 7 | 缺少速率限制 | 全局 | LOW | [ ] |
| 8 | Token 估算重复 3 处 | `AssistantService` 等 3 文件 | HIGH | [ ] |
| 9 | ID 验证重复 6+ 处 | 6 个 Service | HIGH | [ ] |
| 10 | 文本标准化重复 4 处 | 4 个 memory 文件 | MEDIUM | [ ] |
| 11 | God Class: DocumentUploadService | `DocumentUploadService.java` | HIGH | [ ] |
| 12 | God Class: AssistantConversationService | `AssistantConversationService.java` | HIGH | [ ] |
| 13 | 枚举 String vs Enum 类型不一致 | 6 个 Entity | MEDIUM | [ ] |
| 14 | @Slf4j vs LoggerFactory 不一致 | 3 个文件 | MEDIUM | [ ] |
| 15 | DTO Record vs Class 不一致 | `CreateAssistantSessionRequest` | MEDIUM | [ ] |
| 16 | 日志中英文混用 | 全局 | MEDIUM | [ ] |
| 17 | @Transactional 自调用绕过 | `AssistantService.java:137` | HIGH | [ ] |
| 18 | 事务跨 MinIO+DB 边界 | `DocumentUploadService.java` 3 方法 | HIGH | [ ] |
| 19 | 构造注入参数过多 | `AssistantService`/`AssistantConversationService` | MEDIUM | [ ] |
| 20 | 跨模块直接依赖 | `assistant`→`group`, `document`→`group` | MEDIUM | [ ] |
| 21 | 手动 Map 强制转换 | `GroupMembershipService.java:129` | MEDIUM | [ ] |
| 22 | 缺少 Entity→VO 映射工具 | 全局 | MEDIUM | [ ] |
| 23 | N+1: 群组关联子查询 | `GroupMembershipMapper.xml` | HIGH | [ ] |
| 24 | N+1: 会话上下文 5 次查库 | `AssistantConversationService.java:130` | HIGH | [ ] |
| 25 | 单值枚举 (GroupStatus 等) | 2 个 Enum 文件 | LOW | [ ] |
| 26 | CLAUDE.md 与 Lombok 实际使用不符 | `CLAUDE.md` | LOW | [ ] |

### 前端问题清单 (23 项)

| # | 问题 | 文件 | 优先级 | 状态 |
|---|------|------|--------|------|
| 1 | God Component: AssistantView | `AssistantView.vue` | HIGH | [ ] |
| 2 | God Component: HomeView | `HomeView.vue` | HIGH | [ ] |
| 3 | God Component: DefaultLayout | `DefaultLayout.vue` | MEDIUM | [ ] |
| 4 | SSE 流解析重复 (~100 行) | `api/qa.ts`, `api/assistant.ts` | MEDIUM | [ ] |
| 5 | `unwrapApiResponse` 重复 4 处 | `api/auth.ts` 等 | MEDIUM | [ ] |
| 6 | `formatDate` 重复 3 处 | 3 个 Tab 组件 | MEDIUM | [ ] |
| 7 | Markdown CSS 重复 (~140 行) | `QaMessage`, `AssistantMessage` | MEDIUM | [ ] |
| 8 | 引用展示组件重复 | `CitationRail`, `AssistantCitationBar` | MEDIUM | [ ] |
| 9 | 侧边栏组件重复 | `QaSidebar`, `AssistantSidebar` | MEDIUM | [ ] |
| 10 | 装饰背景 CSS 重复 | `QaEmptyHero`, `AssistantEmpty` | MEDIUM | [ ] |
| 11 | `as any` 绕过类型检查 | `InvitationsTab.vue:47` | MEDIUM | [ ] |
| 12 | DocumentStatus 为宽泛 string | `document.ts:54` | MEDIUM | [ ] |
| 13 | API 规范化代码 140 行 | `document.ts:571-597` | LOW | [ ] |
| 14 | SSE JSON 解析无 try-catch | `api/assistant.ts:240` | MEDIUM | [ ] |
| 15 | 路由守卫未检查 `meta.requireAdmin` | `router/index.ts:61` | LOW | [ ] |
| 16 | 404 静默重定向而非 404 页面 | `router/index.ts:25` | LOW | [ ] |
| 17 | 登录表单重复 | `LoginModal` + `LoginView` | LOW | [ ] |
| 18 | 死代码: AccountPasswordForm | `AccountPasswordForm.vue` | LOW | [ ] |
| 19 | `@keyframes spin` 重复 8+ 处 | 8+ 个 Vue 文件 | LOW | [ ] |
| 20 | CSS 无效属性 | `groups-page.css:24` | LOW | [ ] |
| 21 | Element Plus 全量导入 | `main.ts:14` | MEDIUM | [ ] |
| 22 | Google Fonts 阻塞渲染 | `main.css:1-2` | MEDIUM | [ ] |
| 23 | IntersectionObserver 内存泄漏 | `HomeView.vue:88` | LOW | [ ] |

### 数据库/基础设施问题清单 (9 项)

| # | 问题 | 优先级 | 状态 |
|---|------|--------|------|
| 1 | 5 个缺失索引导致全表扫描 | HIGH | [ ] |
| 2 | YAML 配置 85% 重复 | HIGH | [ ] |
| 3 | 外键无级联删除规则 | MEDIUM | [ ] |
| 4 | TIMESTAMP 无时区 | MEDIUM | [ ] |
| 5 | VARCHAR 枚举列无 CHECK 约束 | MEDIUM | [ ] |
| 6 | 无自定义 HealthIndicator | MEDIUM | [ ] |
| 7 | 4xx 异常完全不记录日志 | MEDIUM | [ ] |
| 8 | LogAop 无参数脱敏 | MEDIUM | [ ] |
| 9 | 无请求 Trace ID | LOW | [ ] |
