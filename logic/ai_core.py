"""AI 推理核心（音频 -> 特征 -> 预测）

这个模块的目标是“可复用”：
- Streamlit UI 会直接 import 并调用。
- FastAPI 后端也会 import 并调用。
- pytest 需要能 import（即使没有 Streamlit runtime）。

因此这里刻意避免把 Streamlit 的运行时假设写死在模块加载阶段：
缓存仅在 Streamlit runtime 存在时启用；其余环境退化为普通函数。
"""

import os
import joblib
import numpy as np
import librosa
import pandas as pd
try:
    import streamlit as st
    from streamlit.runtime import runtime as st_runtime
except Exception:  # pragma: no cover
    st = None
    st_runtime = None
from gradio_client import Client, handle_file

# 配置
# 这些常量需要与训练/导出特征阶段保持一致，否则本地模型的输入维度会不匹配。
SAMPLE_RATE = 22050
DURATION = 2.0
N_MFCC = 13
HF_SPACE_ID = "Corden/pubg-sound-api" # 你的 Space 地址

def _cache_resource(func):
    """仅在 Streamlit runtime 下启用 st.cache_resource。

    背景：
    - Streamlit 的缓存对 UI 体验很好（避免重复加载模型/网络客户端）。
    - 但在 FastAPI/pytest 环境下，强依赖 Streamlit runtime 会导致 import 失败。
    """

    try:
        if st is not None and st_runtime is not None and st_runtime.exists():
            return st.cache_resource(func)
    except Exception:
        # Fallback to no-op caching outside Streamlit.
        pass
    return func


@_cache_resource
def load_local_models():
    """加载本地 RF 模型。

    约定：模型文件放在项目根目录下的 data/processed/weapon_classifier.pkl。
    这里用相对当前文件的方式定位项目根目录，避免依赖工作目录（cwd）。
    """
    try:
        # 1. 获取当前文件 (logic/ai_core.py) 的绝对路径
        current_file_path = os.path.abspath(__file__)
        
        # 2. 获取项目根目录 (logic 的上一级)
        # 第一次 dirname 得到 logic/ 目录
        # 第二次 dirname 得到 项目根目录
        project_root = os.path.dirname(os.path.dirname(current_file_path))
        
        # 3. 拼接出模型的绝对路径
        model_path = os.path.join(project_root, "data", "processed", "weapon_classifier.pkl")
        
        # 调试打印，让你确认路径对不对
        print(f"🔍 正在尝试加载模型，路径: {model_path}")

        if os.path.exists(model_path):
            model = joblib.load(model_path)
            print("✅ 本地模型加载成功！")
            return model
        else:
            print("错误：模型文件不存在于该路径。")
            return None

    except Exception as e:
        print(f"模型加载发生异常: {e}")
        return None

def extract_features(audio_file):
    """提取音频特征（必须与训练时一致）。

    输入：音频文件路径
    输出：形状为 (1, n_features) 的 numpy 数组；失败返回 None。

    这里会做两件“工程化”的处理：
    - 固定采样率与截断时长，减少输入分布漂移。
    - 不足时长则补零，保证特征维度固定，便于模型推理。
    """
    try:
        y, sr = librosa.load(audio_file, sr=SAMPLE_RATE, duration=DURATION)
        if len(y) < SAMPLE_RATE * DURATION:
            padding = int(SAMPLE_RATE * DURATION) - len(y)
            y = np.pad(y, (0, padding), 'constant')
        
        zcr = np.mean(librosa.feature.zero_crossing_rate(y))
        rms = np.mean(librosa.feature.rms(y=y))
        cent = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
        mfcc_mean = np.mean(mfcc, axis=1)
        
        features = [zcr, rms, cent]
        features.extend(mfcc_mean)
        return np.array([features])
    except Exception as e:
        print(f"特征提取错误: {e}")
        return None

def predict_cloud(audio_file_path):
    """调用 Hugging Face 云端 API。

    失败时返回 {"error": "..."}，上层可以直接透传给前端并提示。
    """
    try:
        client = Client(HF_SPACE_ID)
        result = client.predict(
            handle_file(audio_file_path),
            api_name="/predict_weapon"
        )
        return result
    except Exception as e:
        return {"error": str(e)}