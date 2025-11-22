import streamlit as st
import hashlib
import os  # <--- 必须引入 os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

@st.cache_resource
def init_connection():
    """初始化 MongoDB 连接 (支持 环境变量 和 secrets.toml 双模式)"""
    uri = None
    
    try:
        # 1. 优先尝试读取系统环境变量 (对应 Codespaces Secrets 或 Hugging Face Secrets)
        # 注意：你需要确保在 Codespaces 设置里 Secret 的名字叫 MONGO_URI
        if "MONGO_URI" in os.environ:
            uri = os.environ["MONGO_URI"]
            # print("✅ 使用环境变量连接") # 调试用
            
        # 2. 如果环境变量里没有，再尝试读取本地 secrets.toml 文件
        elif hasattr(st, "secrets") and "mongo" in st.secrets:
            uri = st.secrets["mongo"]["uri"]
            # print("✅ 使用本地 secrets.toml 连接") # 调试用
            
        # 3. 如果两边都没找到
        if uri is None:
            st.error("❌ 未找到数据库配置！请检查 .streamlit/secrets.toml 或 环境变量 MONGO_URI")
            return None

        return MongoClient(uri, server_api=ServerApi('1'))

    except Exception as e:
        st.error(f"数据库连接异常: {e}")
        return None

def get_db():
    """获取数据库实例的快捷方式"""
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