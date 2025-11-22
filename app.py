import streamlit as st
import pandas as pd
import hashlib
import os
import joblib
import numpy as np
import librosa
from datetime import datetime
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# ==========================================
# 0. 全局配置
# ==========================================
st.set_page_config(
    page_title="PUBG 武器管理与识别系统",
    page_icon="🔫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 1. 核心工具函数 (数据库 & AI)
# ==========================================

@st.cache_resource
def init_connection():
    """初始化 MongoDB 连接"""
    try:
        # 从 secrets.toml 读取配置
        uri = st.secrets["mongo"]["uri"]
        return MongoClient(uri, server_api=ServerApi('1'))
    except Exception as e:
        st.error(f"数据库连接失败: {e}")
        return None

@st.cache_resource
def load_model():
    """加载训练好的 AI 模型"""
    model_path = "data/processed/weapon_classifier.pkl"
    if os.path.exists(model_path):
        try:
            return joblib.load(model_path)
        except Exception as e:
            st.error(f"模型文件损坏: {e}")
            return None
    return None

def extract_features_for_prediction(audio_file):
    """
    AI 核心：提取音频特征
    注意：必须与训练脚本 (extract_features.py) 的逻辑完全一致
    """
    SAMPLE_RATE = 22050
    DURATION = 2.0
    N_MFCC = 13
    
    try:
        # librosa 可以直接读取 streamlit 上传的文件对象
        y, sr = librosa.load(audio_file, sr=SAMPLE_RATE, duration=DURATION)
        
        # 填充 (Padding) - 如果音频短于 2 秒
        if len(y) < SAMPLE_RATE * DURATION:
            padding = int(SAMPLE_RATE * DURATION) - len(y)
            y = np.pad(y, (0, padding), 'constant')

        # 提取特征 (顺序必须严格一致: ZCR -> RMS -> Centroid -> MFCC)
        zcr = np.mean(librosa.feature.zero_crossing_rate(y))
        rms = np.mean(librosa.feature.rms(y=y))
        cent = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
        mfcc_mean = np.mean(mfcc, axis=1)
        
        # 组装特征向量
        features = [zcr, rms, cent]
        features.extend(mfcc_mean)
        
        # 返回二维数组 (1, N_features) 以符合 scikit-learn 输入格式
        return np.array([features]) 
    except Exception as e:
        st.error(f"特征提取失败: {e}")
        return None

def make_hash(password):
    """密码加密 (SHA256)"""
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    """密码校验"""
    if make_hash(password) == hashed_text:
        return True
    return False

# 初始化资源
client = init_connection()
if not client:
    st.stop()
db = client.pubg_sys

# ==========================================
# 2. 登录与注册界面
# ==========================================
def login_page():
    st.markdown("<h1 style='text-align: center;'>🔐 PUBG 综合实训系统</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["登录账号", "注册新用户"])
        
        with tab1:
            username = st.text_input("学号 (Student ID)")
            password = st.text_input("密码", type='password')
            
            if st.button("登录", use_container_width=True):
                user = db.users.find_one({"student_id": username})
                if user:
                    if check_hashes(password, user['password']):
                        # 设置 Session 状态
                        st.session_state['logged_in'] = True
                        st.session_state['user_info'] = user
                        st.session_state['username'] = username
                        st.success("登录成功！")
                        st.rerun()
                    else:
                        st.error("❌ 密码错误")
                else:
                    st.error("❌ 该学号未注册")

        with tab2:
            new_user = st.text_input("输入学号注册")
            new_pass = st.text_input("设置密码", type='password')
            confirm_pass = st.text_input("确认密码", type='password')
            
            if st.button("立即注册", use_container_width=True):
                if new_pass != confirm_pass:
                    st.error("两次密码输入不一致")
                elif db.users.find_one({"student_id": new_user}):
                    st.warning("该学号已存在！")
                else:
                    user_data = {
                        "student_id": new_user,
                        "password": make_hash(new_pass),
                        "inventory": [],
                        "created_at": datetime.now()
                    }
                    db.users.insert_one(user_data)
                    st.success("✅ 注册成功！请切换到登录标签进行登录。")

# ==========================================
# 3. 主应用程序 (登录后)
# ==========================================
def main_app():
    user = st.session_state['user_info']
    
    # --- 侧边栏 ---
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/pubg.png", width=80)
        st.write(f"👋 欢迎回来, **{user['student_id']}**")
        
        st.divider()
        if st.button("🚪 退出登录", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()
            
        st.info("提示：\n1. 在'武器图鉴'添加装备\n2. 在'声音识别'测试模型")

    st.title("🔫 PUBG 武器指挥中心")
    
    # --- 主要功能区 ---
    tab_inventory, tab_catalog, tab_admin, tab_ai = st.tabs([
        "🎒 我的背包", 
        "📚 武器图鉴", 
        "🛠️ 管理员", 
        "🎙️ 声音识别(AI)"
    ])

    # TAB 1: 背包系统
    with tab_inventory:
        # 实时拉取数据
        current_user = db.users.find_one({"student_id": user['student_id']})
        inventory = current_user.get('inventory', [])
        
        if not inventory:
            st.info("🎒 背包空空如也，快去进货吧！")
        else:
            # 统计数据
            df_inv = pd.DataFrame(inventory)
            total_ammo = df_inv['ammo_count'].sum()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("武器数量", len(inventory))
            c2.metric("总弹药量", total_ammo)
            c3.metric("最后更新", datetime.now().strftime("%H:%M"))
            
            st.dataframe(df_inv, use_container_width=True)
            
            # 丢弃功能
            with st.expander("🗑️ 丢弃武器"):
                weapon_to_remove = st.selectbox("选择要丢弃的物品", [item['weapon_name'] for item in inventory])
                if st.button("确认丢弃"):
                    db.users.update_one(
                        {"student_id": user['student_id']},
                        {"$pull": {"inventory": {"weapon_name": weapon_to_remove}}}
                    )
                    st.success(f"已丢弃 {weapon_to_remove}")
                    st.rerun()

    # TAB 2: 武器图鉴
    with tab_catalog:
        weapons = list(db.game_weapons.find({}, {"_id": 0}))
        if not weapons:
            st.warning("数据库中没有武器数据，请先运行 data_processor.py 脚本导入数据。")
        else:
            df_weapons = pd.DataFrame(weapons)
            
            col_sort, col_search = st.columns(2)
            with col_sort:
                sort_col = st.selectbox("排序方式", ["damage", "name", "type"])
            with col_search:
                search_term = st.text_input("🔍 搜索武器", "")
            
            # 筛选逻辑
            if search_term:
                df_weapons = df_weapons[df_weapons['name'].str.contains(search_term, case=False)]
            
            df_sorted = df_weapons.sort_values(by=sort_col, ascending=False)
            st.dataframe(df_sorted, use_container_width=True)
            
            st.divider()
            st.write("### 📥 装备补给")
            c1, c2 = st.columns([2, 1])
            with c1:
                selected_weapon = st.selectbox("选择武器", df_sorted['name'].unique())
            with c2:
                ammo_count = st.number_input("子弹数量", min_value=1, value=30)
            
            if st.button("放入背包", type="primary"):
                item = {
                    "weapon_name": selected_weapon,
                    "ammo_count": ammo_count,
                    "added_at": datetime.now()
                }
                db.users.update_one(
                    {"student_id": user['student_id']},
                    {"$push": {"inventory": item}}
                )
                st.toast(f"✅ {selected_weapon} 已加入背包！")

    # TAB 3: 管理员
    with tab_admin:
        st.warning("⚠️ 管理员区域：修改将影响所有玩家的图鉴数据")
        if weapons:
            edit_target = st.selectbox("选择要编辑的武器", df_weapons['name'].unique())
            current_data = db.game_weapons.find_one({"name": edit_target})
            
            with st.form("admin_form"):
                c1, c2 = st.columns(2)
                with c1:
                    new_damage = st.number_input("伤害数值", value=int(current_data.get('damage', 0)))
                with c2:
                    new_type = st.text_input("武器类型", value=current_data.get('type', 'Unknown'))
                
                if st.form_submit_button("💾 保存更改"):
                    db.game_weapons.update_one(
                        {"name": edit_target},
                        {"$set": {"damage": new_damage, "type": new_type}}
                    )
                    st.success("更新成功！")
                    st.rerun()

    # TAB 4: AI 声音识别 (增加距离和方位)
    with tab_ai:
        st.header("🤖 智能枪声识别 (Level B - 多任务)")
        
        package = load_model() # 加载回来的是那个大字典
        if package is None:
            st.error("❌ 未检测到模型文件！请先运行 'scripts/train_model.py'")
        else:
            # 获取模型字典
            models = package['models']
            feature_names = package['feature_names']
            
            st.success(f"✅ 多任务模型已加载 (支持: 武器/距离/方位)")
            
            uploaded_audio = st.file_uploader("上传 MP3 录音文件", type=["mp3"])
            
            if uploaded_audio is not None:
                st.audio(uploaded_audio, format='audio/mp3')
                
                if st.button("🔍 全方位分析", type="primary"):
                    with st.spinner("正在进行多维度推理..."):
                        # 1. 提取特征
                        X_input = extract_features_for_prediction(uploaded_audio)
                        
                        if X_input is not None:
                            # 2. 分别预测三个任务
                            pred_weapon = models['weapon'].predict(X_input)[0]
                            pred_dist = models['distance'].predict(X_input)[0]
                            pred_dir = models['direction'].predict(X_input)[0]
                            
                            # 获取武器的置信度
                            prob_weapon = np.max(models['weapon'].predict_proba(X_input)[0])
                            
                            # 3. 结果展示 (三列布局)
                            st.divider()
                            st.subheader("🎯 分析报告")
                            
                            c1, c2, c3 = st.columns(3)
                            
                            with c1:
                                st.info("🔫 武器型号")
                                st.markdown(f"### {pred_weapon}")
                                st.caption(f"置信度: {prob_weapon:.1%}")
                            
                            with c2:
                                st.warning("📏 射击距离")
                                st.markdown(f"### {pred_dist}")
                            
                            with c3:
                                st.success("🧭 射击方位")
                                st.markdown(f"### {pred_dir}")
                                
                            # 4. 依然保留武器概率图
                            st.divider()
                            st.write("武器类型概率分布:")
                            probs = models['weapon'].predict_proba(X_input)[0]
                            classes = models['weapon'].classes_
                            sorted_indices = np.argsort(probs)[::-1][:5]
                            
                            chart_data = pd.DataFrame({
                                "Weapon": classes[sorted_indices],
                                "Probability": probs[sorted_indices]
                            })
                            st.bar_chart(chart_data.set_index("Weapon"))

# ==========================================
# 4. 程序入口
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login_page()
else:
    main_app()