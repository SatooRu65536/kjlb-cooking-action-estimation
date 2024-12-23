import pandas as pd
import os
import glob
import shutil
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import argparse
import japanize_matplotlib
from sklearn.model_selection import train_test_split

from modules.common.labels import Labels
from modules.estimation.model import Model, ModelType

parser = argparse.ArgumentParser()
parser.add_argument("--key", type=str, default="default")
args = parser.parse_args()

KEY = args.key

TRAIN_DIR = os.path.join("./data/output/", KEY)
LABELS_FILE = os.path.join("./data/input/", KEY, "labels.csv")
MODEL_DIR = os.path.join("./models/", KEY)


def load_data(dir: str, filename="output.csv") -> dict[str, pd.DataFrame]:
    """
    指定したディレクトリ内のデータを読み込む

    Parameters
    ----------
    dir : str
        データが保存されているディレクトリのパス
    filename : str
        データのファイル名

    Returns
    -------
    data : dict
        データ
    """

    data: dict[str, pd.DataFrame] = {}

    # dir 以下のフォルダを取得
    dirs = glob.glob(f"{dir}/*")
    for dir in dirs:
        data_name = os.path.basename(dir)
        data_path = os.path.join(dir, filename)
        try:
            data[data_name] = pd.read_csv(data_path)
        except pd.errors.EmptyDataError:
            continue

    return data


def train_and_test(
    data: dict[str, pd.DataFrame],
    labels: Labels,
    type: ModelType,
    test_data_name: str,
    label_col="label",
    smooth_window_size=1 * 60,
):
    """
    モデルを学習する

    Parameters
    ----------
    data : dict
        データ
    labels : Labels
        ラベル
    type : ModelType
        モデルの種類
    label_col : str
        ラベルの列名
    """

    # モデルの定義
    clf = Model(type, num_class=len(labels))

    x_train = pd.DataFrame()
    y_train = pd.Series()
    x_test = pd.DataFrame()
    y_test = pd.Series()

    for data_name, df in data.items():
        if data_name == test_data_name:
            x_test = df.drop(label_col, axis=1)
            y_test = df[label_col]
        elif y_train.empty or x_train.empty:
            x_train = df.drop(label_col, axis=1)
            y_train = df[label_col]
        else:
            x_train = pd.concat([x_train, df.drop(label_col, axis=1)])
            y_train = pd.concat([y_train, df[label_col]])

    # 学習
    print(f"train data: {len(x_train)}")
    clf.fit(x_train, y_train)

    # テスト
    print(f"test data: {len(x_test)}")
    pred = clf.predict(x_test)
    pred_proba = clf.predict_proba(x_test)

    # スムージング
    smoothed_pred_proba = smooth_result(pred_proba, window_size=smooth_window_size)

    # 評価
    accuracy = np.mean(pred == y_test)

    return pred, pred_proba, smoothed_pred_proba, accuracy, y_test


def smooth_result(pred_proba, window_size=1 * 60):
    result = []

    for i in range(len(pred_proba) - window_size):
        part = pred_proba[i : i + window_size]
        # 縦方向に足す
        part_sum = np.sum(part, axis=0)
        # 最大値のインデックスを取得
        max_index = np.argmax(part_sum)
        result.append(max_index)

    return np.array(result)


def smooth_results(pred_proba: np.ndarray, window_size=1 * 60):
    result: list[list[int]] = []

    for i in range(len(pred_proba) - window_size):
        part = pred_proba[i : i + window_size]
        # 縦方向に足す
        part_sum = np.sum(part, axis=0)
        # 大きい順に追加
        result.append(list(np.argsort(part_sum)[::-1]))

    return np.array(result)


def print_classification_report(y_test, pred):
    print(classification_report(y_test, pred, zero_division=0))


def print_top_k_precision(y_true, pred_proba, k=3):
    top_k_preds = np.argsort(pred_proba, axis=1)[:, -k:]
    correct_preds = np.array([y_true[i] in top_k_preds[i] for i in range(len(y_true))])
    print(f"top-{k} precision: {np.mean(correct_preds)}")


def plot_color_map(labels: Labels, filename="color_map.png"):
    color_dict = labels.color_dict()

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, len(color_dict))
    ax.axis("off")

    # 各色とラベルを描画
    for i, (label, color) in enumerate(color_dict.items()):
        rect = mpatches.Rectangle((0, i), 0.1, 0.8, color=color)
        ax.add_patch(rect)
        ax.text(0.15, i + 0.4, label, va="center", ha="left", fontsize=10)

    print(f"export: {filename}")
    plt.savefig(filename)


def plot_result(y_test, pred: np.ndarray, labels: Labels, file_path="result.png"):
    plt.figure(figsize=(10, 3))
    plt.xlim(0, len(y_test))
    plt.ylim(0, 1)

    for i, label_id in enumerate(y_test):
        # y_testに合わせて背景色を設定
        plt.axvspan(i, i + 1, 0.5, 1, color=labels.color_by_id(label_id), alpha=0.5)

    # 予測結果をプロット
    for i, label_id in enumerate(pred):
        plt.axvspan(i, i + 1, 0, 0.5, color=labels.color_by_id(label_id))

    print(f"export: {file_path}")
    plt.savefig(file_path)


def plot_result_top_k(y_test, pred_proba, labels: Labels, k=3, filename="result.png"):
    top_k_preds = np.argsort(pred_proba, axis=1)[:, -k:]

    plt.figure(figsize=(10, 3))
    plt.xlim(0, len(y_test))
    plt.ylim(0, 1)

    split_range = 1 / (k + 1)

    for i, label_id in enumerate(y_test):
        # y_testに合わせて背景色を設定
        plt.axvspan(
            i, i + 1, 0, split_range, color=labels.color_by_id(label_id), alpha=0.5
        )

    # 予測結果をプロット
    for i in range(k):
        for j, label_id in enumerate(top_k_preds[:, i]):
            plt.axvspan(
                j,
                j + 1,
                split_range * (i + 1),
                split_range * (i + 2),
                color=labels.color_by_id(label_id),
            )

    print(f"export: {filename}")
    plt.savefig(filename)


def main():
    labels = Labels(LABELS_FILE)
    data = load_data(TRAIN_DIR)

    print(f"--- COLOR MAP ---")
    plot_color_map(labels, filename=f"zzz/{KEY}color_map.png")
    color_dict = labels.color_dict()
    for label, color in color_dict.items():
        print(f"- {label}: {color}")

    # model_types = ["randomforest"]
    model_types = ["randomforest", "xgboost", "lightgbm"]
    for i, model_type in enumerate(model_types):
        print(f"--- {model_type}[{i+1}/{len(model_types)}] ---")
        data_name = "4"

        pred, pred_proba, smoothed_pred_proba, accuracy, y_test = train_and_test(
            data, labels, model_type, data_name
        )
        print(f"accuracy: {accuracy}")
        plot_result(
            y_test,
            pred,
            labels,
            filename=f"zzz/{KEY}/result_{model_type}_{data_name}.png",
        )
        plot_result(
            y_test,
            smoothed_pred_proba,
            labels,
            filename=f"zzz/{KEY}/smoothed_result_{model_type}_{data_name}.png",
        )


def remove_output_dir():
    if os.path.exists(MODEL_DIR):
        shutil.rmtree(MODEL_DIR)
    os.makedirs(MODEL_DIR)


if __name__ == "__main__":
    remove_output_dir()
    main()
