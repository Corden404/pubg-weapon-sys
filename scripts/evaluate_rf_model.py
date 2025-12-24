"""随机森林（RF）模型测评与可视化（精简版）

面向“写报告”的最小输出集：
- 每个任务（weapon / distance / direction）的核心指标：
    accuracy / precision_macro / recall_macro / f1_macro
- 一张宏指标对比图（overview）
- 每个任务一张“归一化混淆矩阵”（normalized confusion matrix）

默认会优先使用 CSV 里的 dataset 划分（gun_sound_train / gun_sound_test），
这样更贴近你原始数据的训练/测试划分，避免不小心把同分布样本混到一起。

运行：
    python scripts/evaluate_rf_model.py
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

# 在无头环境（例如 CI 或容器）中使用非交互式后端，避免显示相关错误
import matplotlib

matplotlib.use("Agg")  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import seaborn as sns  # noqa: E402
from sklearn.ensemble import RandomForestClassifier  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split  # noqa: E402


DEFAULT_DATA = "data/processed/weapon_features_final.csv"
DEFAULT_MODEL = "data/processed/weapon_classifier.pkl"
DEFAULT_OUTPUT_DIR = "reports"
DEFAULT_TEST_DATASET_NAME = "gun_sound_test"


def _ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _select_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """按照训练时的规则选取数值特征并返回特征表与列名列表。

    实现细节：会剔除常见的标签或元数据列（如 weapon/distance/direction/dataset 等），
    然后仅保留数值类型的列，确保与训练脚本的特征相兼容。
    """

    drop_cols = ["weapon", "distance", "direction", "dataset", "id", "distance_label"]
    actual_drop = [c for c in drop_cols if c in df.columns]

    # 只保留数值列，防止字符串列被误当作特征
    x = df.drop(columns=actual_drop, errors="ignore").select_dtypes(include=[np.number])
    return x, list(x.columns)


def _maybe_split_by_dataset(
    df: pd.DataFrame,
    *,
    test_dataset_name: str,
) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    """如果 CSV 中含有 `dataset` 字段并能识别测试集名称，则返回 train/test 的布尔掩码。

    例如仓库中常见命名：gun_sound_train / gun_sound_test。若无法识别合适的划分，
    返回 None，调用方会退回到随机划分策略。
    """

    if "dataset" not in df.columns:
        return None

    dataset_values = df["dataset"].astype(str)
    test_mask = dataset_values.eq(test_dataset_name)

    # 训练集为非测试集的数据
    train_mask = ~test_mask

    if test_mask.sum() == 0:
        return None

    if train_mask.sum() == 0:
        return None

    return train_mask.to_numpy(), test_mask.to_numpy()


def _load_models(model_path: Path) -> Optional[Dict[str, Any]]:
    """加载由 `scripts/train_model.py` 保存的模型包。

    期望格式：
        {"models": {"weapon": clf, "distance": clf, "direction": clf}, "feature_names": [...]}
    """

    if not model_path.exists():
        return None

    try:
        pkg = joblib.load(model_path)
    except Exception:
        return None

    if isinstance(pkg, dict) and "models" in pkg:
        return pkg

    # 向后兼容：如果 pkl 里只保存了单个估计器，则当作 weapon 任务的模型处理。
    if hasattr(pkg, "predict"):
        return {"models": {"weapon": pkg}, "feature_names": None}

    return None


def _train_models(
    x_train: pd.DataFrame,
    y_train_by_task: Dict[str, pd.Series],
    *,
    n_estimators: int,
    random_state: int,
) -> Dict[str, RandomForestClassifier]:
    models: Dict[str, RandomForestClassifier] = {}
    for task, y_train in y_train_by_task.items():
        clf = RandomForestClassifier(
            n_estimators=n_estimators,
            n_jobs=-1,
            random_state=random_state,
        )
        clf.fit(x_train, y_train)
        models[task] = clf
    return models


def _plot_confusion_matrix(
    y_true: Iterable[Any],
    y_pred: Iterable[Any],
    *,
    labels: List[str],
    title: str,
    out_path: Path,
) -> None:
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    # 使用归一化混淆矩阵，方便在报告中直观展示每一类的误判分布
    with np.errstate(divide="ignore", invalid="ignore"):
        cm = cm.astype(float) / cm.sum(axis=1, keepdims=True)
        cm = np.nan_to_num(cm)

    # 标签较多时增加图像尺寸以保持可读性
    base = max(6.0, min(24.0, 0.45 * len(labels)))
    plt.figure(figsize=(base, base * 0.85))
    fmt = ".2f"

    ax = sns.heatmap(
        cm,
        annot=len(labels) <= 25,
        fmt=fmt,
        cmap="Blues",
        xticklabels=labels,
        yticklabels=labels,
        cbar=True,
    )
    ax.set_title(title)
    ax.set_xlabel("pred")
    ax.set_ylabel("true")
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()


def _evaluate_task(
    clf: Any,
    *,
    task: str,
    x_test: pd.DataFrame,
    y_test: pd.Series,
    out_dir: Path,
    run_id: str,
) -> Dict[str, Any]:
    y_pred = clf.predict(x_test)

    accuracy = float(accuracy_score(y_test, y_pred))
    precision_macro = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
    recall_macro = float(recall_score(y_test, y_pred, average="macro", zero_division=0))
    f1_macro = float(f1_score(y_test, y_pred, average="macro", zero_division=0))

    labels = sorted(pd.Series(list(y_test)).astype(str).unique().tolist())

    # Normalized confusion matrix
    _plot_confusion_matrix(
        y_test.astype(str),
        pd.Series(y_pred).astype(str),
        labels=labels,
        title=f"RF Confusion Matrix (normalized) - {task}",
        out_path=out_dir / f"rf_{run_id}_{task}_confusion_norm.png",
    )

    return {
        "task": task,
        "n_test": int(len(y_test)),
        "accuracy": accuracy,
        "precision_macro": precision_macro,
        "recall_macro": recall_macro,
        "f1_macro": f1_macro,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate RF metrics + key plots (report-friendly)")
    parser.add_argument("--data", default=DEFAULT_DATA, help="Path to features CSV")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Path to saved model pkl (optional)")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Where to write reports")
    parser.add_argument(
        "--test-dataset-name",
        default=DEFAULT_TEST_DATASET_NAME,
        help="Value in CSV column 'dataset' treated as test set",
    )
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--n-estimators", type=int, default=200)
    parser.add_argument(
        "--retrain",
        action="store_true",
        help="Ignore model file and retrain for evaluation",
    )

    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        raise SystemExit(f"CSV not found: {data_path}")

    out_dir = _ensure_dir(args.output_dir)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    df = pd.read_csv(data_path)
    x, feature_names = _select_features(df)

    targets: Dict[str, pd.Series] = {}
    for col in ("weapon", "distance", "direction"):
        if col in df.columns:
            targets[col] = df[col]

    if not targets:
        raise SystemExit("CSV does not contain any target columns: weapon/distance/direction")

    # Split: prefer the original train/test split if provided by feature extraction.
    dataset_split = _maybe_split_by_dataset(df, test_dataset_name=args.test_dataset_name)

    if dataset_split is not None:
        train_mask, test_mask = dataset_split
        x_train = x.loc[train_mask]
        x_test = x.loc[test_mask]
        y_train_by_task = {t: y.loc[train_mask] for t, y in targets.items()}
        y_test_by_task = {t: y.loc[test_mask] for t, y in targets.items()}
    else:
        # Fallback: stratify by weapon if possible.
        stratify = targets.get("weapon")
        x_train, x_test = train_test_split(
            x,
            test_size=0.2,
            random_state=args.random_state,
            stratify=stratify if stratify is not None else None,
        )
        y_train_by_task = {t: y.loc[x_train.index] for t, y in targets.items()}
        y_test_by_task = {t: y.loc[x_test.index] for t, y in targets.items()}

    # Try loading existing models. If it doesn't exist, we train models for evaluation.
    models: Dict[str, Any]
    loaded_pkg = None if args.retrain else _load_models(Path(args.model))

    if loaded_pkg is not None:
        models = dict(loaded_pkg["models"])

        # If the model package includes feature_names, align columns defensively.
        pkg_features = loaded_pkg.get("feature_names")
        if isinstance(pkg_features, list) and pkg_features:
            # Create missing columns as zeros and drop extra columns.
            for col in pkg_features:
                if col not in x_train.columns:
                    x_train[col] = 0.0
                if col not in x_test.columns:
                    x_test[col] = 0.0
            x_train = x_train[pkg_features]
            x_test = x_test[pkg_features]
            feature_names = pkg_features
    else:
        models = _train_models(
            x_train,
            y_train_by_task,
            n_estimators=args.n_estimators,
            random_state=args.random_state,
        )

    # Evaluate
    results: List[Dict[str, Any]] = []

    for task, y_test in y_test_by_task.items():
        clf = models.get(task)
        if clf is None:
            # If an old single-model pkl exists, we only have weapon; skip the rest.
            continue

        task_result = _evaluate_task(
            clf,
            task=task,
            x_test=x_test,
            y_test=y_test,
            out_dir=out_dir,
            run_id=run_id,
        )

        # Attach shared metadata once (kept in CSV for report tables).
        task_result["n_train"] = int(len(x_train))
        task_result["used_dataset_split"] = bool(dataset_split is not None)
        results.append(task_result)

    metrics_df = pd.DataFrame(results)
    metrics_df.to_csv(out_dir / f"rf_{run_id}_metrics.csv", index=False)

    # Plot macro metrics overview
    if not metrics_df.empty:
        plot_df = metrics_df[["task", "accuracy", "precision_macro", "recall_macro", "f1_macro"]]
        plot_df = plot_df.melt(id_vars=["task"], var_name="metric", value_name="value")

        plt.figure(figsize=(9, 4.8))
        ax = sns.barplot(data=plot_df, x="task", y="value", hue="metric")
        ax.set_title("RandomForest metrics (macro)")
        ax.set_ylim(0.0, 1.0)
        plt.tight_layout()
        plt.savefig(out_dir / f"rf_{run_id}_metrics_overview.png", dpi=160)
        plt.close()

    # Console summary (friendly when running locally)
    print("\n=== RF evaluation summary ===")
    print(f"run_id: {run_id}")
    print(f"output_dir: {out_dir}")
    print(f"used_dataset_split: {dataset_split is not None}")
    for r in results:
        print(
            f"- {r['task']}: acc={r['accuracy']:.4f}, "
            f"p_macro={r['precision_macro']:.4f}, r_macro={r['recall_macro']:.4f}, f1_macro={r['f1_macro']:.4f} "
            f"(n_test={r['n_test']})"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
