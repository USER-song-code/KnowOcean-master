"""从 prompts/ 目录加载提示词模板

所有 .st 文件使用 {variable} 占位符，与 Python .format() 兼容。
"""
from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _read(name: str) -> str:
    path = _PROMPTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    return path.read_text(encoding="utf-8").strip()


# QA 问答提示词
QA_SYSTEM = _read("qa/system.st")
QA_USER = _read("qa/user.st")
QA_RAG_CONTEXT = _read("qa/rag-context.st")

# 查询规划提示词
QUERY_PLANNING_USER = _read("query-planning/user.st")

# AI 助手提示词（后续使用）
ASSISTANT_RUNTIME_COMPACT = _read("assistant/runtime-compact-summary.st")
ASSISTANT_SESSION_COMPACT = _read("assistant/session-compact-summary.st")
ASSISTANT_SESSION_MEMORY = _read("assistant/session-memory-update.st")
