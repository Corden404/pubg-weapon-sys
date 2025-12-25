"""
脚本名称: update_weapon_stats.py
功能: 批量更新数据库，补充武器的详细属性（射速、射程、弹药等）
"""

import os
import toml
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# 1. 详细的武器数据 (由 AI 生成，参考 PUBG Wiki)
# 键必须与数据库里的 'name' 字段匹配 (注意大小写，如果不匹配脚本会自动跳过)
WEAPON_DATA = {
    "ak": {
        "full_name": "AKM",
        "type": "突击步枪",
        "damage": 47,
        "ammo_type": "7.62mm",
        "stats": {"headshot_rate": 2.3, "fire_rate": 0.100, "range": 400, "mag_size": 30, "reload_time": 2.9}
    },
    "m4": {
        "full_name": "M416",
        "type": "突击步枪",
        "damage": 41,
        "ammo_type": "5.56mm",
        "stats": {"headshot_rate": 2.3, "fire_rate": 0.086, "range": 600, "mag_size": 30, "reload_time": 2.1}
    },
    "m16": {
        "full_name": "M16A4",
        "type": "突击步枪",
        "damage": 43,
        "ammo_type": "5.56mm",
        "stats": {"headshot_rate": 2.3, "fire_rate": 0.075, "range": 600, "mag_size": 30, "reload_time": 2.2}
    },
    "scar": {
        "full_name": "SCAR-L",
        "type": "突击步枪",
        "damage": 41,
        "ammo_type": "5.56mm",
        "stats": {"headshot_rate": 2.3, "fire_rate": 0.096, "range": 600, "mag_size": 30, "reload_time": 2.2}
    },
    "gro": {
        "full_name": "Groza",
        "type": "突击步枪",
        "damage": 47,
        "ammo_type": "7.62mm",
        "stats": {"headshot_rate": 2.3, "fire_rate": 0.080, "range": 400, "mag_size": 30, "reload_time": 3.0}
    },
    "aug": {
        "full_name": "AUG A3",
        "type": "突击步枪",
        "damage": 41,
        "ammo_type": "5.56mm",
        "stats": {"headshot_rate": 2.3, "fire_rate": 0.085, "range": 600, "mag_size": 30, "reload_time": 3.0}
    },
    "g36c": {
        "full_name": "G36C",
        "type": "突击步枪",
        "damage": 41,
        "ammo_type": "5.56mm",
        "stats": {"headshot_rate": 2.3, "fire_rate": 0.085, "range": 600, "mag_size": 30, "reload_time": 2.5}
    },
    "k2": {
        "full_name": "K2",
        "type": "突击步枪",
        "damage": 43,
        "ammo_type": "5.56mm",
        "stats": {"headshot_rate": 2.3, "fire_rate": 0.088, "range": 550, "mag_size": 30, "reload_time": 2.4}
    },
    "qbz": {
        "full_name": "QBZ95",
        "type": "突击步枪",
        "damage": 42,
        "ammo_type": "5.56mm",
        "stats": {"headshot_rate": 2.3, "fire_rate": 0.090, "range": 500, "mag_size": 30, "reload_time": 2.3}
    },
    "kar": {
        "full_name": "Kar98k",
        "type": "栓动狙击枪",
        "damage": 79,
        "ammo_type": "7.62mm",
        "stats": {"headshot_rate": 2.5, "fire_rate": 1.900, "range": 500, "mag_size": 5, "reload_time": 4.0}
    },
    "m24": {
        "full_name": "M24",
        "type": "栓动狙击枪",
        "damage": 75,
        "ammo_type": "7.62mm",
        "stats": {"headshot_rate": 2.5, "fire_rate": 1.800, "range": 800, "mag_size": 5, "reload_time": 4.2}
    },
    "awm": {
        "full_name": "AWM",
        "type": "栓动狙击枪",
        "damage": 105,
        "ammo_type": ".300 Magnum",
        "stats": {"headshot_rate": 2.5, "fire_rate": 1.850, "range": 1000, "mag_size": 5, "reload_time": 4.6}
    },
    "win": {
        "full_name": "Winchester",
        "type": "栓动狙击枪",
        "damage": 72,
        "ammo_type": ".45ACP",
        "stats": {"headshot_rate": 2.5, "fire_rate": 1.200, "range": 300, "mag_size": 8, "reload_time": 3.5}
    },
    "sks": {
        "full_name": "SKS",
        "type": "射手步枪",
        "damage": 53,
        "ammo_type": "7.62mm",
        "stats": {"headshot_rate": 2.3, "fire_rate": 0.090, "range": 800, "mag_size": 10, "reload_time": 2.9}
    },
    "mini": {
        "full_name": "Mini14",
        "type": "射手步枪",
        "damage": 46,
        "ammo_type": "5.56mm",
        "stats": {"headshot_rate": 2.3, "fire_rate": 0.100, "range": 700, "mag_size": 20, "reload_time": 3.6}
    },
    "vss": {
        "full_name": "VSS Vintorez",
        "type": "射手步枪",
        "damage": 41,
        "ammo_type": "9mm",
        "stats": {"headshot_rate": 2.3, "fire_rate": 0.086, "range": 200, "mag_size": 10, "reload_time": 2.9}
    },
    "slr": {
        "full_name": "SLR",
        "type": "射手步枪",
        "damage": 58,
        "ammo_type": "7.62mm",
        "stats": {"headshot_rate": 2.3, "fire_rate": 0.100, "range": 800, "mag_size": 10, "reload_time": 3.2}
    },
    "qbu": {
        "full_name": "QBU-88",
        "type": "射手步枪",
        "damage": 48,
        "ammo_type": "5.56mm",
        "stats": {"headshot_rate": 2.3, "fire_rate": 0.095, "range": 600, "mag_size": 10, "reload_time": 3.0}
    },
    "mk": {
        "full_name": "Mk14",
        "type": "射手步枪",
        "damage": 61,
        "ammo_type": "7.62mm",
        "stats": {"headshot_rate": 2.3, "fire_rate": 0.085, "range": 800, "mag_size": 10, "reload_time": 3.5}
    },
    "ump": {
        "full_name": "UMP45",
        "type": "冲锋枪",
        "damage": 39,
        "ammo_type": ".45ACP",
        "stats": {"headshot_rate": 1.8, "fire_rate": 0.092, "range": 300, "mag_size": 25, "reload_time": 3.1}
    },
    "uzi": {
        "full_name": "Micro UZI",
        "type": "冲锋枪",
        "damage": 26,
        "ammo_type": "9mm",
        "stats": {"headshot_rate": 1.8, "fire_rate": 0.048, "range": 200, "mag_size": 25, "reload_time": 3.1}
    },
    "vec": {
        "full_name": "Vector",
        "type": "冲锋枪",
        "damage": 31,
        "ammo_type": "9mm",
        "stats": {"headshot_rate": 1.8, "fire_rate": 0.055, "range": 150, "mag_size": 19, "reload_time": 2.2}
    },
    "p90": {
        "full_name": "P90",
        "type": "冲锋枪",
        "damage": 35,
        "ammo_type": "5.7mm",
        "stats": {"headshot_rate": 2.0, "fire_rate": 0.050, "range": 300, "mag_size": 50, "reload_time": 3.5}
    },
    "tommy": {
        "full_name": "Thompson",
        "type": "冲锋枪",
        "damage": 40,
        "ammo_type": ".45ACP",
        "stats": {"headshot_rate": 1.8, "fire_rate": 0.086, "range": 250, "mag_size": 30, "reload_time": 3.3}
    },
    "s12k": {
        "full_name": "S12K",
        "type": "散弹枪",
        "damage": 22,
        "ammo_type": "12 Gauge",
        "stats": {"headshot_rate": 1.5, "fire_rate": 0.250, "range": 50, "mag_size": 5, "reload_time": 3.0}
    },
    "dbs": {
        "full_name": "DBS",
        "type": "散弹枪",
        "damage": 26,
        "ammo_type": "12 Gauge",
        "stats": {"headshot_rate": 1.5, "fire_rate": 0.100, "range": 50, "mag_size": 14, "reload_time": 2.5}
    },
    "pump": {
        "full_name": "S1897",
        "type": "散弹枪",
        "damage": 24,
        "ammo_type": "12 Gauge",
        "stats": {"headshot_rate": 1.5, "fire_rate": 0.750, "range": 50, "mag_size": 5, "reload_time": 3.2}
    },
    "m249": {
        "full_name": "M249",
        "type": "轻机枪",
        "damage": 45,
        "ammo_type": "5.56mm",
        "stats": {"headshot_rate": 2.3, "fire_rate": 0.075, "range": 600, "mag_size": 100, "reload_time": 5.0}
    },
    "dp": {
        "full_name": "DP-28",
        "type": "轻机枪",
        "damage": 51,
        "ammo_type": "7.62mm",
        "stats": {"headshot_rate": 2.3, "fire_rate": 0.100, "range": 400, "mag_size": 47, "reload_time": 3.5}
    },
    "p18c": {
        "full_name": "P18C",
        "type": "手枪",
        "damage": 23,
        "ammo_type": "9mm",
        "stats": {"headshot_rate": 2.0, "fire_rate": 0.060, "range": 50, "mag_size": 17, "reload_time": 2.0}
    },
    "p92": {
        "full_name": "P92",
        "type": "手枪",
        "damage": 35,
        "ammo_type": "9mm",
        "stats": {"headshot_rate": 2.0, "fire_rate": 0.080, "range": 50, "mag_size": 15, "reload_time": 2.0}
    },
    "p1911": {
        "full_name": "P1911",
        "type": "手枪",
        "damage": 41,
        "ammo_type": ".45ACP",
        "stats": {"headshot_rate": 2.0, "fire_rate": 0.075, "range": 50, "mag_size": 7, "reload_time": 2.0}
    },
    "r1895": {
        "full_name": "R1895",
        "type": "手枪",
        "damage": 55,
        "ammo_type": "7.62mm",
        "stats": {"headshot_rate": 2.0, "fire_rate": 1.000, "range": 100, "mag_size": 7, "reload_time": 4.0}
    },
    "r45": {
        "full_name": "R45",
        "type": "手枪",
        "damage": 55,
        "ammo_type": ".45ACP",
        "stats": {"headshot_rate": 2.0, "fire_rate": 0.900, "range": 100, "mag_size": 6, "reload_time": 3.5}
    },
    "deagle": {
        "full_name": "Desert Eagle",
        "type": "手枪",
        "damage": 62,
        "ammo_type": ".45ACP",
        "stats": {"headshot_rate": 2.0, "fire_rate": 0.800, "range": 150, "mag_size": 7, "reload_time": 2.5}
    },
    "scorp": {
        "full_name": "Skorpion",
        "type": "手枪",
        "damage": 22,
        "ammo_type": "9mm",
        "stats": {"headshot_rate": 1.8, "fire_rate": 0.070, "range": 100, "mag_size": 20, "reload_time": 2.8}
    },
    "verl": {
        "full_name": "Vera Lynn",
        "type": "精确射手步枪",
        "damage": 56,
        "ammo_type": "7.62mm",
        "stats": {"headshot_rate": 2.3, "fire_rate": 0.110, "range": 700, "mag_size": 10, "reload_time": 3.2}
    },
    "pp": {
        "full_name": "PP-19 Bizon",
        "type": "冲锋枪",
        "damage": 35,
        "ammo_type": "9mm",
        "stats": {"headshot_rate": 1.8, "fire_rate": 0.080, "range": 250, "mag_size": 53, "reload_time": 3.0}
    },
    "nogun": {
        "full_name": "No Gun",
        "type": "近战武器",
        "damage": 60,
        "ammo_type": "N/A",
        "stats": {"headshot_rate": 1.5, "fire_rate": 0.250, "range": 50, "mag_size": 5, "reload_time": 3.0}
    }
}

def get_db_connection():
    """获取数据库连接 (复用 data_processor.py 的逻辑)"""
    try:
        # 寻找 secrets.toml
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        secrets_path = os.path.join(project_root, ".streamlit", "secrets.toml")
        
        config = toml.load(secrets_path)
        uri = config["mongo"]["uri"]
        return MongoClient(uri, server_api=ServerApi('1')).pubg_sys
    except Exception as e:
        print(f"连接失败: {e}")
        return None

def update_database():
    db = get_db_connection()
    if db is None: return

    print("开始批量更新武器详细属性...")
    
    updated_count = 0
    
    # 遍历我们准备好的数据
    for short_name, data in WEAPON_DATA.items():
        # 在数据库中查找 (因为之前 CSV 导入的 name 可能是 'ak', 'm4' 这种简写)
        # 我们尝试匹配 'name' 字段
        
        # 构造要更新的数据
        update_fields = {
            "type": data["type"],
            "damage": data["damage"],
            "ammo_type": data["ammo_type"],
            "stats": data["stats"],
            "full_name": data["full_name"] # 增加一个全名字段，界面显示更漂亮
        }
        
        # 执行更新
        # 这里的逻辑是：如果数据库里的 name 是 'ak'，我们就更新它
        result = db.game_weapons.update_one(
            {"name": short_name}, 
            {"$set": update_fields}
        )
        
        if result.matched_count > 0:
            print(f"已更新: {short_name} -> {data['full_name']}")
            updated_count += 1
        else:
            print(f"跳过: 数据库中没找到名为 '{short_name}' 的武器")

    print(f"\n更新完成！共更新了 {updated_count} 把武器的数据。")

if __name__ == "__main__":
    update_database()