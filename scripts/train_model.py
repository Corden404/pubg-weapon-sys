"""
脚本名称: train_model.py
功能: 读取 weapon_features_final.csv，训练随机森林分类器，并保存模型。
"""

import pandas as pd
import numpy as np
import joblib  # 用于保存和加载模型
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

# --- 配置 ---
DATA_FILE = "data/processed/weapon_features_final.csv"
MODEL_FILE = "data/processed/weapon_classifier.pkl" # 模型保存路径
LABEL_ENCODER_FILE = "data/processed/label_encoder.pkl" # 标签编码器保存路径

def train():
    print("1. 正在读取特征数据...")
    try:
        df = pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        print(f"❌ 错误：找不到 {DATA_FILE}。请先运行 extract_features.py！")
        return

    # --- 数据预处理 ---
    # 我们的目标是预测 'weapon' (枪种)
    # 特征是除了 weapon, distance, direction, id, dataset 之外的所有列
    
    # 排除非特征列
    drop_cols = ['weapon', 'distance', 'direction', 'dataset']
    # 注意：如果 CSV 里还有 id 列或其他杂项，也要排除。
    # 简单做法：只保留数值类型的列作为特征
    X = df.drop(columns=[c for c in drop_cols if c in df.columns])
    # 再次过滤，确保只剩数值
    X = X.select_dtypes(include=[np.number])
    
    y = df['weapon'] # 目标标签
    
    print(f"   特征维度: {X.shape}, 标签数量: {len(y)}")

    # --- 划分训练集和测试集 ---
    # 虽然数据里有 'dataset' 字段标记了 train/test，但为了简单通用，我们这里重新随机划分
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # --- 模型训练 (Random Forest) ---
    print("2. 开始训练随机森林模型 (Random Forest)...")
    # n_estimators=100 表示用 100 棵决策树
    clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    clf.fit(X_train, y_train)
    
    print("✅ 训练完成！")

    # --- 模型评估 ---
    print("3. 正在评估模型...")
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"   🚀 测试集准确率 (Accuracy): {acc:.4f}")
    
    print("\n   详细分类报告:")
    print(classification_report(y_test, y_pred))

    # --- 保存模型 ---
    print(f"4. 保存模型到 {MODEL_FILE} ...")
    # 我们把 模型 和 训练时用到的特征列名 一起保存
    # 这样预测时能确保特征顺序一致
    model_data = {
        "model": clf,
        "feature_names": list(X.columns)
    }
    joblib.dump(model_data, MODEL_FILE)
    print("✅ 模型已保存，可供网页调用！")

    # --- (可选) 绘制混淆矩阵并保存图片 ---
    # 这张图你可以放在实验报告里
    plt.figure(figsize=(10, 8))
    cm = confusion_matrix(y_test, y_pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=clf.classes_, yticklabels=clf.classes_)
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.savefig('data/processed/confusion_matrix.png')
    print("📊 混淆矩阵已保存为 confusion_matrix.png")

if __name__ == "__main__":
    train()