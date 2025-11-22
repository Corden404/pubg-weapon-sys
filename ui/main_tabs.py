import streamlit as st
import pandas as pd
import os
from datetime import datetime
from utils.database import get_db
from logic.ai_core import load_local_models, extract_features, predict_cloud
from utils.logger import log_action

def render_main_app():
    user = st.session_state['user_info']
    db = get_db()
    
    if db is None:
        st.error("无法连接数据库")
        st.stop()
    
    # --- 侧边栏 ---
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/pubg.png", width=80)
        st.write(f"👋 欢迎, **{user['student_id']}**")
        if st.button("🚪 退出"):
            st.session_state['logged_in'] = False
            st.rerun()
    
    st.title("🔫 PUBG 武器指挥中心")
    
    t1, t2, t3, t4 = st.tabs(["🎒 背包", "📚 图鉴", "🛠️ 管理", "🎙️ AI识别"])

    # --- Tab 1: 背包 (优化显示) ---
    with t1:
        curr_user = db.users.find_one({"student_id": user['student_id']})
        inventory = curr_user.get('inventory', [])
        
        if inventory:
            # 数据处理：格式化时间
            df = pd.DataFrame(inventory)
            
            # 如果有 added_at 字段，格式化一下显示
            if 'added_at' in df.columns:
                df['added_at'] = pd.to_datetime(df['added_at']).dt.strftime('%Y-%m-%d %H:%M')
            
            # 重命名列，让表格更好看
            df_display = df.rename(columns={
                "weapon_name": "武器名称",
                "ammo_count": "携带弹药",
                "added_at": "入库时间"
            })
            
            c1, c2 = st.columns([3, 1])
            with c1:
                st.metric("总弹药储备", df['ammo_count'].sum())
                st.dataframe(df_display, use_container_width=True)
            
            with c2:
                st.write("#### 🗑️ 丢弃")
                to_remove = st.selectbox("选择武器", [i['weapon_name'] for i in inventory], key='inv_remove')
                if st.button("确认丢弃", type="primary"):
                    db.users.update_one(
                        {"student_id": user['student_id']}, 
                        {"$pull": {"inventory": {"weapon_name": to_remove}}}
                    )
                    st.toast(f"已丢弃 {to_remove}")
                    log_action(db, user['student_id'], "INVENTORY_REMOVE", f"丢弃了 {to_remove}")
                    st.rerun()
        else:
            st.info("🎒 背包空空如也，快去图鉴进货吧！")

    # --- Tab 2: 图鉴 (修复弹药选择与时间戳) ---
    with t2:
        weapons = list(db.game_weapons.find({}, {"_id": 0}))
        df = pd.DataFrame(weapons)
        
        # 排序与搜索
        c_sort, c_search = st.columns([1, 2])
        with c_sort:
            sort_col = st.selectbox("排序", ["damage", "name", "type"], index=0)
        with c_search:
            search_txt = st.text_input("搜索武器", placeholder="输入 M4, AK...")
            
        # 筛选逻辑
        if search_txt:
            df = df[df['name'].str.contains(search_txt, case=False) | df['full_name'].str.contains(search_txt, case=False)]
            
        df = df.sort_values(by=sort_col, ascending=False)
        
        for index, row in df.iterrows():
            with st.container():
                # 分栏布局：图片(1) | 详细参数(3) | 操作区(1.5)
                c1, c2, c3 = st.columns([1, 3, 1.5])
                
                with c1:
                    local_img = f"images/{row['name']}.png"
                    img_src = local_img if os.path.exists(local_img) else row.get('image_url')
                    if not img_src: img_src = "https://img.icons8.com/ios-filled/50/gun.png"
                    st.image(img_src, width=100)
                
                with c2:
                    full_name = row.get('full_name', row['name'])
                    st.subheader(f"{full_name}")
                    st.caption(f"类型: {row['type']} | 子弹: {row['ammo_type']}")
                    
                    stats = row.get('stats', {})
                    if isinstance(stats, dict):
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("伤害", row.get('damage', 0))
                        m2.metric("射速", f"{stats.get('fire_rate', 0)}s")
                        m3.metric("射程", f"{stats.get('range', 0)}m")
                        m4.metric("弹匣", stats.get('mag_size', 0))

                with c3:
                    # --- 修复：增加弹药输入框 ---
                    ammo_val = st.number_input("弹药量", min_value=1, value=30, key=f"ammo_{row['name']}", label_visibility="collapsed")
                    
                    if st.button("🎒 添加至背包", key=f"add_{row['name']}"):
                        # --- 修复：增加时间戳 ---
                        item = {
                            "weapon_name": row['name'],
                            "ammo_count": ammo_val,
                            "added_at": datetime.now()  # 这里补上了时间
                        }
                        
                        db.users.update_one(
                            {"student_id": user['student_id']},
                            {"$push": {"inventory": item}}
                        )
                        log_action(db, user['student_id'], "INVENTORY_ADD", {"item": row['name'], "ammo": ammo_val})
                        st.toast(f"✅ 已添加 {full_name} (x{ammo_val})")
            st.divider()

    # --- Tab 3: 管理 ---
    with t3:
        st.warning("⚠️ 管理员区域：修改将影响全局数据")
        if not df.empty:
            target = st.selectbox("编辑武器数据", df['name'].unique())
            curr = db.game_weapons.find_one({"name": target})
            with st.form("admin_edit"):
                c1, c2 = st.columns(2)
                with c1:
                    n_dmg = st.number_input("基础伤害", value=int(curr.get('damage', 0)))
                with c2:
                    n_type = st.text_input("武器类型", value=curr.get('type', 'Unknown'))
                if st.form_submit_button("💾 保存修改"):
                    db.game_weapons.update_one({"name": target}, {"$set": {"damage": n_dmg, "type": n_type}})
                    # 日志记录（管理员修改）
                    log_action(db, user['student_id'], "ADMIN_MODIFY", {"target": target, "changes": {"damage": n_dmg, "type": n_type}})
                    st.success("数据库已更新")

    # --- Tab 4: AI ---
    with t4:
        st.header("端云协同 AI")
        uploaded = st.file_uploader("上传音频文件", type=["mp3", "wav"])
        
        if uploaded and st.button("🚀 开始混合推理"):
            status = st.status("正在分析...", expanded=True)
            with open("temp.mp3", "wb") as f:
                f.write(uploaded.getbuffer())
            # 1. Cloud
            status.write("☁️ 云端 CNN 识别武器型号...")
            cloud_raw_res = predict_cloud("temp.mp3")
            cloud_weapon_name = "未知"
            cloud_conf = 0.0
            try:
                if isinstance(cloud_raw_res, dict) and 'label' in cloud_raw_res:
                    cloud_weapon_name = cloud_raw_res['label']
                    if 'confidences' in cloud_raw_res:
                        cloud_conf = cloud_raw_res['confidences'][0]['confidence']
                elif isinstance(cloud_raw_res, dict):
                    cloud_weapon_name = max(cloud_raw_res, key=cloud_raw_res.get)
                    cloud_conf = cloud_raw_res[cloud_weapon_name]
                elif isinstance(cloud_raw_res, str):
                    cloud_weapon_name = cloud_raw_res
            except: pass

            # 2. Local
            status.write("💻 本地 RF 测算距离方位...")
            local_models = load_local_models()
            local_dist, local_dir = "N/A", "N/A"
            if local_models:
                feats = extract_features("temp.mp3")
                if feats is not None:
                    local_dist = local_models['models']['distance'].predict(feats)[0]
                    local_dir = local_models['models']['direction'].predict(feats)[0]

            status.update(label="分析完成", state="complete", expanded=False)

            # 日志记录（AI推理）
            log_action(
                db,
                user['student_id'],
                "AI_INFERENCE",
                {
                    "cloud": {"weapon": cloud_weapon_name, "conf": float(cloud_conf)},
                    "local": {"dist": local_dist, "dir": local_dir},
                    "audio_file": uploaded.name
                }
            )

            # 3. Result
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("武器型号", cloud_weapon_name)
                st.progress(float(cloud_conf), text=f"置信度: {float(cloud_conf):.1%}")
                img_path = f"images/{cloud_weapon_name}.png"
                if os.path.exists(img_path): st.image(img_path, width=120)
            c2.metric("射击距离", local_dist)
            c3.metric("射击方位", local_dir)