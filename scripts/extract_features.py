"""
脚本名称: extract_features.py
功能: 遍历音频文件夹，提取 MFCC 特征，保存为 CSV，用于模型训练。
"""

import os
import pandas as pd
import numpy as np
import librosa
import warnings
from tqdm import tqdm # 进度条库

# 忽略 librosa 的一些警告
warnings.filterwarnings('ignore')

# --- 配置参数 ---
DATA_DIR = "data/audio/sounds" # 解压后的音频根目录
OUTPUT_FILE = "data/processed/weapon_features_final.csv"
SAMPLE_RATE = 22050 # 标准采样率
DURATION = 2.0      # 统一截取前 2 秒 (枪声通常很短)
N_MFCC = 13         # 提取 13 个 MFCC 特征 (标准做法)

def parse_filename(filename):
    """
    解析文件名: ak_100m_front_0906.mp3
    返回: {weapon, distance, direction, id}
    """
    name_no_ext = filename.replace('.mp3', '')
    parts = name_no_ext.split('_')
    
    info = {}
    if parts[0] == 'nogun':
        info['weapon'] = 'nogun'
        info['distance'] = '0m'
        info['direction'] = 'center' # 默认值
    else:
        # 正常格式: ak_100m_front_0906
        if len(parts) >= 4:
            info['weapon'] = parts[0]
            info['distance'] = parts[1]
            info['direction'] = parts[2]
        else:
            # 异常文件名处理
            return None
    return info

def extract_features(file_path):
    """
    核心函数: 读取音频 -> 提取 MFCC 特征
    """
    try:
        # 1. 加载音频 (只取前 DURATION 秒)
        y, sr = librosa.load(file_path, sr=SAMPLE_RATE, duration=DURATION)
        
        # 2. 如果音频太短，进行填充
        if len(y) < SAMPLE_RATE * DURATION:
            padding = int(SAMPLE_RATE * DURATION) - len(y)
            y = np.pad(y, (0, padding), 'constant')

        # 3. 提取特征
        # A. Zero Crossing Rate (过零率 - 声音有多“尖”)
        zcr = np.mean(librosa.feature.zero_crossing_rate(y))
        
        # B. RMS Energy (能量 - 声音有多响)
        rms = np.mean(librosa.feature.rms(y=y))
        
        # C. Spectral Centroid (频谱质心 - 音色的明亮度)
        cent = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
        
        # D. MFCC (梅尔频率倒谱系数 - 核心特征，相当于声纹)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
        # mfcc 返回的是 (n_mfcc, time_steps)，我们需要取平均值变成一维向量
        mfcc_mean = np.mean(mfcc, axis=1)
        
        # 4. 组装特征字典
        features = {
            "zcr": zcr,
            "rms": rms,
            "spectral_centroid": cent
        }
        # 把 13 个 MFCC 数值展开: mfcc_0, mfcc_1 ...
        for i in range(N_MFCC):
            features[f'mfcc_{i}'] = mfcc_mean[i]
            
        return features
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

def process_dataset():
    all_data = []
    
    # 确保输出目录存在
    os.makedirs("data/processed", exist_ok=True)
    
    # 遍历 train 和 test 两个文件夹
    sub_dirs = ['gun_sound_train', 'gun_sound_test']
    
    # 收集所有文件路径
    file_list = []
    for sub in sub_dirs:
        dir_path = os.path.join(DATA_DIR, sub)
        if not os.path.exists(dir_path):
            print(f"警告: 找不到目录 {dir_path}，请检查解压路径！")
            continue
            
        for f in os.listdir(dir_path):
            if f.endswith('.mp3'):
                # 记录: (完整路径, 来源集合, 文件名)
                file_list.append((os.path.join(dir_path, f), sub, f))
    
    print(f"共发现 {len(file_list)} 个音频文件，开始提取特征...")
    
    # 使用 tqdm 显示进度条
    for file_path, dataset_type, filename in tqdm(file_list):
        # 1. 解析文件名标签
        meta_info = parse_filename(filename)
        if not meta_info:
            continue
            
        # 2. 提取音频特征
        features = extract_features(file_path)
        if features:
            # 3. 合并所有信息
            # 标签 + 特征 + 数据集来源(train/test)
            row = {**meta_info, **features, "dataset": dataset_type}
            all_data.append(row)
            
    # 保存为 CSV
    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"\n特征提取完成！已保存至 {OUTPUT_FILE}")
        print(f"数据预览:\n{df.head()}")
    else:
        print("没有提取到任何数据，请检查路径。")

if __name__ == "__main__":
    # 安装必要的库 (以防万一)
    os.system("pip install librosa tqdm scikit-learn")
    process_dataset()