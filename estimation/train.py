import pandas as pd
import pickle
import glob

from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

# csvファイルを読み込む
TRAIN_CSV_FILES = "./data/train/**/*.csv"

## 学習用
train_df = pd.DataFrame()
labels: list[str] = []

csv_files = glob.glob(TRAIN_CSV_FILES)
for csv_file in csv_files:
    try:
        data = pd.read_csv(csv_file)
    except pd.errors.EmptyDataError:
        continue
    data["label"] = len(labels)
    label = csv_file.split("/")[-1].split(".")[0]
    if label not in labels:
        labels.append(label)
    train_df = pd.concat([train_df, data])

# labels をソート
labels = sorted(labels, key=lambda x: int(x.split("_")[0]))

# labels を保存
pd.DataFrame(labels).to_csv("./estimation/model/labels.csv", header=False, index=False)

# モデルの定義
clf_random_forest = RandomForestClassifier()
clf_xgboost = XGBClassifier(
    objective="multi:softmax",
    num_class=3,
    eval_metric="mlogloss",
    use_label_encoder=False,
)
clf_lightgbm = LGBMClassifier(objective="multiclass", num_class=len(labels))

# 学習
X_train = train_df.drop("label", axis=1)
y_train = train_df["label"]

print("train random forest")
clf_random_forest.fit(X_train, y_train)
with open("./estimation/model/random_forest.pkl", "wb") as f:
    pickle.dump(clf_random_forest, f)

print("train xgboost")
clf_xgboost.fit(X_train, y_train)
with open("./estimation/model/xgboost.pkl", "wb") as f:
    pickle.dump(clf_xgboost, f)

print("train lightgbm")
clf_lightgbm.fit(X_train, y_train)
with open("./estimation/model/lightgbm.pkl", "wb") as f:
    pickle.dump(clf_lightgbm, f)
