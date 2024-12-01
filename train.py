import pandas as pd
import os
import glob
import shutil
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report

from modules.common.labels import Labels
from modules.estimation.model import Model, ModelType

TRAIN_DIR = "./data/output/none_other/"
LABEL_FILE = "./data/input/labels.csv"
MODEL_DIR = "./models/"


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

    x_test = pd.DataFrame()
    y_test = pd.DataFrame()
    x_train = pd.DataFrame()
    y_train = pd.DataFrame()

    for data_name, df in data.items():
        if data_name == test_data_name:
            x_test = df.drop(label_col, axis=1)
            y_test = df[label_col]
        else:
            x_train = pd.concat([x_train, df.drop(label_col, axis=1)])
            y_train = pd.concat([y_train, df[label_col]])

    # 学習
    clf.fit(df.drop(label_col, axis=1), df[label_col])

    # テスト
    pred = clf.predict(x_test)
    accuracy = (pred == y_test).sum() / len(y_test)

    return clf, pred, accuracy, y_test


def main():
    labels = Labels(LABEL_FILE)
    data = load_data(TRAIN_DIR)

    model_types = ["randomforest"]
    # model_types = ["randomforest", "xgboost", "lightgbm"]
    for i, model_type in enumerate(model_types):
        print(f"--- {model_type}[{i+1}/{len(model_types)}] ---")

        for j, data_name in enumerate(data.keys()):
            print(f"- {data_name:5}[{j+1}/{len(data.keys())}]")
            clf, pred, accuracy, y_test = train_and_test(
                data, labels, model_type, data_name
            )
            # print(classification_report(y_test, pred, zero_division=0))
            clf.dump(os.path.join(MODEL_DIR, f"{model_type}_{data_name}.pkl"))


def remove_output_dir():
    if os.path.exists(MODEL_DIR):
        shutil.rmtree(MODEL_DIR)
    os.makedirs(MODEL_DIR)


if __name__ == "__main__":
    remove_output_dir()
    main()
