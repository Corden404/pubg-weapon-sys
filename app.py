import streamlit as st
import pandas as pd

st.title("PUBG 武器管理系统 - 云端开发版")
st.write("如果能看到这句话，说明环境配置成功！")

# 模拟读取数据
data = {'武器': ['M416', '98K'], '伤害': [44, 97]}
df = pd.DataFrame(data)
st.table(df)