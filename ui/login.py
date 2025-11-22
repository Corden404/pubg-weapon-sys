import streamlit as st
from datetime import datetime
from utils.database import get_db, make_hash, check_hashes

def render_login():
    st.markdown("<h1 style='text-align: center;'>🔐 PUBG 综合实训系统</h1>", unsafe_allow_html=True)
    
    db = get_db()
    if db is None: return

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["登录账号", "注册新用户"])
        
        with tab1:
            username = st.text_input("学号 (Student ID)")
            password = st.text_input("密码", type='password')
            
            if st.button("登录", use_container_width=True):
                user = db.users.find_one({"student_id": username})
                if user and check_hashes(password, user['password']):
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = user
                    st.session_state['username'] = username
                    st.success("登录成功！")
                    st.rerun()
                else:
                    st.error("❌ 账号或密码错误")

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
                    db.users.insert_one({
                        "student_id": new_user,
                        "password": make_hash(new_pass),
                        "inventory": [],
                        "created_at": datetime.now()
                    })
                    st.success("✅ 注册成功！请登录。")