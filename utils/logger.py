"""日志与审计

这里分两层：
1) 控制台日志：方便开发时看运行情况（logging logger）。
2) 审计日志：写入 MongoDB 的 logs 集合，记录“谁在什么时候做了什么”。

注意：这个模块既会被 Streamlit UI 调用，也会被 FastAPI 后端调用。
所以不要在这里做 UI 相关依赖（比如 st.*），保持它纯粹。
"""

import logging
from datetime import datetime

# --- 1. 系统级日志配置 (控制台输出) ---
# 防止重复配置：在 Streamlit/FastAPI 的热重载环境下，模块可能被重复 import。
logger = logging.getLogger("PUBG_System")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # 输出到控制台
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

def get_logger():
    """获取系统日志记录器"""
    return logger

# --- 2. 业务审计日志 (写入 MongoDB) ---
def log_action(db, user_id, action_type, details=None, level="INFO"):
    """
    记录用户操作到数据库
    :param db: 数据库连接对象
    :param user_id: 操作者ID (学号)
    :param action_type: 动作类型 (如 LOGIN, ADD_ITEM, AI_PREDICT)
    :param details: 详细信息 (字典或字符串)
    :param level: 日志级别 (INFO, WARN, ERROR)
    """
    # 这里不 raise：
    # - 日志写入失败不应该让主流程崩掉（比如用户正常下单/分析不该因为日志挂了就失败）
    # - 但会在控制台输出 error，便于排查
    if db is None:
        logger.error("无法写入审计日志：数据库连接为空")
        return

    # 建议：后续可以在 logs 上建索引（timestamp/user_id/action），便于检索。
    log_entry = {
        "timestamp": datetime.now(),
        "user_id": user_id,
        "action": action_type,
        "level": level,
        "details": details or {}
    }

    try:
        db.logs.insert_one(log_entry)
        # 同时打印到控制台方便开发调试
        logger.info(f"[{user_id}] {action_type}: {details}")
    except Exception as e:
        logger.error(f"写入审计日志失败: {e}")