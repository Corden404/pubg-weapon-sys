import os
import joblib
import numpy as np
import librosa
import pandas as pd
import streamlit as st
from gradio_client import Client, handle_file

# 配置
SAMPLE_RATE = 22050
DURATION = 2.0
N_MFCC = 13
HF_SPACE_ID = "Corden/pubg-sound-api" # 你的 Space 地址

@st.cache_resource
def load_local_models():
    """加载本地 RF 模型"""
    model_path = "data/processed/weapon_classifier.pkl"
    if os.path.exists(model_path):
        try:
            return joblib.load(model_path)
        except:
            return None
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