import streamlit as st
from ui.login import render_login
from ui.main_tabs import render_main_app

# 全局配置
st.set_page_config(
    page_title="PUBG 武器系统 (Refactored)",
    page_icon="🔫",
    layout="wide"
)

# 初始化 Session
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# 路由逻辑 (Routing)
if not st.session_state['logged_in']:
    render_login()
else:
    render_main_app()