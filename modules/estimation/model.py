from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from typing import Literal
import pickle

ModelType = Literal["randomforest", "xgboost", "lightgbm"]


class Model:
    def __init__(self, type: ModelType, num_class: int | None = None):
        match type:
            case "randomforest":
                self.model = RandomForestClassifier()
            case "xgboost":
                self.model = XGBClassifier(
                    objective="multi:softmax",
                    num_class=num_class,
                    eval_metric="mlogloss",
                )
            case "lightgbm":
                if num_class is None:
                    raise ValueError("num_class is required for lightgbm")

                self.model = LGBMClassifier(
                    objective="multiclass", num_class=num_class, force_col_wise=True
                )

    def predict(self, x):
        return self.model.predict(x)

    def predict_proba(self, x):
        return self.model.predict_proba(x)

    def fit(self, x, y):
        return self.model.fit(x, y)

    def dump(self, path: str):
        with open(path, "wb") as f:
            pickle.dump(self.model, f)

    @classmethod
    def load(self, path: str, type: ModelType, num_class: int | None = None):
        # モデルのタイプに応じて初期化
        model = self(type, num_class)
        with open(path, "rb") as f:
            model.model = pickle.load(f)  # 保存されたモデルを読み込む

        return model
