"""
脚本名称: data_processor.py
功能: 读取本地 CSV/Excel 原始数据，清洗后存入 MongoDB 云数据库
运行方式: 在终端执行 python scripts/data_processor.py
"""

import pandas as pd
import toml
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# 1. 安全读取数据库密码 (因为脚本不在 streamlit 环境运行，需要手动读 secrets)
# 注意：为了方便脚本运行，我们临时用个小技巧读取 .streamlit/secrets.toml
def get_db_connection():
    try:
        # 定位 secrets.toml 文件的路径
        current_dir = os.path.dirname(os.path.abspath(__file__)) # scripts 目录
        project_root = os.path.dirname(current_dir)              # 项目根目录
        secrets_path = os.path.join(project_root, ".streamlit", "secrets.toml")
        
        # 读取文件
        config = toml.load(secrets_path)
        uri = config["mongo"]["uri"]
        
        # 连接 MongoDB
        client = MongoClient(uri, server_api=ServerApi('1'))
        client.admin.command('ping') # 测试连接
        print("✅ 数据库连接成功！")
        return client.pubg_sys # 返回数据库对象
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return None

def process_audio_features(db):
    """处理声音特征 CSV 数据 -> 存入 audio_features 表"""
    csv_path = "data/raw/test_selected_features.csv"
    
    if not os.path.exists(csv_path):
        print(f"⚠️ 未找到文件: {csv_path}，跳过声音数据导入。")
        return

    print(f"正在读取 {csv_path} ...")
    df = pd.read_csv(csv_path)
    
    # --- 数据探索与清洗 (Data Cleaning) ---
    # 这里可以展示给老师看：你检查了缺失值
    if df.isnull().sum().sum() > 0:
        print("发现缺失值，正在填充...")
        df = df.fillna(0)
    
    # 转换格式为字典列表
    data_dict = df.to_dict("records")
    
    # --- 存入数据库 ---
    # 为了演示，先清空旧数据（开发阶段常用，生产环境慎用）
    db.audio_features.delete_many({})
    print("旧声音特征数据已清空。")
    
    # 批量插入
    db.audio_features.insert_many(data_dict)
    print(f"🚀 成功导入 {len(data_dict)} 条声音特征数据！")
    
    # --- 自动生成武器图鉴 (根据 CSV 里的武器名) ---
    # 这是作业要求的“武器管理”基础数据
    unique_weapons = df['weapon'].unique()
    existing_weapons = db.game_weapons.distinct("name")
    
    new_weapons = []
    for w in unique_weapons:
        if w not in existing_weapons:
            # 构造一个初始的武器对象
            new_weapons.append({
                "name": w,
                "type": "Unknown", # 以后在网页端修改
                "damage": 0,       # 以后在网页端修改
                "ammo_type": "N/A"
            })
    
    if new_weapons:
        db.game_weapons.insert_many(new_weapons)
        print(f"🔫 自动在这个 game_weapons 表中补充了 {len(new_weapons)} 种新武器：{unique_weapons}")

if __name__ == "__main__":
    # 主程序入口
    db = get_db_connection()
    if db is not None:
        # 执行导入逻辑
        process_audio_features(db)
        print("\n🎉 数据初始化脚本运行结束！")