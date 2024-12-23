import glob
from itertools import product
import os
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd

from modules.common.labels import Labels
from modules.estimation.model import Model, ModelType
from preprocess import (
    export_csv,
    get_data_files,
    segment_and_extract_feature,
    split_motion_by_label,
    to_dataframe,
)
from train import smooth_result, smooth_results

top_k = 3
# test_data_group_list = [["4", "5"], ["6", "7"], ["8", "9"], ["10", "11"], ["12", "13"]]
test_data_group_list = [["4", "5"]]
model_types = ["randomforest", "xgboost", "lightgbm"]
# model_types = ["randomforest"]
segment_window_size_list = [60, 120, 180, 240, 300, 360, 420, 480, 540]
segment_gap_size_list = [10]
smooth_window_size_list = [60, 120, 180, 240, 300, 360, 420, 480, 540]

INPUT_DIR = "./data/input/each_process"
OUTPUT_BASE_DIR = "./data/output/all/each_process2"


# すべての組み合わせを返す
def all_combinations(*args):
    return list(product(*args))


def preprocess(window_size: int, gap_size: int, labels: Labels, output_dir: str):
    data_files_list = get_data_files(INPUT_DIR)

    for i, data_files in enumerate(data_files_list):
        output_path = os.path.join(output_dir, f"{data_files['name']}.csv")

        if os.path.exists(output_path):
            continue

        df = to_dataframe(data_files, labels)
        grouped_df_list = split_motion_by_label(df, labels)

        data_df = pd.DataFrame()
        for i, grouped_df in enumerate(grouped_df_list):
            # print(f">> to feature values: {i+1}/{len(grouped_df_list)}")
            feature_values_df = segment_and_extract_feature(
                grouped_df, window_size_frame=window_size, gap_size_frame=gap_size
            )
            data_df = pd.concat([data_df, feature_values_df])

        print(f">>> Export: {output_path}")
        export_csv(data_df, output_path)

    return output_dir


def load_data(data_dir: str, test_data_names: list[str]):
    """
    指定したディレクトリ内のデータを読み込む

    Parameters
    ----------
    data_dir : str
        データが保存されているディレクトリのパス
    test_data_name : str
        テストデータのフォルダ名

    Returns
    -------
    """

    train = pd.DataFrame()
    test = pd.DataFrame()

    file_paths = glob.glob(os.path.join(data_dir, "*.csv"))
    for file_path in file_paths:
        data_name = os.path.basename(file_path).split(".")[0]
        if data_name in ["pred", "pred_proba", "smoothed_pred_proba"]:
            continue

        try:
            df = pd.read_csv(file_path)
            if data_name in test_data_names:
                test = pd.concat([test, df], ignore_index=True)
            else:
                train = pd.concat([train, df], ignore_index=True)
        except pd.errors.EmptyDataError:
            continue

    x_train = train.drop("label", axis=1)
    y_train = train["label"]
    x_test = test.drop("label", axis=1)
    y_test = test["label"]

    return x_train, y_train, x_test, y_test


def train(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    labels: Labels,
    model_type: ModelType,
    output_dir: str,
    test_data_names: list[str],
):
    model_path = os.path.join(output_dir, f"{'-'.join(test_data_names)}_model_2.pkl")

    if os.path.exists(model_path):
        print(f">> Load model: {model_path}")
        clf = Model.load(model_path, model_type, num_class=len(labels))
        return clf

    clf = Model(model_type, num_class=len(labels))
    clf.fit(x_train, y_train)

    # モデルの保存
    clf.dump(model_path)

    return clf


def test(clf, x_test, y_test, smooth_window_size: int, k: int):
    pred = clf.predict(x_test)
    pred_proba = clf.predict_proba(x_test)

    # スムージング
    smoothed_pred = smooth_result(pred_proba, window_size=smooth_window_size)

    # 評価
    accurary = np.mean(pred == y_test)
    smoothed_accurary = np.mean(smoothed_pred == y_test[: len(smoothed_pred)])
    top_k = np.argsort(pred_proba, axis=1)[:, -k:]
    top_k_accurary = np.mean([y in top_k[i] for i, y in enumerate(y_test)])

    return accurary, smoothed_accurary, top_k_accurary, pred, pred_proba, smoothed_pred


def to_top_k_pred(pred_proba: np.ndarray, y_test: pd.Series, k: int):
    y_test_ = np.array(y_test)
    top_k = np.argsort(pred_proba, axis=1)[:, -k:]
    result = top_k[:, 0]

    # top_kのうち正解があればそれに置き換える
    mask = np.array([y_test_[i] in tk for i, tk in enumerate(top_k)])
    result[mask] = y_test_[mask]

    return result


def save_result(
    accuracy: float,
    smoothed_accurary: float,
    top_k_accurary: float,
    pred: np.ndarray,
    pred_proba: np.ndarray,
    smoothed_pred_proba: np.ndarray,
    output_dir: str,
):
    # pred を保存
    pred_file_path = os.path.join(output_dir, "pred.csv")
    print(f">> Save: {pred_file_path}")
    np.savetxt(pred_file_path, pred, delimiter=",")

    # pred_proba を保存
    pred_proba_file_path = os.path.join(output_dir, "pred_proba.csv")
    print(f">> Save: {pred_proba_file_path}")
    np.savetxt(pred_proba_file_path, pred_proba, delimiter=",")

    # smoothed_pred_proba を保存
    smoothed_pred_proba_file_path = os.path.join(output_dir, "smoothed_pred_proba.csv")
    print(f">> Save: {smoothed_pred_proba_file_path}")
    np.savetxt(
        smoothed_pred_proba_file_path,
        smoothed_pred_proba,
        delimiter=",",
    )

    # accuracy を保存
    result_file_path = os.path.join(output_dir, "result_4_5.txt")
    print(f">> Save: {result_file_path}")
    with open(result_file_path, "w") as f:
        print(f"accuracy: {accuracy}", file=f)
        print(f"smoothed_accurary: {smoothed_accurary}", file=f)
        print(f"top_k_accurary: {top_k_accurary}", file=f)


def load_result(output_dir: str):
    result_file_path = os.path.join(output_dir, "result.txt")
    result: dict[str, str | float] = {}

    if not os.path.exists(result_file_path):
        return result

    with open(result_file_path, "r") as f:
        lines = f.readlines()
        for line in lines:
            key_, value_ = line.split(":")
            key = key_.strip()
            value = value_.strip()
            result[key] = float(value)

    return result


def plot_result(y_test, pred: np.ndarray, labels: Labels, output_dir: str):
    plt.figure(figsize=(10, 3))
    plt.xlim(0, len(y_test))
    plt.ylim(0, 1)

    for i, label_id in enumerate(y_test):
        # y_testに合わせて背景色を設定
        plt.axvspan(i, i + 1, 0.5, 1, color=labels.color_by_id(label_id), alpha=0.5)

    # 予測結果をプロット
    for i, label_id in enumerate(pred):
        plt.axvspan(i, i + 1, 0, 0.5, color=labels.color_by_id(label_id))

    file_path = os.path.join(output_dir, "result.png")
    plt.savefig(file_path)
    print(f">> Save: {file_path}")


def plot_result_by_graph(
    y_test: pd.Series,
    pred: np.ndarray,
    labels: Labels,
    output_dir: str,
    file_name="result_graph.png",
):
    fontsize = 20
    line_width = 2

    plt.figure(figsize=(10, 4))

    x_pred = [x / 60 / 6 for x in np.arange(len(pred))]
    plt.step(
        x_pred,
        pred,
        where="post",
        label="予測",
        color="black",
        alpha=0.5,
        linewidth=line_width,
    )
    x_test = [x / 60 / 6 for x in np.arange(len(y_test))]
    plt.step(
        x_test,
        y_test,
        where="post",
        label="正解",
        color="blue",
        alpha=0.5,
        linewidth=line_width,
    )
    plt.xlim(0, max(x_pred + x_test))
    plt.grid(axis="both", linestyle="--", alpha=0.7)
    plt.xticks(np.arange(0, max(x_pred + x_test), 1), fontsize=fontsize)
    plt.yticks(range(len(labels)), labels.labels, fontsize=fontsize)
    plt.xlabel("時間[分]", fontsize=fontsize)

    file_path = os.path.join(output_dir, file_name)
    plt.tight_layout()
    plt.legend(fontsize=18, loc="upper left")
    plt.savefig(file_path)
    print(f">> Save: {file_path}")


def plot_one_graph(ax, title, pred, y_test, labels, fontsize=20, line_width=2):
    """
    1つのグラフをプロットします。

    Args:
        ax: matplotlib.axes.Axes オブジェクト
        pred: 予測値のリスト
        y_test: テストデータのリスト
        labels: ラベルのリスト
        fontsize: フォントサイズ (デフォルト: 20)
        line_width: 線幅 (デフォルト: 2)
    """

    x_pred = [x / 60 / 6 for x in np.arange(len(pred))]
    ax.step(
        x_pred,
        pred,
        where="post",
        label="予測",
        color="black",
        alpha=0.5,
        linewidth=line_width,
    )
    x_test = [x / 60 / 6 for x in np.arange(len(y_test))]
    ax.step(
        x_test,
        y_test,
        where="post",
        label="正解",
        color="blue",
        alpha=0.5,
        linewidth=line_width,
    )
    ax.set_title(title, fontsize=fontsize)
    ax.set_xlim(0, max(x_pred + x_test))
    ax.grid(axis="both", linestyle="--", alpha=0.7)
    ax.set_xticks(np.arange(0, max(x_pred + x_test), 1))
    ax.set_yticks(range(len(labels)), labels.labels)
    ax.set_xlabel("時間[分]", fontsize=fontsize)
    ax.tick_params(axis="both", which="major", labelsize=fontsize)
    ax.legend(fontsize=20, loc="upper left")


def plot_results_by_graph(
    title_list: list[str],
    pred_list: list[np.ndarray],
    y_test: pd.Series,
    labels: Labels,
    file_path: str,
    fontsize=22,
    line_width=2,
):
    """
    複数のグラフを1つの図にプロットします。

    Args:
        pred_list: 予測値のリストのリスト
        y_test: テストデータのリスト
        labels: ラベルのリスト
        output_dir: 出力ディレクトリ
        file_name: 出力ファイル名
        fontsize: フォントサイズ (デフォルト: 20)
        line_width: 線幅 (デフォルト: 2)
    """

    num_plots = len(pred_list)
    fig, axes = plt.subplots(nrows=num_plots, ncols=1, figsize=(10, 6 * num_plots))

    for i, (title, pred, ax) in enumerate(zip(title_list, pred_list, axes.flat)):
        plot_one_graph(ax, title, pred, y_test, labels, fontsize, line_width)

    plt.tight_layout()

    plt.savefig(file_path)
    print(f">> Save: {file_path}")


def main():
    labels = Labels(os.path.join(INPUT_DIR, "labels.csv"))

    for model_type, segment_wsize, segment_gsize, smooth_wsize in all_combinations(
        model_types,
        segment_window_size_list,
        segment_gap_size_list,
        smooth_window_size_list,
    ):
        smooth_wsize_min = int(smooth_wsize / segment_gsize)
        key = f"{model_type}_segmentw{segment_wsize}_segmentgap{segment_gsize}_smoothw{smooth_wsize}"
        if key not in [
            "xgboost_segmentw120_segmentgap10_smoothw360",
        ]:
            continue
        print(f"\n== {key} ==")

        output_dir = os.path.join(OUTPUT_BASE_DIR, key)
        os.makedirs(output_dir, exist_ok=True)

        # 前処理
        print("> Preprocess")
        data_dir = preprocess(segment_wsize, segment_gsize, labels, output_dir)

        # データの読み込み
        for test_data_names in test_data_group_list:
            print(f"> LoadData: {test_data_names}")
            x_train, y_train, x_test, y_test = load_data(data_dir, test_data_names)

            # 学習
            print("> Train")
            clf = train(
                x_train, y_train, labels, model_type, output_dir, test_data_names
            )

            # テスト
            print("> Test")
            (
                accuracy,
                smoothed_accurary,
                top_k_accurary,
                pred,
                pred_proba,
                smoothed_pred,
            ) = test(clf, x_test, y_test, smooth_wsize_min, top_k)

            # 以前の結果を読み込む
            result = load_result(output_dir)
            replace_accuracy = "accuracy" in result and result["accuracy"] > accuracy
            accuracy = result["accuracy"] if replace_accuracy else accuracy

            replace_smoothed_accurary = (
                "smoothed_accurary" in result
                and result["smoothed_accurary"] > smoothed_accurary
            )
            smoothed_accurary = (
                result["smoothed_accurary"]
                if replace_smoothed_accurary
                else smoothed_accurary
            )

            replace_top_k_accurary = (
                "top_k_accurary" in result and result["top_k_accurary"] > top_k_accurary
            )
            top_k_accurary = (
                result["top_k_accurary"] if replace_top_k_accurary else top_k_accurary
            )

            # 結果の保存
            print("> SaveResult")
            save_result(
                accuracy,
                smoothed_accurary,
                top_k_accurary,
                pred,
                pred_proba,
                smoothed_pred,
                output_dir,
            )

        # 結果のプロット
        print("> PlotResult")

        start = int(len(y_test) / 2)
        smooth_results_pred_proba = smooth_results(
            pred_proba, window_size=smooth_wsize_min
        )
        y_test_half = y_test[
            start + int(smooth_wsize_min / 2) : -int(smooth_wsize_min / 2)
        ]
        smoothed_top_1_pred_half = smooth_results_pred_proba[start:, 0]
        # to_top_k_pred(smooth_results_pred_proba[start:], y_test_half, 1)
        smoothed_top_3_pred_half = to_top_k_pred(smooth_results_pred_proba[start:], y_test_half, 3)
        plot_results_by_graph(
            ["XGboost の Top-1の結果", "XGboost の Top-3の結果"],
            [smoothed_top_1_pred_half, smoothed_top_3_pred_half],
            y_test_half,
            labels,
            file_path=f"/Users/satooru/Documents/kajilab/ipsj-cooking-action-recognition/images/{model_type}_top1_top3.png",  # "result_graph_top_k.png",
        )
        # plot_result_by_graph(
        #     y_test_half,
        #     smoothed_pred_half,
        #     labels,
        #     output_dir,
        #     file_name=f"/Users/satooru/Documents/kajilab/ipsj-cooking-action-recognition/images/{model_type}_top1.png",  # "result_graph_top_k.png",
        # )
        # # if replace_top_k_accurary:
        # plot_result_by_graph(
        #     y_test_half,
        #     top_k_pred_half,
        #     labels,
        #     output_dir,
        #     file_name=f"/Users/satooru/Documents/kajilab/ipsj-cooking-action-recognition/images/{model_type}_top3.png",  # "result_graph_top_k.png",
        # )


if __name__ == "__main__":
    main()
