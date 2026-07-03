"""Metrics 聚合查询服务

从 llm_usage_records、users、groups、documents 表聚合统计数据。
所有函数直接返回 camelCase 字典，与前端 API 类型一致。
"""
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ── 时间条件映射 ──

_PERIOD_INTERVALS: dict[str, str] = {
    "TODAY":         "created_at >= CURRENT_DATE",
    "LAST_7_DAYS":   "created_at >= CURRENT_DATE - INTERVAL '7 days'",
    "LAST_14_DAYS":  "created_at >= CURRENT_DATE - INTERVAL '14 days'",
    "LAST_30_DAYS":  "created_at >= CURRENT_DATE - INTERVAL '30 days'",
}
_DEFAULT_PERIOD = "LAST_7_DAYS"


def _period_where(period: str) -> str:
    return _PERIOD_INTERVALS.get(period, _PERIOD_INTERVALS[_DEFAULT_PERIOD])


async def _aggregate_usage(db: AsyncSession, where_clause: str, extra_where: str = "", params: dict | None = None) -> dict:
    """通用使用统计聚合查询，返回 camelCase 字典"""
    try:
        sql = f"""
            SELECT
                COALESCE(SUM(prompt_tokens), 0)      AS total_prompt_tokens,
                COALESCE(SUM(completion_tokens), 0)   AS total_completion_tokens,
                COALESCE(SUM(total_tokens), 0)        AS total_tokens,
                COALESCE(SUM(cost_amount), 0)         AS total_cost,
                COUNT(*)                              AS total_requests,
                SUM(CASE WHEN success THEN 1 ELSE 0 END)     AS success_requests,
                SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) AS failed_requests,
                AVG(latency_ms)                       AS avg_latency_ms
            FROM llm_usage_records
            WHERE {where_clause} {extra_where}
        """
        result = await db.execute(text(sql), params or {})
        row = result.fetchone()
        if not row or row.total_requests == 0:
            return {
                "totalPromptTokens": 0, "totalCompletionTokens": 0,
                "totalTokens": 0, "totalCost": 0.0,
                "totalRequests": 0, "successRequests": 0, "failedRequests": 0,
                "successRate": 0.0, "avgLatencyMs": 0.0,
            }
        sr = row.success_requests
        tr = row.total_requests
        rate = round(float(sr) / float(tr) * 100, 2) if tr > 0 else 0.0
        return {
            "totalPromptTokens": row.total_prompt_tokens,
            "totalCompletionTokens": row.total_completion_tokens,
            "totalTokens": row.total_tokens,
            "totalCost": float(row.total_cost or 0),
            "totalRequests": tr,
            "successRequests": sr,
            "failedRequests": row.failed_requests,
            "successRate": rate,
            "avgLatencyMs": round(float(row.avg_latency_ms or 0), 1),
        }
    except Exception as e:
        logger.error(f"_aggregate_usage failed: {e}")
        return {
            "totalPromptTokens": 0, "totalCompletionTokens": 0,
            "totalTokens": 0, "totalCost": 0.0,
            "totalRequests": 0, "successRequests": 0, "failedRequests": 0,
            "successRate": 0.0, "avgLatencyMs": 0.0,
        }


async def get_overview(db: AsyncSession):
    """仪表盘概览：今日 KPI + 30 天趋势 + 平台计数"""
    from src.common.response import ApiResponse

    try:
        today_where = _period_where("TODAY")
        today_data = await _aggregate_usage(db, today_where)

        # 30 天趋势
        trend_sql = """
            SELECT
                TO_CHAR(DATE(created_at), 'YYYY-MM-DD') AS date,
                COUNT(*)                                AS requests,
                COALESCE(SUM(total_tokens), 0)          AS tokens,
                COALESCE(SUM(cost_amount), 0)           AS cost
            FROM llm_usage_records
            WHERE """ + _period_where("LAST_30_DAYS") + """
            GROUP BY DATE(created_at)
            ORDER BY date
        """
        trend_result = await db.execute(text(trend_sql))
        daily_trend = [
            {"date": row.date, "requests": row.requests, "tokens": row.tokens, "cost": float(row.cost or 0)}
            for row in trend_result.fetchall()
        ]

        user_count = (await db.execute(text("SELECT COUNT(*) FROM users"))).scalar() or 0
        group_count = (await db.execute(text("SELECT COUNT(*) FROM groups WHERE status = 'ACTIVE'"))).scalar() or 0
        doc_count = (await db.execute(text("SELECT COUNT(*) FROM documents WHERE deleted = false"))).scalar() or 0

        return ApiResponse.ok(data={
            "todayRequests": today_data["totalRequests"],
            "todayTokens": today_data["totalTokens"],
            "todayCost": today_data["totalCost"],
            "todaySuccessRate": today_data["successRate"],
            "totalUsers": user_count,
            "totalGroups": group_count,
            "totalDocuments": doc_count,
            "dailyTrend": daily_trend,
        })
    except Exception as e:
        logger.error(f"get_overview failed: {e}")
        return ApiResponse.ok(data={
            "todayRequests": 0, "todayTokens": 0, "todayCost": 0.0, "todaySuccessRate": 0.0,
            "totalUsers": 0, "totalGroups": 0, "totalDocuments": 0, "dailyTrend": [],
        })


async def get_platform_stats(db: AsyncSession, period: str = "LAST_7_DAYS"):
    from src.common.response import ApiResponse
    try:
        where = _period_where(period)
        data = await _aggregate_usage(db, where)
        return ApiResponse.ok(data=data)
    except Exception as e:
        logger.error(f"get_platform_stats failed: {e}")
        return ApiResponse.ok(data={
            "totalPromptTokens": 0, "totalCompletionTokens": 0, "totalTokens": 0, "totalCost": 0.0,
            "totalRequests": 0, "successRequests": 0, "failedRequests": 0, "successRate": 0.0, "avgLatencyMs": 0.0,
        })


async def get_user_stats(db: AsyncSession, user_id: int, period: str = "LAST_7_DAYS"):
    from src.common.response import ApiResponse
    try:
        where = _period_where(period)
        data = await _aggregate_usage(db, where, "AND user_id = :uid", {"uid": user_id})
        return ApiResponse.ok(data=data)
    except Exception as e:
        logger.error(f"get_user_stats failed: {e}")
        return ApiResponse.ok(data={
            "totalPromptTokens": 0, "totalCompletionTokens": 0, "totalTokens": 0, "totalCost": 0.0,
            "totalRequests": 0, "successRequests": 0, "failedRequests": 0, "successRate": 0.0, "avgLatencyMs": 0.0,
        })


async def get_user_detail(db: AsyncSession, user_id: int, period: str = "LAST_7_DAYS"):
    from src.common.response import ApiResponse
    try:
        where = _period_where(period)

        user_row = (await db.execute(
            text("SELECT display_name FROM users WHERE id = :uid"), {"uid": user_id}
        )).fetchone()
        if not user_row:
            return ApiResponse.fail(code=404, message="用户不存在")

        usage_data = await _aggregate_usage(db, where, "AND user_id = :uid", {"uid": user_id})

        # 按模型拆分
        model_sql = f"""
            SELECT
                COALESCE(model_name, 'Unknown')           AS model_name,
                COUNT(*)                                  AS requests,
                COALESCE(SUM(prompt_tokens), 0)           AS prompt_tokens,
                COALESCE(SUM(completion_tokens), 0)       AS completion_tokens,
                COALESCE(SUM(total_tokens), 0)            AS total_tokens,
                COALESCE(SUM(cost_amount), 0)             AS cost
            FROM llm_usage_records
            WHERE {where} AND user_id = :uid
            GROUP BY model_name
            ORDER BY total_tokens DESC
        """
        model_result = await db.execute(text(model_sql), {"uid": user_id})
        model_breakdown = [
            {
                "modelName": row.model_name, "requests": row.requests,
                "promptTokens": row.prompt_tokens, "completionTokens": row.completion_tokens,
                "totalTokens": row.total_tokens, "cost": float(row.cost or 0),
            }
            for row in model_result.fetchall()
        ]

        # 按模块拆分
        module_sql = f"""
            SELECT module, COUNT(*) AS requests,
                   COALESCE(SUM(total_tokens), 0) AS total_tokens,
                   COALESCE(SUM(cost_amount), 0)  AS cost
            FROM llm_usage_records
            WHERE {where} AND user_id = :uid
            GROUP BY module ORDER BY total_tokens DESC
        """
        module_result = await db.execute(text(module_sql), {"uid": user_id})
        module_breakdown = [
            {"module": row.module, "requests": row.requests,
             "totalTokens": row.total_tokens, "cost": float(row.cost or 0)}
            for row in module_result.fetchall()
        ]

        # 每日趋势
        trend_sql = f"""
            SELECT TO_CHAR(DATE(created_at), 'YYYY-MM-DD') AS date,
                   COUNT(*) AS requests,
                   COALESCE(SUM(total_tokens), 0) AS tokens,
                   COALESCE(SUM(cost_amount), 0)  AS cost
            FROM llm_usage_records
            WHERE {where} AND user_id = :uid
            GROUP BY DATE(created_at) ORDER BY date
        """
        trend_result = await db.execute(text(trend_sql), {"uid": user_id})
        daily_trend = [
            {"date": row.date, "requests": row.requests, "tokens": row.tokens, "cost": float(row.cost or 0)}
            for row in trend_result.fetchall()
        ]

        doc_count = (await db.execute(
            text("SELECT COUNT(*) FROM documents WHERE uploader_user_id = :uid AND deleted = false"),
            {"uid": user_id},
        )).scalar() or 0

        question_count = (await db.execute(
            text(f"""SELECT COUNT(*) FROM llm_usage_records
                     WHERE {where} AND user_id = :uid AND module = 'QA'"""),
            {"uid": user_id},
        )).scalar() or 0

        return ApiResponse.ok(data={
            "userId": user_id,
            "displayName": user_row.display_name or "",
            "usageStats": usage_data,
            "modelBreakdown": model_breakdown,
            "moduleBreakdown": module_breakdown,
            "dailyTrend": daily_trend,
            "documentCount": doc_count,
            "questionCount": question_count,
        })
    except Exception as e:
        logger.error(f"get_user_detail failed: {e}")
        return ApiResponse.ok(data={
            "userId": user_id, "displayName": "",
            "usageStats": {"totalPromptTokens": 0, "totalCompletionTokens": 0, "totalTokens": 0, "totalCost": 0.0,
                           "totalRequests": 0, "successRequests": 0, "failedRequests": 0,
                           "successRate": 0.0, "avgLatencyMs": 0.0},
            "modelBreakdown": [], "moduleBreakdown": [], "dailyTrend": [],
            "documentCount": 0, "questionCount": 0,
        })


async def get_group_stats(db: AsyncSession, group_id: int, period: str = "LAST_7_DAYS"):
    from src.common.response import ApiResponse
    try:
        where = _period_where(period)
        data = await _aggregate_usage(db, where, "AND group_id = :gid", {"gid": group_id})
        return ApiResponse.ok(data=data)
    except Exception as e:
        logger.error(f"get_group_stats failed: {e}")
        return ApiResponse.ok(data={
            "totalPromptTokens": 0, "totalCompletionTokens": 0, "totalTokens": 0, "totalCost": 0.0,
            "totalRequests": 0, "successRequests": 0, "failedRequests": 0, "successRate": 0.0, "avgLatencyMs": 0.0,
        })


async def get_trend(db: AsyncSession, period: str = "LAST_7_DAYS", module: str | None = None):
    from src.common.response import ApiResponse
    try:
        where = _period_where(period)
        extra = ""
        params = {}
        if module:
            extra = "AND module = :mod"
            params["mod"] = module

        sql = f"""
            SELECT TO_CHAR(DATE(created_at), 'YYYY-MM-DD') AS date,
                   COUNT(*) AS requests,
                   COALESCE(SUM(total_tokens), 0) AS tokens,
                   COALESCE(SUM(cost_amount), 0)  AS cost
            FROM llm_usage_records
            WHERE {where} {extra}
            GROUP BY DATE(created_at) ORDER BY date
        """
        result = await db.execute(text(sql), params)
        data = [
            {"date": row.date, "requests": row.requests, "tokens": row.tokens, "cost": float(row.cost or 0)}
            for row in result.fetchall()
        ]
        return ApiResponse.ok(data=data)
    except Exception as e:
        logger.error(f"get_trend failed: {e}")
        return ApiResponse.ok(data=[])


async def get_user_rank(db: AsyncSession, period: str = "LAST_7_DAYS", limit: int = 10):
    from src.common.response import ApiResponse
    try:
        where = _period_where(period)
        sql = f"""
            SELECT u.id, u.display_name AS name,
                   COUNT(*) AS total_requests,
                   COALESCE(SUM(r.total_tokens), 0) AS total_tokens,
                   COALESCE(SUM(r.cost_amount), 0)  AS total_cost
            FROM llm_usage_records r
            JOIN users u ON u.id = r.user_id
            WHERE {where}
            GROUP BY u.id, u.display_name
            ORDER BY total_cost DESC
            LIMIT :limit
        """
        result = await db.execute(text(sql), {"limit": limit})
        data = [
            {"id": row.id, "name": row.name,
             "totalRequests": row.total_requests, "totalTokens": row.total_tokens,
             "totalCost": float(row.total_cost or 0)}
            for row in result.fetchall()
        ]
        return ApiResponse.ok(data=data)
    except Exception as e:
        logger.error(f"get_user_rank failed: {e}")
        return ApiResponse.ok(data=[])


async def get_group_rank(db: AsyncSession, period: str = "LAST_7_DAYS", limit: int = 10):
    from src.common.response import ApiResponse
    try:
        where = _period_where(period)
        sql = f"""
            SELECT g.id, g.group_name AS name,
                   COUNT(*) AS total_requests,
                   COALESCE(SUM(r.total_tokens), 0) AS total_tokens,
                   COALESCE(SUM(r.cost_amount), 0)  AS total_cost
            FROM llm_usage_records r
            JOIN groups g ON g.id = r.group_id
            WHERE {where} AND r.group_id IS NOT NULL
            GROUP BY g.id, g.group_name
            ORDER BY total_cost DESC
            LIMIT :limit
        """
        result = await db.execute(text(sql), {"limit": limit})
        data = [
            {"id": row.id, "name": row.name,
             "totalRequests": row.total_requests, "totalTokens": row.total_tokens,
             "totalCost": float(row.total_cost or 0)}
            for row in result.fetchall()
        ]
        return ApiResponse.ok(data=data)
    except Exception as e:
        logger.error(f"get_group_rank failed: {e}")
        return ApiResponse.ok(data=[])
