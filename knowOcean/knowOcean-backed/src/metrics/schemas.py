"""Metrics Pydantic Schemas

所有响应模型使用 camelCase 别名，与前端 API 类型对齐。
"""
from pydantic import BaseModel, Field


# ── 通用统计 ──

class UsageStats(BaseModel):
    total_prompt_tokens: int = Field(0, alias="totalPromptTokens")
    total_completion_tokens: int = Field(0, alias="totalCompletionTokens")
    total_tokens: int = Field(0, alias="totalTokens")
    total_cost: float = Field(0.0, alias="totalCost")
    total_requests: int = Field(0, alias="totalRequests")
    success_requests: int = Field(0, alias="successRequests")
    failed_requests: int = Field(0, alias="failedRequests")
    success_rate: float = Field(0.0, alias="successRate")
    avg_latency_ms: float = Field(0.0, alias="avgLatencyMs")

    model_config = {"populate_by_name": True, "by_alias": True}


# ── 趋势 ──

class TrendItem(BaseModel):
    date: str
    requests: int = 0
    tokens: int = 0
    cost: float = 0.0


# ── 排行 ──

class UsageRankItem(BaseModel):
    id: int
    name: str
    total_requests: int = Field(0, alias="totalRequests")
    total_tokens: int = Field(0, alias="totalTokens")
    total_cost: float = Field(0.0, alias="totalCost")

    model_config = {"populate_by_name": True, "by_alias": True}


# ── 仪表盘概览 ──

class MetricsOverview(BaseModel):
    today_requests: int = Field(0, alias="todayRequests")
    today_tokens: int = Field(0, alias="todayTokens")
    today_cost: float = Field(0.0, alias="todayCost")
    today_success_rate: float = Field(0.0, alias="todaySuccessRate")
    total_users: int = Field(0, alias="totalUsers")
    total_groups: int = Field(0, alias="totalGroups")
    total_documents: int = Field(0, alias="totalDocuments")
    daily_trend: list[TrendItem] = Field(default_factory=list, alias="dailyTrend")

    model_config = {"populate_by_name": True, "by_alias": True}


# ── 模型用量拆分 ──

class ModelBreakdownItem(BaseModel):
    model_name: str = Field(..., alias="modelName")
    requests: int = 0
    prompt_tokens: int = Field(0, alias="promptTokens")
    completion_tokens: int = Field(0, alias="completionTokens")
    total_tokens: int = Field(0, alias="totalTokens")
    cost: float = 0.0

    model_config = {"populate_by_name": True, "by_alias": True}


# ── 模块用量拆分 ──

class ModuleBreakdownItem(BaseModel):
    module: str
    requests: int = 0
    total_tokens: int = Field(0, alias="totalTokens")
    cost: float = 0.0

    model_config = {"populate_by_name": True, "by_alias": True}


# ── 用户使用详情（新端点） ──

class UserUsageDetail(BaseModel):
    user_id: int = Field(..., alias="userId")
    display_name: str = Field("", alias="displayName")
    usage_stats: UsageStats = Field(default_factory=UsageStats, alias="usageStats")
    model_breakdown: list[ModelBreakdownItem] = Field(default_factory=list, alias="modelBreakdown")
    module_breakdown: list[ModuleBreakdownItem] = Field(default_factory=list, alias="moduleBreakdown")
    daily_trend: list[TrendItem] = Field(default_factory=list, alias="dailyTrend")
    document_count: int = Field(0, alias="documentCount")
    question_count: int = Field(0, alias="questionCount")

    model_config = {"populate_by_name": True, "by_alias": True}
