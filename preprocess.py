import os
import json
import shutil
import pandas as pd
from mcp_persor import BVHparser
import argparse

from modules.common.labels import Labels

parser = argparse.ArgumentParser()
parser.add_argument("--key", type=str, default="default")
parser.add_argument("--pick", type=str)
args = parser.parse_args()

KEY = args.key
PICK_DIR = args.pick

INPUT_DIR = os.path.join("./data/input/", KEY)
OUTPUT_DIR = os.path.join("./data/output/", KEY)

BVH_CHANNELS = {
    "POSITION": ["Xposition", "Yposition", "Zposition"],
    "ROTATION": ["Zrotation", "Xrotation", "Yrotation"],
    "ALL": [
        "Xposition",
        "Yposition",
        "Zposition",
        "Zrotation",
        "Xrotation",
        "Yrotation",
    ],
}


def get_data_files(input_dir: str) -> list[dict[str, str]]:
    """
    データファイルのパスを取得する

    Parameters
    ----------
    input_dir : str
        データファイルが格納されているディレクトリのパス

    Returns
    -------
    source_dirs : list
        データファイルが格納されているディレクトリのリスト
    """

    dirs = os.listdir(input_dir)

    # 各ディレクトリに "label.json" と "motion.bvh" があるか確認
    data_files_list = []
    for dir in dirs:
        label_path = os.path.join(input_dir, dir, "label.json")
        motion_path = os.path.join(input_dir, dir, "motion.bvh")

        if not os.path.exists(label_path) or not os.path.exists(motion_path):
            continue

        data_name = os.path.basename(dir)

        if PICK_DIR is not None and data_name != PICK_DIR:
            continue

        data_files_list.append(
            {"label": label_path, "motion": motion_path, "name": data_name}
        )

    return data_files_list


def to_dataframe(data_files: dict[str, str], labels: Labels) -> pd.DataFrame:
    """
    データファイルを DataFrame に変換する

    Parameters
    ----------
    data_files : list
        データファイルのリスト

    Returns
    -------
    df : DataFrame
        データファイルを結合した DataFrame
    """

    bvhp = BVHparser(data_files["motion"])
    motion_df = bvhp.get_motion_df()
    frame_rate = 1 / bvhp.frame_time

    # motion_df にラベルを追加
    motion_df["label"] = labels.other_id()

    with open(data_files["label"]) as f:
        content = json.load(f)
        tricks = content[0]["tricks"]

    for trick in tricks:
        start_s = trick["start"]
        end_s = trick["end"]
        label = trick["labels"][0]
        label_id = labels.id(label)

        start = int(start_s * frame_rate)
        end = int(end_s * frame_rate)

        motion_df.loc[start:end, "label"] = label_id

    return motion_df


def split_motion_by_label(df: pd.DataFrame, labels: Labels) -> list[pd.DataFrame]:
    """
    ラベルごとにデータを分割する

    Parameters
    ----------
    df : DataFrame
        ラベルが追加された DataFrame

    Returns
    -------
    df_group_by_label : list[pd.DataFrame]
        ラベルごとに分割された DataFrame のリスト
    """

    df["group"] = (df["label"] != df["label"].shift()).cumsum()
    grouped_df_list = [group for _, group in df.groupby(["label", "group"])]

    # group 列を削除
    for grouped_df in grouped_df_list:
        label = grouped_df["label"].iloc[0]
        if label == labels.unuse_id():
            continue

        grouped_df.drop(columns=["group"], inplace=True)

    return grouped_df_list


def get_index_names(index: pd.Index | pd.MultiIndex, suffix: str) -> list[str]:
    """
    DataFrame のインデックス名を取得する

    Parameters
    ----------
    index : pd.Index or pd.MultiIndex
        インデックス
    suffix : str
        インデックス名に付けるサフィックス

    Returns
    -------
    index_names : list
        インデックス名のリスト
    """

    return list(
        map(
            lambda x: f"{x}-{suffix}",
            index,
        )
    )


def segment_and_extract_feature(
    df: pd.DataFrame,
    window_size_frame=3 * 60,  # ウィンドウサイズ
    gap_size_frame=1 * 1,  # ウィンドウの間隔
) -> pd.DataFrame:
    """
    スケルトンのDaraFrameを特徴量のDataFrameに変換する

    Parameters
    ----------
    df : pd.DataFrame
        スケルトンのDataFrame
    window_size_frame: int, optional
        ウィンドウサイズ, by default 100
    gap_size_frame: int, optional
        ウィンドウの間隔, by default 10
    """

    feature_values_df = pd.DataFrame()

    end = len(df) - window_size_frame
    for i in range(0, end, gap_size_frame):
        part_df = df.iloc[i : i + window_size_frame]
        ## 平均
        pos_part_df_avg = part_df.mean()
        pos_part_avg_names = get_index_names(pos_part_df_avg.index, "pos-avg")
        ## 分散
        pos_part_df_var = part_df.var()
        pos_part_var_names = get_index_names(pos_part_df_var.index, "pos-var")
        ## 標準偏差
        pos_part_df_std = part_df.std()
        pos_part_std_names = get_index_names(pos_part_df_std.index, "pos-std")
        ## 最大値と最小値の差
        pos_part_df_range = part_df.max() - part_df.min()
        pos_part_range_names = get_index_names(pos_part_df_range.index, "pos-range")

        line = (
            pd.concat(
                [
                    pos_part_df_avg,
                    pos_part_df_var,
                    pos_part_df_std,
                    pos_part_df_range,
                ],
            )
            .to_frame()
            .T
        )
        line.columns = (
            pos_part_avg_names
            + pos_part_var_names
            + pos_part_std_names
            + pos_part_range_names
        )

        # 最も多いラベルを取得
        label = part_df["label"].mode().iloc[0]
        line["label"] = label

        feature_values_df = pd.concat([feature_values_df, line])

    # for i in range(0, end, gap_size_frame):
    #     part_df = df.iloc[i : i + window_size_frame]

    #     # 上半身のスケルトン
    #     upper_joint_keys = [
    #         "torso_1",
    #         "torso_2",
    #         "torso_3",
    #         "torso_4",
    #         "torso_5",
    #         "torso_6",
    #         "torso_7",
    #         "l_shoulder",
    #         "l_up_arm",
    #         "l_low_arm",
    #         "l_hand",
    #         "r_shoulder",
    #         "r_up_arm",
    #         "r_low_arm",
    #         "r_hand",
    #     ]
    #     upper_joint_columns = [
    #         f"{j}_{k}" for j in upper_joint_keys for k in BVH_CHANNELS["ALL"]
    #     ]
    #     upper_part_df = part_df[upper_joint_columns]
    #     ## 平均
    #     upper_part_df_avg = upper_part_df.mean()
    #     upper_part_avg_names = get_index_names(upper_part_df_avg.index, "upper-avg")
    #     ## 分散
    #     upper_part_df_var = upper_part_df.var()
    #     upper_part_var_names = get_index_names(upper_part_df_var.index, "upper-var")
    #     ## 標準偏差
    #     upper_part_df_std = upper_part_df.std()
    #     upper_part_std_names = get_index_names(upper_part_df_std.index, "upper-std")
    #     ## 最大値と最小値の差
    #     upper_part_df_range = upper_part_df.max() - upper_part_df.min()
    #     upper_part_range_names = get_index_names(
    #         upper_part_df_range.index, "upper-range"
    #     )

    #     # 位置
    #     position_columns = [f"root_{c}" for c in BVH_CHANNELS["ALL"]]
    #     pos_part_df = part_df[position_columns]
    #     ## 平均
    #     pos_part_df_avg = pos_part_df.mean()
    #     pos_part_avg_names = get_index_names(pos_part_df_avg.index, "pos-avg")
    #     ## 分散
    #     pos_part_df_var = pos_part_df.var()
    #     pos_part_var_names = get_index_names(pos_part_df_var.index, "pos-var")
    #     ## 標準偏差
    #     pos_part_df_std = pos_part_df.std()
    #     pos_part_std_names = get_index_names(pos_part_df_std.index, "pos-std")
    #     ## 最大値と最小値の差
    #     pos_part_df_range = pos_part_df.max() - pos_part_df.min()
    #     pos_part_range_names = get_index_names(pos_part_df_range.index, "pos-range")

    #     line = (
    #         pd.concat(
    #             [
    #                 upper_part_df_avg,
    #                 upper_part_df_var,
    #                 upper_part_df_std,
    #                 upper_part_df_range,
    #                 pos_part_df_avg,
    #                 pos_part_df_var,
    #                 pos_part_df_std,
    #                 pos_part_df_range,
    #             ],
    #         )
    #         .to_frame()
    #         .T
    #     )
    #     line.columns = (
    #         upper_part_avg_names
    #         + upper_part_var_names
    #         + upper_part_std_names
    #         + upper_part_range_names
    #         + pos_part_avg_names
    #         + pos_part_var_names
    #         + pos_part_std_names
    #         + pos_part_range_names
    #     )

    #     # 最も多いラベルを取得
    #     label = part_df["label"].mode().iloc[0]
    #     line["label"] = label

    #     feature_values_df = pd.concat([feature_values_df, line])

    return feature_values_df


def export_csv(df: pd.DataFrame, output_path: str):
    """
    DataFrame を CSV ファイルに出力する

    Parameters
    ----------
    df : pd.DataFrame
        出力する DataFrame
    output_path : str
        出力するファイルのパス

    Returns
    -------
    None
    """

    output_dir = os.path.dirname(output_path)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    df.to_csv(output_path, index=False)


def main():
    labels = Labels(os.path.join(INPUT_DIR, "labels.csv"))
    data_files_list = get_data_files(INPUT_DIR)

    for i, data_files in enumerate(data_files_list):
        print(f"\n--- [{i + 1}/{len(data_files_list)}] {data_files['name']} ---")
        print(f"- label: {data_files['label']}")
        print(f"- motion: {data_files['motion']}")

        df = to_dataframe(data_files, labels)
        grouped_df_list = split_motion_by_label(df, labels)

        train_df = pd.DataFrame()
        for i, grouped_df in enumerate(grouped_df_list):
            print(f"> to feature values: {i+1}/{len(grouped_df_list)}")
            feature_values_df = segment_and_extract_feature(
                grouped_df, window_size_frame=240, gap_size_frame=1
            )
            train_df = pd.concat([train_df, feature_values_df])

        output_path = os.path.join(OUTPUT_DIR, data_files["name"], "output.csv")
        print(f">> Export: {output_path}")
        export_csv(train_df, output_path)


def remove_output_dir():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)


if __name__ == "__main__":
    if PICK_DIR is None:
        remove_output_dir()
    main()
