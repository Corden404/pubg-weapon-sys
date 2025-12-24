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
SAMPLE_RATE = 22050
DURATION = 2.0
N_MFCC = 13
HF_SPACE_ID = "Corden/pubg-sound-api" # 你的 Space 地址

def _cache_resource(func):
    """Use Streamlit cache only when running under Streamlit runtime.

    This keeps the function usable from FastAPI and pytest.
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
    """加载本地 RF 模型 (使用绝对路径修复版)"""
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
            print("❌ 错误：模型文件不存在于该路径。")
            return None

    except Exception as e:
        print(f"❌ 模型加载发生异常: {e}")
        return None

def extract_features(audio_file):
    """提取音频特征 (与训练时一致)"""
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
    """调用 Hugging Face 云端 API"""
    try:
        client = Client(HF_SPACE_ID)
        result = client.predict(
            handle_file(audio_file_path),
            api_name="/predict_weapon"
        )
        return result
    except Exception as e:
        return {"error": str(e)}