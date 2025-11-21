import streamlit as st
import pandas as pd
import hashlib
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime

# ==========================================
# 1. 基础配置与工具函数
# ==========================================
st.set_page_config(page_title="PUBG 武器管理系统", page_icon="🔫", layout="wide")

@st.cache_resource
def init_connection():
    """连接数据库"""
    try:
        uri = st.secrets["mongo"]["uri"]
        return MongoClient(uri, server_api=ServerApi('1'))
    except Exception as e:
        st.error(f"数据库连接失败: {e}")
        return None

def make_hash(password):
    """对密码进行 SHA256 加密 (作业加分项: 密码加密保存)"""
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    """校验密码"""
    if make_hash(password) == hashed_text:
        return True
    return False

# 初始化数据库
client = init_connection()
if not client:
    st.stop()
db = client.pubg_sys

# ==========================================
# 2. 身份验证模块 (Authentication)
# ==========================================
def login_page():
    st.header("🔐 PUBG 系统登录")
    
    tab1, tab2 = st.tabs(["登录", "注册新玩家"])
    
    with tab1:
        username = st.text_input("学号 (Student ID)")
        password = st.text_input("密码", type='password') # 作业要求: 密码遮蔽
        
        if st.button("登录"):
            user = db.users.find_one({"student_id": username})
            if user:
                if check_hashes(password, user['password']):
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = user
                    st.session_state['username'] = username
                    st.success("登录成功！")
                    st.rerun()
                else:
                    st.error("密码错误")
            else:
                st.error("该学号未注册")

    with tab2:
        new_user = st.text_input("输入学号注册")
        new_pass = st.text_input("设置密码", type='password')
        
        if st.button("注册"):
            if db.users.find_one({"student_id": new_user}):
                st.warning("该学号已存在！")
            else:
                # 创建新用户结构
                user_data = {
                    "student_id": new_user,
                    "password": make_hash(new_pass),
                    "inventory": [], # 初始背包为空
                    "created_at": datetime.now()
                }
                db.users.insert_one(user_data)
                st.success("注册成功！请切换到登录标签进行登录。")

# ==========================================
# 3. 主应用程序 (登录后可见)
# ==========================================
def main_app():
    user = st.session_state['user_info']
    
    # 侧边栏：用户信息
    with st.sidebar:
        st.write(f"👤 当前玩家: **{user['student_id']}**")
        if st.button("退出登录"):
            st.session_state['logged_in'] = False
            st.rerun()
        st.divider()
        st.info("💡 提示：去'武器图鉴'把枪添加到你的背包里。")

    st.title("🔫 PUBG 武器指挥中心")
    
    # 页面分栏
    tab_inventory, tab_catalog, tab_admin = st.tabs(["🎒 我的背包", "📚 武器图鉴(全)", "🛠️ 管理员修改"])

    # --- TAB 1: 我的背包 (Inventory) ---
    with tab_inventory:
        # 实时从数据库拉取最新的用户信息
        current_user = db.users.find_one({"student_id": user['student_id']})
        inventory = current_user.get('inventory', [])
        
        if not inventory:
            st.warning("你的背包是空的！快去'武器图鉴'进货吧。")
        else:
            # 转换为 DataFrame 展示
            df_inv = pd.DataFrame(inventory)
            st.dataframe(df_inv, use_container_width=True)
            
            # 作业要求: 统计剩余子弹
            total_ammo = df_inv['ammo_count'].sum()
            
            col1, col2 = st.columns(2)
            col1.metric("携带武器数量", len(inventory))
            col2.metric("剩余子弹总数", total_ammo)
            
            # 功能: 丢弃武器
            weapon_to_remove = st.selectbox("选择要丢弃的武器", [item['weapon_name'] for item in inventory])
            if st.button("🗑️ 丢弃选中武器"):
                db.users.update_one(
                    {"student_id": user['student_id']},
                    {"$pull": {"inventory": {"weapon_name": weapon_to_remove}}}
                )
                st.success(f"已丢弃 {weapon_to_remove}")
                st.rerun()

    # --- TAB 2: 武器图鉴 (Global Catalog) ---
    with tab_catalog:
        st.subheader("武器库总览")
        # 读取公共武器库
        weapons = list(db.game_weapons.find({}, {"_id": 0})) # 不显示 _id
        df_weapons = pd.DataFrame(weapons)
        
        # 作业要求: 排序与筛选
        sort_col = st.selectbox("排序依据", ["damage", "name", "type"])
        df_sorted = df_weapons.sort_values(by=sort_col, ascending=False)
        
        st.dataframe(df_sorted, use_container_width=True)
        
        st.divider()
        st.write("### 📥 装备武器")
        col_add1, col_add2 = st.columns(2)
        with col_add1:
            selected_weapon = st.selectbox("选择一把武器加入背包", df_sorted['name'].unique())
        with col_add2:
            ammo_count = st.number_input("携带子弹数量", min_value=1, value=30)
        
        if st.button("放入背包"):
            # 构建背包物品数据
            item = {
                "weapon_name": selected_weapon,
                "ammo_count": ammo_count,
                "added_at": datetime.now()
            }
            # 更新数据库
            db.users.update_one(
                {"student_id": user['student_id']},
                {"$push": {"inventory": item}}
            )
            st.toast(f"✅ {selected_weapon} 已加入背包！")

    # --- TAB 3: 管理员修改 (CRUD) ---
    with tab_admin:
        st.warning("⚠️ 这里修改的是全局游戏数据，会影响所有玩家！")
        
        # 选择要修改的武器
        edit_target = st.selectbox("选择要修改数据的武器", df_weapons['name'].unique())
        
        # 获取当前数据
        current_data = db.game_weapons.find_one({"name": edit_target})
        
        with st.form("edit_form"):
            new_damage = st.number_input("修改伤害 (Damage)", value=int(current_data.get('damage', 0)))
            new_type = st.text_input("修改类型 (Type)", value=current_data.get('type', 'Unknown'))
            
            if st.form_submit_button("💾 保存修改"):
                db.game_weapons.update_one(
                    {"name": edit_target},
                    {"$set": {"damage": new_damage, "type": new_type}}
                )
                st.success(f"{edit_target} 数据已更新！")
                st.rerun()

# ==========================================
# 4. 程序入口控制
# ==========================================
# 检查 Session 状态，判断显示登录页还是主页
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login_page()
else:
    main_app()