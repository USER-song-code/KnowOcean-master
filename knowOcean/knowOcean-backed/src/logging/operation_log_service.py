"""操作日志查询服务

合并 operation_logs（系统操作）和 llm_usage_records（LLM 调用）为统一活动日志。
"""
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.common.response import ApiResponse

logger = logging.getLogger(__name__)

# 类别映射
CATEGORY_LABELS: dict[str, str] = {
    "AUTH":     "认证",
    "ADMIN":    "管理",
    "DOCUMENT": "文档",
    "QA":       "知识问答",
    "ASSISTANT":"AI助手",
}

ACTION_LABELS: dict[str, str] = {
    "LOGIN":        "登录",
    "LOGOUT":       "登出",
    "USER_ENABLE":  "启用用户",
    "USER_DISABLE": "禁用用户",
    "DOC_UPLOAD":   "上传文档",
    "DOC_DELETE":   "删除文档",
    "qa/ask":       "QA 提问",
    "qa/stream-ask":"QA 流式提问",
    "qa/query-plan":"QA 查询规划",
    "qa/ask-retry": "QA 重试",
}


async def get_operation_logs(
    db: AsyncSession,
    user_id: int | None = None,
    category: str | None = None,
    page: int = 1,
    size: int = 20,
) -> ApiResponse:
    """统一查询操作日志 + LLM 调用日志，按时间倒序分页。

    返回格式:
    {
        items: [{
            source, id, userId, username, category, action, actionLabel,
            categoryLabel, detail, createdAt
        }],
        total, page, size
    }
    """
    try:
        offset = max(0, (page - 1) * size)

        # 构建 WHERE 条件
        sys_where = []
        llm_where = []
        all_params = {}

        if user_id:
            sys_where.append("o.user_id = :user_id")
            llm_where.append("r.user_id = :user_id")
            all_params["user_id"] = user_id
        if category:
            sys_where.append("o.category = :category")
            all_params["category"] = category
            # LLM 按 module 过滤
            llm_map = {"ADMIN": None, "AUTH": None, "DOCUMENT": None}
            if category in llm_map:
                llm_where.append("1=0")  # 不匹配任何 LLM 记录
            elif category == "QA":
                llm_where.append("r.module = 'QA'")
            elif category == "ASSISTANT":
                llm_where.append("r.module = 'ASSISTANT'")

        sys_cond = ("WHERE " + " AND ".join(sys_where)) if sys_where else ""
        llm_cond = ("WHERE " + " AND ".join(llm_where)) if llm_where else ""

        # 统一查询 — JOIN users 获取显示名
        sql = f"""
            SELECT * FROM (
                -- 系统操作
                SELECT 'SYS_OP'              AS source,
                       o.id,
                       o.user_id,
                       COALESCE(u1.display_name, o.username, '未知用户') AS username,
                       o.category,
                       o.action,
                       o.detail,
                       o.created_at
                FROM operation_logs o
                LEFT JOIN users u1 ON u1.id = o.user_id
                {sys_cond}

                UNION ALL

                -- LLM 调用
                SELECT 'LLM'                 AS source,
                       r.id,
                       r.user_id,
                       COALESCE(u2.display_name, u2.username, CAST(r.user_id AS text)) AS username,
                       r.module             AS category,
                       r.endpoint           AS action,
                       jsonb_build_object(
                           'model', COALESCE(r.model_name, ''),
                           'tokens', r.total_tokens,
                           'cost', ROUND(COALESCE(r.cost_amount, 0)::numeric, 4),
                           'success', r.success,
                           'latencyMs', r.latency_ms,
                           'endpoint', r.endpoint
                       ) AS detail,
                       r.created_at
                FROM llm_usage_records r
                LEFT JOIN users u2 ON u2.id = r.user_id
                {llm_cond}
            ) combined
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """

        all_params["limit"] = size
        all_params["offset"] = offset

        result = await db.execute(text(sql), all_params)
        rows = result.fetchall()

        items = []
        for row in rows:
            cat = row.category or ""
            act = row.action or ""
            items.append({
                "source": row.source,
                "id": row.id,
                "userId": row.user_id,
                "username": row.username or str(row.user_id),
                "category": cat,
                "action": act,
                "categoryLabel": CATEGORY_LABELS.get(cat, cat),
                "actionLabel": ACTION_LABELS.get(act, act),
                "detail": row.detail or {},
                "createdAt": row.created_at.isoformat() if row.created_at else "",
            })

        # 查询总数（简化版）
        total_sql = f"""
            SELECT (
                (SELECT COUNT(*) FROM operation_logs o {sys_cond}) +
                (SELECT COUNT(*) FROM llm_usage_records r {llm_cond})
            ) AS total
        """
        total_result = await db.execute(text(total_sql), all_params)
        total = total_result.scalar() or 0

        return ApiResponse.ok(data={
            "items": items,
            "total": total,
            "page": page,
            "size": size,
        })

    except Exception as e:
        logger.error(f"查询操作日志失败: {e}")
        return ApiResponse.ok(data={"items": [], "total": 0, "page": page, "size": size})
