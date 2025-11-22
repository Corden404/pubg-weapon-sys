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
import logging
from gradio_client import Client, handle_file

# ==========================================
# 0. 全局配置
# ==========================================
st.set_page_config(
    page_title="PUBG 武器管理与识别系统",
    page_icon="🔫",
    layout="wide",
    initial_sidebar_state="expanded"
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("system.log", encoding="utf-8"), #存入文件
        logging.StreamHandler() #输出到终端
    ]
)
logging.info("系统启动")

# ==========================================
# 1. 核心工具函数 (数据库 & AI)
# ==========================================

class Weapon:
    def __init__(self, name, w_type, damage, headshot_rate, fire_rate, range_m, ammo_type, mag_size, reload_time, image_url=""):
        self.name = name                # 名称 (M416)
        self.w_type = w_type            # 类型 (突击步枪)
        self.damage = damage            # 基础伤害
        self.headshot_rate = headshot_rate # 爆头倍率 (2.3)
        self.fire_rate = fire_rate      # 射速 (0.086s)
        self.range_m = range_m          # 有效射程
        self.ammo_type = ammo_type      # 子弹类型
        self.mag_size = mag_size        # 弹匣容量
        self.reload_time = reload_time  # 换弹时间
        self.image_url = image_url      # 图片链接

    def to_dict(self):
        """转为字典以存入 MongoDB"""
        return {
            "name": self.name,
            "type": self.w_type,
            "damage": self.damage,
            "stats": {  # 我们可以把详细属性折叠在一个子字典里，保持整洁
                "headshot_rate": self.headshot_rate,
                "fire_rate": self.fire_rate,
                "range": self.range_m,
                "mag_size": self.mag_size,
                "reload_time": self.reload_time
            },
            "ammo_type": self.ammo_type,
            "image_url": self.image_url
        }

@st.cache_resource
def init_connection():
    try:
        # 优先尝试读取环境变量 (Codespaces Secret)
        if "MONGO_URI" in os.environ:
            uri = os.environ["MONGO_URI"]
        else:
            # 其次尝试读取 secrets.toml (本地文件)
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
                        logging.info(f"用户 {username} 登录成功") #记录日志
                        # 设置 Session 状态
                        st.session_state['logged_in'] = True
                        st.session_state['user_info'] = user
                        st.session_state['username'] = username
                        st.success("登录成功！")
                        st.rerun()
                    else:
                        st.error("❌ 密码错误")
                        logging.warning(f"用户 {username} 登录失败，密码错误")
                else:
                    st.error("❌ 该学号未注册")
                    logging.warning(f"登录失败，学号 {username} 未注册")
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
                    logging.info(f"新用户注册成功: {new_user}") #记录日志
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
            logging.info(f"用户 {user['student_id']} 退出登录") #记录日志
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
                    logging.info(f"用户 {user['student_id']} 丢弃武器 {weapon_to_remove}")
                    db.users.update_one(
                        {"student_id": user['student_id']},
                        {"$pull": {"inventory": {"weapon_name": weapon_to_remove}}}
                    )
                    st.success(f"已丢弃 {weapon_to_remove}")
                    logging.info(f"用户 {user['student_id']} 丢弃武器 {weapon_to_remove}")
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
            
            if 'stats' in df_sorted.columns:
                # 把 stats 字典里的字段拆分出来变成单独的列
                stats_df = pd.json_normalize(df_sorted['stats'])
                df_display = pd.concat([df_sorted.drop(columns=['stats']), stats_df], axis=1)
                
                # 重命名一下列名，显示中文
                df_display = df_display.rename(columns={
                    "name": "武器名称",
                    "type": "武器类型", 
                    "damage": "基础伤害",
                    "ammo_type": "弹药类型",
                    "headshot_rate": "爆头倍率",
                    "fire_rate": "射速(s)",
                    "range": "射程(m)",
                    "mag_size": "弹夹容量",
                    "reload_time": "换弹时间(s)"
                })
                
                st.dataframe(df_display, use_container_width=True)
            else:
                # 如果没有 stats 列，直接显示原始数据（英文表头）
                st.dataframe(df_sorted, use_container_width=True)
            
            st.divider()
            st.write("### 📥 装备补给")
            c1, c2 = st.columns([2, 1])
            with c1:
                selected_weapon = st.selectbox("选择武器", df_sorted['name'].unique())
            with c2:
                ammo_count = st.number_input("子弹数量", min_value=1, value=30)
            
            if st.button("放入背包", type="primary"):
                logging.info(f"用户 {user['student_id']} 将武器 {selected_weapon} 和弹药 {ammo_count} 放入背包")
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

    # TAB 4: AI (混合架构版)
    with tab_ai:
        st.header("☁️ 云端 AI 识别 ")
        st.info("💡 架构说明：利用云端 CNN 进行高精度武器分类，同时利用本地 RF 模型补充距离与方位信息。")

        # Hugging Face 地址
        HF_SPACE_ID = "Corden/pubg-sound-api" # <--- 确认是你的地址
        
        uploaded_audio = st.file_uploader("上传录音 (MP3/WAV)", type=["mp3", "wav"])
        
        if uploaded_audio is not None:
            st.audio(uploaded_audio)
            
            if st.button("🚀 启动混合推理引擎", type="primary"):
                # 准备容器显示结果
                col_main, col_details = st.columns([1, 2])
                
                # --- 1. 云端推理 (负责武器分类) ---
                cloud_result = None
                with col_main:
                    with st.status("正在连接 Hugging Face...", expanded=True) as status:
                        try:
                            client = Client(HF_SPACE_ID)
                            
                            # 写入临时文件
                            with open("temp_upload.mp3", "wb") as f:
                                f.write(uploaded_audio.getbuffer())
                            
                            # 调用 API
                            status.write("📤 发送音频数据...")
                            result = client.predict(
                                handle_file("temp_upload.mp3"),
                                api_name="/predict_weapon"
                            )
                            status.write("📥 接收神经网络张量...")
                            
                            # 解析云端结果 (假设返回的是 Label 字典)
                            # Gradio Client 返回格式通常是: {'label': 'ak', 'confidences': [...]} 或 直接字典
                            if isinstance(result, dict) and 'confidences' in result:
                                # 提取 Top 1
                                cloud_weapon = result['label']
                                cloud_conf = result['confidences'][0]['confidence']
                            elif isinstance(result, dict):
                                # 兼容直接返回字典的情况
                                cloud_weapon = max(result, key=result.get)
                                cloud_conf = result[cloud_weapon]
                            else:
                                cloud_weapon = "解析错误"
                                cloud_conf = 0.0
                                
                            cloud_result = (cloud_weapon, cloud_conf)
                            status.update(label="✅ 云端推理完成", state="complete", expanded=False)
                            
                        except Exception as e:
                            status.update(label="❌ 云端连接失败", state="error")
                            st.error(f"API 错误: {e}")

                # --- 2. 本地推理 (负责距离和方位) ---
                local_dist = "N/A"
                local_dir = "N/A"
                
                # 加载本地模型 (如果存在)
                try:
                    local_package = load_model()
                    if local_package:
                        # 提取特征
                        X_input = extract_features_for_prediction(uploaded_audio)
                        if X_input is not None:
                            # 只预测距离和方位
                            local_dist = local_package['models']['distance'].predict(X_input)[0]
                            local_dir = local_package['models']['direction'].predict(X_input)[0]
                except Exception:
                    pass # 如果本地模型坏了，就忽略，只显示云端结果

                # --- 3. 合并展示结果 ---
                st.divider()
                st.subheader("🎯 战术分析报告")
                
                c1, c2, c3 = st.columns(3)
                
                with c1:
                    st.caption("🔫 武器型号 (Cloud CNN)")
                    if cloud_result:
                        st.markdown(f"## {cloud_result[0].upper()}")
                        st.progress(cloud_result[1], text=f"置信度: {cloud_result[1]:.1%}")
                    else:
                        st.error("获取失败")
                
                with c2:
                    st.caption("📏 射击距离 (Local RF)")
                    st.markdown(f"## {local_dist}")
                
                with c3:
                    st.caption("🧭 射击方位 (Local RF)")
                    st.markdown(f"## {local_dir}")

                # 展示图片
                if cloud_result:
                    img_path = f"images/{cloud_result[0]}.png"
                    if os.path.exists(img_path):
                        st.image(img_path, caption=f"识别为: {cloud_result[0]}", width=200)

# ==========================================
# 4. 程序入口
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login_page()
else:
    main_app()