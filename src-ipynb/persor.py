import pandas as pd
import numpy as np
import time


class BVHparser:
    def __init__(self, filename):
        self.bvh = self.__readfile(filename)

        lines = self.bvh.split("\n")

        hierarchy_tokens = self.__get_hierarchy_tokens(lines)
        (skeleton, root) = self.__get_joint(hierarchy_tokens)
        self.skeleton = skeleton
        self.root = root
        self.channels = self.__get_channels()

        (frame_time, motion) = self.__get_motion(lines)

        self.frame_time = frame_time
        self.default_motion_df = self.__convert_default_motion_df(motion)
        self.motion_df = self.default_motion_df.copy()

    def __readfile(self, filename):
        """
        BVHファイルを読み込む

        Parameters
        ----------
        filename : str
            BVHファイルのパス
        """

        with open(filename, "r") as f:
            return f.read()

    def __try_to_float(self, s):
        """
        文字列をfloatに変換する. 変換できない場合はNoneを返す

        Parameters
        ----------
        s : str
            変換する文字列

        Returns
        -------
        float or None
            変換後の値
        """

        try:
            return float(s)
        except ValueError:
            return None

    def __get_hierarchy_tokens(self, lines):
        """
        BVHファイルからHierarchy部をトークンごとの配列に変換する

        Parameters
        ----------
        lines : list
            BVHファイルの行データ

        Returns
        -------
        list
            階層構造のトークン
        """

        tokens = []
        index = 0
        nesting_level = 0
        is_closeing = False

        for i in range(len(lines)):
            line = lines.pop(0)
            tokens += line.split()
            nesting_level += line.count("{") - line.count("}")
            index += 1
            if line.count("}") > 0:
                is_closeing = True
            if nesting_level == 0 and is_closeing:
                break

        return tokens

    def __get_joint(self, tokens):
        """
        トークン配列からJointデータを取得する

        Parameters
        ----------
        tokens : list
            Hierarchy部のトークン

        Returns
        -------
        dict
            Jointデータ
        """

        skeleton = {}
        joint_name = None
        root = None
        joint_list = []

        next_id = 0
        for i in range(len(tokens)):
            if tokens[i] == "{":
                joint_list.append(joint_name)
            elif tokens[i] == "}":
                joint_list.pop()

            if tokens[i] == "ROOT":
                root = tokens[i + 1]
                joint_name = tokens[i + 1]
                skeleton[tokens[i + 1]] = {
                    "id": next_id,
                    "joint": None,
                    "children": [],
                    "offset": [],
                    "channels": [],
                }
                next_id += 1
            elif tokens[i] == "JOINT":
                joint_name = tokens[i + 1]
                skeleton[joint_list[-1]]["children"].append(tokens[i + 1])
                skeleton[tokens[i + 1]] = {
                    "id": next_id,
                    "joint": joint_list[-1],
                    "children": [],
                    "offset": [],
                    "channels": [],
                }
                next_id += 1
            elif tokens[i] == "OFFSET":
                index = i + 1
                while self.__try_to_float(tokens[index]) != None:
                    offset = self.__try_to_float(tokens[index])
                    skeleton[joint_name]["offset"].append(offset)
                    index += 1
                i = index - 1
            elif tokens[i] == "CHANNELS":
                channels_num = int(tokens[i + 1])
                for index in range(i + 2, i + 2 + channels_num):
                    skeleton[joint_name]["channels"].append(tokens[index])
                i += channels_num + 1
            elif tokens[i] == "End":
                joint_name = f"_End_{joint_name}"
                skeleton[joint_name] = {
                    "id": -1,
                    "joint": joint_name,
                    "children": [],
                    "offset": [],
                    "channels": [],
                }

        return (skeleton, root)

    def __get_channels(self):
        """
        チャンネル名のリストを取得する

        Returns
        -------
        list
            チャンネル名のリスト
        """

        channels = []
        for j in self.skeleton.keys():
            channels += [f"{j}_{c}" for c in self.skeleton[j]["channels"]]

        return channels

    def __get_motion(self, lines):
        """
        行ごとの配列からモーションデータを取得する

        Parameters
        ----------
        tokens : list
            Motion部のトークン

        Returns
        -------
        list
            モーションデータ
        """

        motion = []
        frame_time = None
        for i in range(len(lines)):
            if "MOTION" in lines[i]:
                continue
            elif "Frames:" in lines[i]:
                continue
            elif "Frame Time:" in lines[i]:
                frame_time = self.__try_to_float(lines[i].split(":")[-1])
            else:
                motion += [self.__try_to_float(v) for v in lines[i].split()]

        n = len(self.channels)
        new_motion = [motion[i : i + n] for i in range(0, len(motion), n)]

        return (frame_time, new_motion)

    def __convert_default_motion_df(self, motion):
        """
        モーションの二次元配列からデータフレームに変換する

        Returns
        -------
        pandas.DataFrame
            モーションデータ
        """

        motion_df = pd.DataFrame(motion)
        motion_df.columns = self.channels
        time = np.arange(0, motion_df.shape[0]) * self.frame_time  # type: ignore
        motion_df.insert(0, "time", time)
        for column in motion_df.columns:
            motion_df[column] = pd.to_numeric(motion_df[column], errors="coerce")

        return motion_df

    def __get_joint_columns(self, joint):
        """
        データフレームから指定したjointに関連するカラムを取得する

        Returns
        -------
        pandas.DataFrame
            モーションデータ
        """

        columns = self.motion_df.filter(like=joint).columns
        return columns

    def __get_skeleton_str(self, joint):
        """
        骨格オブジェクトを取得する

        Returns
        -------
        dict
            骨格オブジェクト
        """

        root_or_joint = "ROOT" if joint == self.root else "JOINT"
        offset = self.skeleton[joint]["offset"]
        channels = self.skeleton[joint]["channels"]
        children = self.skeleton[joint]["children"]

        children_str = ""
        if len(children) > 0:
            children_str = "\n".join(
                [self.__get_skeleton_str(child) for child in children]
            )
        else:
            end_offset = " ".join(map(str, self.skeleton[f"_End_{joint}"]["offset"]))
            children_str = f"End Site\n{{\nOFFSET {end_offset}\n}}"

        return (
            f"{root_or_joint} {joint}\n{{\n"
            + f'OFFSET {" ".join(map(str, offset))}\n'
            + f'CHANNELS {len(channels)} {" ".join(map(str, channels))}\n'
            + f"{children_str}\n}}"
        )

    def __get_columns(self, joint):
        """
        カラム名一覧を取得する

        Returns
        -------
        list
            カラム名一覧
        """

        children = self.skeleton[joint]["children"]
        channels = self.skeleton[joint]["channels"]
        channels = [f"{joint}_{c}" for c in channels]

        if len(children) > 0:
            return channels + sum([self.__get_columns(child) for child in children], [])
        else:
            return channels

    def __get_relative_motion_df(self, joint):
        """
        相対的な関節のモーションデータを取得する

        Returns
        -------
        pandas.DataFrame
            モーションデータ
        """

        columns = self.__get_joint_columns(joint)
        joint_motion_df = self.get_motion_df()[["time", *columns]]

        # カラム名から {joint}_ を削除
        columns = joint_motion_df.columns
        joint_motion_df.columns = [c.replace(f"{joint}_", "") for c in columns]

        return joint_motion_df

    def __get_absolute_motion_df(self, joint):
        """
        絶対的な関節のモーションデータを取得する

        Returns
        -------
        pandas.DataFrame
            モーションデータ
        """

        motion_df = self.get_motion_df()
        path = self.get_skeleton_path2root(joint)

        joint_columns = self.__get_joint_columns(joint)
        joint_motion_df = motion_df[joint_columns]
        joint_motion_df.columns = [
            c.replace(f"{joint}_", "") for c in joint_motion_df.columns
        ]

        for i in range(1, len(path)):
            path_columns = self.__get_joint_columns(path[i])
            path_motion_df = motion_df[path_columns]
            path_motion_df.columns = [
                c.replace(f"{path[i]}_", "") for c in path_motion_df.columns
            ]

            joint_motion_df += path_motion_df

        joint_motion_df.insert(0, "time", motion_df["time"])

        return joint_motion_df

    def __set_relative_joint_motion_df(self, joint, motion_df):
        """
        jointの相対的なモーションデータを設定する

        Parameters
        ----------
        motion_df : pandas.DataFrame
            モーションデータ
        """

        cpied_motion_df = motion_df.copy()
        cpied_motion_df.columns = [
            c if c == "time" else f"{joint}_{c}" for c in cpied_motion_df.columns
        ]

        original_columns = set(self.motion_df.columns)
        columns = set(cpied_motion_df.columns)
        missing_columns = columns - original_columns
        if len(missing_columns) > 0:
            raise ValueError(f"columns {missing_columns} are missing in motion_df")
        else:
            self.motion_df.update(cpied_motion_df)

    def __set_absolute_joint_motion_df(self, joint, motion_df):
        """
        jointの絶対的なモーションデータを設定する

        Parameters
        ----------
        motion_df : pandas.DataFrame
            モーションデータ
        """

        cpied_motion_df = motion_df.copy()
        cpied_motion_df.columns = [
            c if c == "time" else f"{joint}_{c}" for c in cpied_motion_df.columns
        ]

        original_columns = set(self.motion_df.columns)
        columns = set(cpied_motion_df.columns)
        missing_columns = columns - original_columns
        if len(missing_columns) > 0:
            raise ValueError(f"columns {missing_columns} are missing in motion_df")

        absolute_motion_df = self.__get_absolute_motion_df(joint)
        diff_motion_df = cpied_motion_df - absolute_motion_df
        diff_motion_df["time"] = cpied_motion_df["time"]

        self.motion_df.update(diff_motion_df)

    def get_joint_offset(self, joint):
        """
        指定したjointのoffsetを取得する

        Parameters
        ----------
        joint : str
            offsetを取得するjoint

        Returns
        -------
        list
            offset
        """

        return self.skeleton[joint]["offset"]

    def set_joint_offset(self, joint, offset):
        """
        指定したjointのoffsetを設定する

        Parameters
        ----------
        joint : str
            offsetを設定するjoint
        offset : list
            offset
        """

        if len(offset) != len(self.skeleton[joint]["offset"]):
            raise ValueError(f"offset length must be 3. but got {len(offset)}")

        self.skeleton[joint]["offset"] = offset

    def get_initial_position(
        self, index=100, channel_names=["Xposition", "Yposition", "Zposition"]
    ):
        """
        初期位置を取得する

        Parameters
        ----------
        position : list
            初期位置
        """

        motion_df = self.default_motion_df.copy()
        return [
            motion_df[f"{self.root}_{channel_name}"][index]
            for channel_name in channel_names
        ]

    def set_initial_position(
        self, position, channel_names=["Xposition", "Yposition", "Zposition"]
    ):
        """
        初期位置を設定する

        Parameters
        ----------
        position : list
            初期位置
        """

        init_pos = self.get_initial_position()
        diff_pos = np.array(position) - np.array(init_pos)

        for i, channel_name in enumerate(channel_names):
            self.motion_df[f"{self.root}_{channel_name}"] += diff_pos[i]

    def get_initial_rotation(
        self, index=1, channel_names=["Xrotation", "Yrotation", "Zrotation"]
    ):
        """
        初期回転量を取得する

        Parameters
        ----------
        rotation : list
            初期回転量
        """

        motion_df = self.default_motion_df.copy()
        return [
            motion_df[f"{self.root}_{channel_name}"][index]
            for channel_name in channel_names
        ]

    def set_initial_rotation(
        self, rotation, channel_names=["Xrotation", "Yrotation", "Zrotation"]
    ):
        """
        初期位置を設定する

        Parameters
        ----------
        rotation : list
            初期回転量
        """

        init_rot = self.get_initial_rotation()
        diff_rot = np.array(rotation) - np.array(init_rot)

        for i, channel_name in enumerate(channel_names):
            self.motion_df[f"{self.root}_{channel_name}"] += diff_rot[i]

    def get_skeleton(self):
        """
        骨格データを取得する

        Returns
        -------
        dict
            骨格データ
        """

        return self.skeleton.copy()

    def get_skeleton_path2root(self, joint):
        """
        指定したjointからrootまでのパスを取得する

        Parameters
        ----------
        joint : str
            パスを取得するjoint

        Returns
        -------
        list
            jointからrootまでのパス
        """

        path = []
        while joint != None:
            path.append(joint)
            joint = self.skeleton[joint]["joint"]

        return path

    def get_motion_df(self):
        """
        モーションのデータフレームを取得する

        Returns
        -------
        pandas.DataFrame
            モーションデータ
        """

        return self.motion_df.copy()

    def set_motion_df(self, motion_df):
        """
        モーションのデータフレームを設定する

        Parameters
        ----------
        motion_df : pandas.DataFrame
            モーションデータ
        """

        original_columns = set(self.motion_df.columns)
        columns = set(motion_df.columns)
        missing_columns = original_columns - columns
        if len(missing_columns) > 0:
            raise ValueError(f"columns {missing_columns} are missing in motion_df")
        else:
            self.motion_df = motion_df.copy()

    def get_joint_motion_df(self, joint, mode="relative"):
        """
        指定したjointのモーションデータを取得する

        Parameters
        ----------
        joint : str
            モーションデータを取得するjoint
        mode : str
            モーションデータの種類
            relative: 相対的な関節のモーションデータ
            absolute: 絶対的な関節のモーションデータ

        Returns
        -------
        pandas.DataFrame
            モーションデータ
        """

        if mode == "relative":
            return self.__get_relative_motion_df(joint)
        elif mode == "absolute":
            return self.__get_absolute_motion_df(joint)
        else:
            raise ValueError(f"invalid mode: {mode}")

    def set_joint_motion_df(self, joint, motion_df, mode="relative"):
        """
        指定したjointのモーションデータを設定する

        Parameters
        ----------
        joint : str
            モーションデータを設定するjoint
        motion_df : pandas.DataFrame
            モーションデータ
        mode : str
            モーションデータの種類
            relative: 相対的な関節のモーションデータ
            absolute: 絶対的な関節のモーションデータ
        """

        if mode == "relative":
            self.__set_relative_joint_motion_df(joint, motion_df)
        elif mode == "absolute":
            self.__set_absolute_joint_motion_df(joint, motion_df)
        else:
            raise ValueError(f"invalid mode: {mode}")

    def get_joints(self):
        """
        関節名のリストを取得する

        Returns
        -------
        list
            関節名のリスト
        """

        return self.skeleton.keys()

    def get_channels(self):
        """
        チャンネル名のリストを取得する

        Returns
        -------
        list
            チャンネル名のリスト
        """

        return self.channels

    def to_csv(self, filename):
        """
        モーションデータをCSVに出力する

        Parameters
        ----------
        filename : str
            出力するCSVファイル名
        """

        self.motion_df.to_csv(filename)

    def to_bvh(self, filename=None):
        """
        BVHファイルに出力する

        Parameters
        ----------
        filename : str
            出力するBVHファイル名
        """

        if filename == None:
            now = time.localtime()
            filename = f'MCPM_{time.strftime("%Y%m%d_%H%M%S", now)}.BVH'

        skelton_str = self.__get_skeleton_str(self.root)
        columns = self.__get_columns(self.root)
        motion_df = self.get_motion_df()

        reordered_motion_df = motion_df[columns]
        motion = reordered_motion_df.to_csv(index=False, header=False, sep=" ")

        n = reordered_motion_df.shape[0]

        with open(filename, "w") as f:
            f.write("HIERARCHY\n")
            f.write(f"{skelton_str}\n")
            f.write("MOTION\n")
            f.write(f"Frames: {n}\n")
            f.write(f"Frame Time: {self.frame_time}\n")
            f.write(motion)
