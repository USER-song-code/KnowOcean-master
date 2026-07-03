"""模型定价配置与费用计算

定价单位为 CNY（人民币）每百万 tokens。
实际部署时应根据模型供应商的最新报价更新。
"""
from decimal import Decimal

# 每百万 tokens 的单价（CNY）
MODEL_PRICING: dict[str, dict[str, float]] = {
    "deepseek-v4-pro":    {"prompt": 2.0,  "completion": 8.0},
    "deepseek-v3":        {"prompt": 1.0,  "completion": 4.0},
    "qwen-plus":          {"prompt": 0.8,  "completion": 2.0},
    "qwen-max":           {"prompt": 2.0,  "completion": 6.0},
    "qwen-turbo":         {"prompt": 0.3,  "completion": 0.6},
    "text-embedding-v3":  {"prompt": 0.7,  "completion": 0.0},
    "_default":           {"prompt": 2.0,  "completion": 8.0},
}


def calculate_cost(model_name: str | None, prompt_tokens: int, completion_tokens: int) -> Decimal:
    """根据模型名称和 token 用量计算费用（CNY）。

    Args:
        model_name: LLM 模型名称，为 None 时使用默认价格
        prompt_tokens: 输入 token 数
        completion_tokens: 输出 token 数

    Returns:
        Decimal 类型的费用金额，保留 6 位小数
    """
    pricing = MODEL_PRICING.get(model_name or "", MODEL_PRICING["_default"])
    prompt_cost = (prompt_tokens / 1_000_000) * pricing["prompt"]
    completion_cost = (completion_tokens / 1_000_000) * pricing["completion"]
    return Decimal(str(round(prompt_cost + completion_cost, 6)))
