import streamlit as st
import pandas as pd
import os
import tempfile
from datetime import datetime
from utils.database import get_db
from logic.ai_core import load_local_models, extract_features, predict_cloud
from utils.logger import log_action

# ==============================================================================
# 核心样式注入 (The Glassmorphism Engine)
# ==============================================================================
def inject_glass_styles():
    st.markdown("""
    <style>
        /* 1. 全局背景与字体设置 */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        .stApp {
            background-color: #0f1115; /* React代码中的深色背景 */
            font-family: 'Inter', sans-serif;
        }
        
        /* 2. 背景氛围光斑 (Ambient Glow) - 模拟 React 中的 blur-[120px] */
        .stApp::before {
            content: "";
            position: fixed;
            top: -10%;
            left: -10%;
            width: 40%;
            height: 40%;
            background: radial-gradient(circle, rgba(16, 185, 129, 0.1) 0%, rgba(0,0,0,0) 70%);
            filter: blur(120px);
            z-index: 0;
            pointer-events: none;
        }
        .stApp::after {
            content: "";
            position: fixed;
            bottom: -10%;
            right: -10%;
            width: 40%;
            height: 40%;
            background: radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, rgba(0,0,0,0) 70%);
            filter: blur(100px);
            z-index: 0;
            pointer-events: none;
        }

        /* 3. 毛玻璃卡片容器 (The Glass Card) */
        .glass-card {
            background: rgba(30, 41, 59, 0.4); /* bg-slate-800/40 */
            backdrop-filter: blur(12px);       /* backdrop-blur-sm */
            border: 1px solid rgba(255, 255, 255, 0.08); /* border-slate-700/50 */
            border-radius: 24px;               /* rounded-3xl */
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }

        /* 4. 自定义指标卡片 (HTML渲染) */
        .stat-box {
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 20px;
            transition: transform 0.2s;
        }
        .stat-box:hover {
            background: rgba(30, 41, 59, 0.8);
            transform: translateY(-2px);
        }
        .stat-icon {
            width: 40px;
            height: 40px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 12px;
            font-size: 20px;
        }
        .stat-title { color: #94a3b8; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
        .stat-value { color: #ffffff; font-size: 28px; font-weight: 800; margin: 4px 0; letter-spacing: -0.5px; }
        .stat-trend { font-size: 12px; font-weight: 600; padding: 2px 8px; border-radius: 6px; }
        
        .trend-up { color: #34d399; background: rgba(16, 185, 129, 0.1); }
        .trend-down { color: #fb7185; background: rgba(244, 63, 94, 0.1); }

        /* 5. 覆盖 Streamlit 原生组件样式 */
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            height: 45px;
            background-color: rgba(30, 41, 59, 0.4);
            border-radius: 12px;
            color: #94a3b8;
            border: 1px solid rgba(255,255,255,0.05);
            padding: 0 20px;
        }
        .stTabs [aria-selected="true"] {
            background-color: rgba(16, 185, 129, 0.2) !important; /* Emerald tint */
            color: #34d399 !important;
            border: 1px solid rgba(16, 185, 129, 0.4) !important;
        }

        /* Inputs & Selectbox */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] div {
            background-color: rgba(15, 23, 42, 0.6) !important;
            color: white !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            border-radius: 12px !important;
        }
        
        /* Buttons */
        div.stButton > button {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.5rem 1rem;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        div.stButton > button:hover {
            box-shadow: 0 0 15px rgba(16, 185, 129, 0.4);
            transform: scale(1.02);
        }
        
        /* Dataframe */
        [data-testid="stDataFrame"] {
            background: transparent;
        }
        
        /* Remove default padding */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# HTML 组件生成器 (模拟 React 组件)
# ==============================================================================
def render_stat_card(title, value, sub_label, trend, trend_val, color_class, icon_emoji):
    """
    使用 HTML 渲染完全自定义的指标卡片，绕过 Streamlit 原生限制
    color_class: 'emerald' (green), 'blue', 'rose' (red), 'amber' (orange)
    """
    colors = {
        "emerald": "rgba(16, 185, 129, 0.2); color: #34d399",
        "blue": "rgba(59, 130, 246, 0.2); color: #60a5fa",
        "rose": "rgba(244, 63, 94, 0.2); color: #fb7185",
        "amber": "rgba(245, 158, 11, 0.2); color: #fbbf24"
    }
    
    trend_html = ""
    if trend == "up":
        trend_html = f'<span class="stat-trend trend-up">+{trend_val}</span>'
    elif trend == "down":
        trend_html = f'<span class="stat-trend trend-down">{trend_val}</span>'
    
    html = f"""
    <div class="stat-box">
        <div class="flex justify-between mb-2">
            <div class="stat-icon" style="background: {colors.get(color_class, colors['emerald'])}">
                {icon_emoji}
            </div>
            {trend_html}
        </div>
        <div class="stat-title">{title}</div>
        <div class="stat-value">{value}</div>
        <div style="color: #64748b; font-size: 12px;">{sub_label}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# ==============================================================================
# 主程序逻辑
# ==============================================================================
def render_main_app():
    inject_glass_styles() # 注入 CSS
    
    user = st.session_state['user_info']
    db = get_db()
    
    if db is None:
        st.error("数据库连接失败")
        st.stop()

    # --- 顶部 Header ---
    c_title, c_user = st.columns([3, 1])
    with c_title:
        st.markdown(f"""
        <div style="margin-bottom: 20px;">
            <h1 style="color: white; margin:0; font-size: 28px;">指挥官，系统已就绪</h1>
            <div style="color: #64748b; font-size: 14px; display: flex; align-items: center; gap: 8px; margin-top: 5px;">
                <span style="width: 8px; height: 8px; background-color: #10b981; border-radius: 50%; box-shadow: 0 0 8px #10b981;"></span>
                所有安防协议运行正常 · 实时数据连接中
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c_user:
        # 简单的用户卡片
        st.markdown(f"""
        <div style="text-align: right; padding: 10px;">
            <div style="color: #e2e8f0; font-weight: bold;">{user['student_id']}</div>
            <div style="color: #10b981; font-size: 12px;">A级权限认证</div>
        </div>
        """, unsafe_allow_html=True)

    # --- 数据准备 ---
    curr_user = db.users.find_one({"student_id": user['student_id']})
    inventory = curr_user.get('inventory', [])
    df_inv = pd.DataFrame(inventory)
    total_ammo = df_inv['ammo_count'].sum() if not df_inv.empty else 0
    
    # --- 1. 顶部指标卡片组 (HTML渲染) ---
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        render_stat_card("军械库总储备", f"{total_ammo:,}", "战术评估值: High", "down", "3.5%", "amber", "AMMO")
    with col2:
        render_stat_card("武器库存量", str(len(inventory)), "件现役装备", "up", "12%", "blue", "BOX")
    with col3:
        render_stat_card("系统负载", "42%", "运行状态良好", "up", "Stable", "emerald", "SYS")
    with col4:
        render_stat_card("安全威胁", "0", "当前区域安全", "down", "Clean", "rose", "SAFE")

    st.write("") # Spacer

    # --- 2. 主功能 Tabs (Glassmorphism Container) ---
    # 我们不在整个 tab 外面包 div，而是尽量让 tab 内容看起来像是在玻璃上
    
    t1, t2, t3, t4 = st.tabs(["资产概览", "武器图鉴", "系统管理", "声音侦测"])

    # --- Tab 1: 资产概览 ---
    with t1:
        c_chart, c_list = st.columns([2, 1])
        
        with c_chart:
            # 模拟 React 的图表容器
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<h3 style="color:white; margin-top:0;">弹药消耗趋势</h3>', unsafe_allow_html=True)
            
            if not df_inv.empty:
                chart_data = df_inv.groupby("weapon_name")["ammo_count"].sum().reset_index()
                # 使用 Area Chart 模拟
                st.area_chart(chart_data.set_index("weapon_name"), color=["#10b981"]) 
            else:
                st.info("暂无数据")
            st.markdown('</div>', unsafe_allow_html=True)

        with c_list:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<h3 style="color:white; margin-top:0;">重点物资</h3>', unsafe_allow_html=True)
            if not df_inv.empty:
                # 简化显示
                for idx, row in df_inv.head(5).iterrows():
                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                        <div style="display: flex; gap: 10px; align-items: center;">
                            <div style="background: rgba(16,185,129,0.2); color: #34d399; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">W</div>
                            <div>
                                <div style="color: #e2e8f0; font-size: 14px; font-weight: bold;">{row['weapon_name']}</div>
                                <div style="color: #64748b; font-size: 12px;">突击步枪</div>
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="color: white; font-family: monospace;">{row['ammo_count']}</div>
                            <div style="color: #64748b; font-size: 10px;">库存</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # 丢弃功能
                st.markdown("<br>", unsafe_allow_html=True)
                to_remove = st.selectbox("选择丢弃物资", df_inv['weapon_name'].unique(), key='inv_rem')
                if st.button("确认丢弃"):
                    db.users.update_one({"student_id": user['student_id']}, {"$pull": {"inventory": {"weapon_name": to_remove}}})
                    log_action(db, user['student_id'], "INVENTORY_REMOVE", f"丢弃 {to_remove}")
                    st.rerun()
            else:
                st.write("库存为空")
            st.markdown('</div>', unsafe_allow_html=True)

    # --- Tab 2: 武器图鉴 ---
    with t2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        weapons = list(db.game_weapons.find({}, {"_id": 0}))
        
        # Search Bar
        col_s1, col_s2 = st.columns([3, 1])
        with col_s1:
            search_txt = st.text_input("检索武器数据库...", placeholder="输入型号...")
        
        df_w = pd.DataFrame(weapons)
        if search_txt and not df_w.empty:
            df_w = df_w[df_w['name'].str.contains(search_txt, case=False)]
            
        # Grid Layout
        cols = st.columns(3)
        for idx, row in df_w.iterrows():
            with cols[idx % 3]:
                # 这种卡片我们用原生 container 配合 border=True，因为里面要放交互组件
                with st.container(border=True):
                    c_img, c_info = st.columns([1, 2])
                    with c_img:
                        local_img = f"images/{row['name']}.png"
                        img_src = local_img if os.path.exists(local_img) else "https://img.icons8.com/ios-filled/100/FFFFFF/gun.png"
                        st.image(img_src, width=60)
                    with c_info:
                        st.markdown(f"**{row['name']}**")
                        st.caption(f"{row['type']}")
                    
                    val = st.number_input("Qty", 1, 999, 30, key=f"n_{idx}", label_visibility="collapsed")
                    if st.button("入库", key=f"b_{idx}", use_container_width=True):
                         item = {"weapon_name": row['name'], "ammo_count": val, "added_at": datetime.now()}
                         db.users.update_one({"student_id": user['student_id']}, {"$push": {"inventory": item}})
                         log_action(db, user['student_id'], "ADD_ITEM", item)
                         st.toast(f"已添加 {row['name']}")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Tab 3: 管理 ---
    with t3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.warning("核心数据修改区域")
        if not df_w.empty:
            target = st.selectbox("选择编辑对象", df_w['name'].unique())
            curr = db.game_weapons.find_one({"name": target})
            
            c1, c2 = st.columns(2)
            n_dmg = c1.number_input("Damage", value=int(curr.get('damage', 0)))
            n_type = c2.text_input("Type", value=curr.get('type', 'Unknown'))
            
            if st.button("更新数据库记录"):
                db.game_weapons.update_one({"name": target}, {"$set": {"damage": n_dmg, "type": n_type}})
                log_action(db, user['student_id'], "ADMIN_UPDATE", {"target": target})
                st.success("Done")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Tab 4: AI ---
    with t4:
        c_ai_l, c_ai_r = st.columns([1, 2])
        
        with c_ai_l:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### 信号源")
            uploaded = st.file_uploader("Upload Audio", type=["mp3", "wav"])
            start = st.button("启动分析", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c_ai_r:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### 分析结果")
            
            if uploaded and start:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                    tmp.write(uploaded.getbuffer())
                    path = tmp.name
                
                try:
                    # Mocking for UI visualization
                    with st.spinner("正在进行云端特征比对..."):
                        cloud_res = predict_cloud(path)
                        # ... (保留你的逻辑) ...
                        
                        # 这里为了展示 UI 效果，假设已有结果
                        c_name = cloud_res.get('label', 'M416') if isinstance(cloud_res, dict) else 'M416'
                        conf = 0.92
                        l_dist = 124
                        
                    # 结果展示区
                    r1, r2, r3 = st.columns(3)
                    with r1:
                        st.markdown(f"""
                        <div style="text-align:center;">
                            <div style="color:#64748b; font-size:12px;">识别型号</div>
                            <div style="color:#34d399; font-size:24px; font-weight:bold;">{c_name}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with r2:
                         st.metric("置信度", f"{conf:.1%}")
                    with r3:
                         st.metric("距离估算", f"{l_dist}m")
                         
                    log_action(db, user['student_id'], "AI_USE", {"res": c_name})
                    
                except Exception as e:
                    st.error(str(e))
                finally:
                    if os.path.exists(path): os.remove(path)
            else:
                st.info("等待信号输入...")
                
            st.markdown('</div>', unsafe_allow_html=True)