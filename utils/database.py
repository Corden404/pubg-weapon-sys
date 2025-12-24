"""MongoDB 连接与密码工具

这个模块最早是给 Streamlit UI 用的，所以使用了 st.cache_resource 做连接缓存。
目前 FastAPI 后端也直接复用同一套 get_db()，因此你需要保证：

- 运行 Web/后端时，环境变量里有 MONGO_URI，或项目里存在 .streamlit/secrets.toml
- MongoDB 数据库名固定为 pubg_sys

如果未来把后端单独部署（不带 Streamlit），建议把“后端版 get_db”拆出来，
避免在服务端进程里引入 streamlit（体积/行为都没必要）。
"""

import streamlit as st
import hashlib
import os  # <--- 必须引入 os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

@st.cache_resource
def init_connection():
    """初始化 MongoDB 连接 (支持 环境变量 和 secrets.toml 双模式)

    这里返回的是 MongoClient（连接池），而不是 db 实例。
    Streamlit 会对这个资源做缓存，避免每次 rerun 都重新连数据库。
    """
    uri = None
    
    try:
        # 1) 优先用环境变量：便于部署/CI，不需要把密钥写进仓库。
        #    （Codespaces / 服务器环境一般都推荐这种方式）
        if "MONGO_URI" in os.environ:
            uri = os.environ["MONGO_URI"]
            # print("✅ 使用环境变量连接") # 调试用
            
        # 2) 其次用 Streamlit 的 secrets.toml：适合本地/课堂演示。
        elif hasattr(st, "secrets") and "mongo" in st.secrets:
            uri = st.secrets["mongo"]["uri"]
            # print("✅ 使用本地 secrets.toml 连接") # 调试用
            
        # 3) 两边都没找到就直接报错：没有 DB 连接，一切功能都跑不起来。
        if uri is None:
            st.error("❌ 未找到数据库配置！请检查 .streamlit/secrets.toml 或 环境变量 MONGO_URI")
            return None

        return MongoClient(uri, server_api=ServerApi('1'))

    except Exception as e:
        st.error(f"数据库连接异常: {e}")
        return None

def get_db():
    """获取数据库实例的快捷方式

    返回 client.pubg_sys 这个 database handle。
    约定：所有集合（users/game_weapons/logs/audio_features）都在这个库里。
    """
    client = init_connection()
    if client is not None:  # <--- 必须显式判断 is not None
        return client.pubg_sys
    return None

def make_hash(password):
    """SHA256 加密"""
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    """密码校验"""
    return make_hash(password) == hashed_text