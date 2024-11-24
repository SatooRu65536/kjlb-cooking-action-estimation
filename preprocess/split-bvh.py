from mcp_persor import BVHparser
from glob import glob
import pandas as pd
import json
import re
from os import path, makedirs
import shutil

INPUT_DIR = "data/input/"
OUTPUT_DIR = "data/train/"
TEST_FILE = "data/input/13/motion.csv"

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


def remove_output_dir():
    if path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    makedirs(OUTPUT_DIR)


def load_labels(label_define_file: str) -> list[str]:
    with open(label_define_file) as f:
        text = f.read()
        re_text = re.sub(r"/\*[\s\S]*?\*/|//[^\"\]\,\[]*\n", "\n", text)
        labels = json.loads(re_text)["labels"]

    return labels


def load_files(bvh_file: str) -> tuple[pd.DataFrame, list[str], str]:
    dir = path.dirname(bvh_file)
    label_file = path.join(dir, "label.csv")

    if not path.exists(label_file):
        print(f"Label file not found: {label_file}")
        raise FileNotFoundError

    labels = load_labels(glob(f"{dir}/*.jsonc")[0])

    bvhp = BVHparser(bvh_file)
    motion_df = bvhp.get_motion_df()
    label_df = pd.read_csv(label_file, names=["label"])

    df = pd.concat([motion_df, label_df], axis=1)

    return df, labels, dir


def split_motion_by_label(df: pd.DataFrame, labels: list[str], dir: str) -> list:
    groups = [group for _, group in df.groupby(["label"])]

    df_group_by_label: list = []
    for group in groups:
        label_index = int(group["label"].iloc[0])
        label = labels[label_index - 1] if label_index <= len(labels) else "その他"

        parent_dir = path.basename(dir)
        output_dir = f"{OUTPUT_DIR}/{parent_dir}"
        output_file = f"{label_index}_{label}.csv"

        df_group_by_label.append(
            {"df": group, "output_path": output_dir, "output_file": output_file}
        )

    return df_group_by_label


def to_feature_values(
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
    window_size : int, optional
        ウィンドウサイズ, by default 100
    gap : int, optional
        ウィンドウの間隔, by default 10
    """

    feature_values_df = pd.DataFrame()

    end = len(df) - window_size_frame
    for i in range(0, end, gap_size_frame):
        part_df = df.iloc[i : i + window_size_frame]

        # 上半身のスケルトンの平均
        upper_joint_keys = [
            "torso_1",
            "torso_2",
            "torso_3",
            "torso_4",
            "torso_5",
            "torso_6",
            "torso_7",
            "l_shoulder",
            "l_up_arm",
            "l_low_arm",
            "l_hand",
            "r_shoulder",
            "r_up_arm",
            "r_low_arm",
            "r_hand",
        ]
        upper_joint_columns = [
            f"{j}_{k}" for j in upper_joint_keys for k in BVH_CHANNELS["ALL"]
        ]
        upper_part_df = part_df[upper_joint_columns]
        upper_part_df_avg = upper_part_df.mean()
        upper_part_df_var = upper_part_df.var()

        # 位置の平均
        position_columns = [f"root_{c}" for c in BVH_CHANNELS["ALL"]]
        position_part_df = part_df[position_columns]
        position_part_df_avg = position_part_df.mean()
        position_part_df_var = position_part_df.var()

        # feature_values_df に追加
        line = (
            pd.concat(
                [
                    upper_part_df_avg,  # 上半身の平均
                    upper_part_df_var,  # 上半身の分散
                    position_part_df_avg,  # 位置の平均
                    position_part_df_var,  # 位置の分散
                ],
            )
            .to_frame()
            .T
        )
        line.columns = list(map(lambda x: f"{x[1]}-{x[0]}", enumerate(line.columns)))
        feature_values_df = pd.concat([feature_values_df, line])

    return feature_values_df


def export_csv(df: pd.DataFrame, output_dir: str, output_file: str):
    if not path.exists(output_dir):
        makedirs(output_dir)

    output_path = path.join(output_dir, output_file)
    df.to_csv(output_path, index=False)


def main():
    bvh_files = glob(path.join(INPUT_DIR, "**/*.bvh")) + glob(
        path.join(INPUT_DIR, "**/*.BVH")
    )

    for bvh_file in bvh_files:
        print(f"\n--- {bvh_file} ---")
        try:
            df, labels, dir = load_files(bvh_file)
        except FileNotFoundError:
            continue
        export_csv(df, dir, "motion.csv")
        df_group_by_label = split_motion_by_label(df, labels, dir)

        for g in df_group_by_label:
            print(f"Export: {g['output_file']}")
            feature_values_df = to_feature_values(g["df"])
            export_csv(feature_values_df, g["output_path"], g["output_file"])


if __name__ == "__main__":
    remove_output_dir()
    main()
