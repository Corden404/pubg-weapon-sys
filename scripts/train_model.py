"""
脚本名称: train_model.py (升级版 - 多任务学习)
功能: 训练三个独立的分类器，分别预测：武器类型、距离、方位
"""
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

DATA_FILE = "data/processed/weapon_features_final.csv"
MODEL_FILE = "data/processed/weapon_classifier.pkl"

def train():
    print("1. 读取数据...")
    df = pd.read_csv(DATA_FILE)
    
    # 准备特征 X (排除所有非数值的标签列)
    # 注意：dataset, id, weapon, distance, direction 都不是特征
    drop_cols = ['weapon', 'distance', 'direction', 'dataset', 'id', 'distance_label'] 
    # 过滤掉不存在的列
    actual_drop = [c for c in drop_cols if c in df.columns]
    X = df.drop(columns=actual_drop).select_dtypes(include=[np.number])
    
    print(f"   特征维度: {X.shape}")

    # --- 训练三个目标 (Targets) ---
    targets = {
        "weapon": df['weapon'],
        "distance": df['distance'],
        "direction": df['direction']
    }
    
    trained_models = {}
    
    for task_name, y in targets.items():
        print(f"\n--- 正在训练任务: [预测 {task_name}] ---")
        
        # 划分数据集
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # 训练模型
        clf = RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42)
        clf.fit(X_train, y_train)
        
        # 评估
        acc = accuracy_score(y_test, clf.predict(X_test))
        print(f"   {task_name} 准确率: {acc:.4f}")
        
        # 存入字典
        trained_models[task_name] = clf

    # --- 保存所有模型 ---
    print(f"\n4. 保存多任务模型到 {MODEL_FILE} ...")
    final_package = {
        "models": trained_models, # 这里面包含了3个模型
        "feature_names": list(X.columns)
    }
    joblib.dump(final_package, MODEL_FILE)
    print("全部完成！")

if __name__ == "__main__":
    train()