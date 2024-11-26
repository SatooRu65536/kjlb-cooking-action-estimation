from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from typing import Literal
import pickle

ModelType = Literal["random forest", "xgboost", "lightgbm"]


class Model:
    def __init__(self, type: ModelType, num_class: int | None = None):
        match type:
            case "random forest":
                self.model = RandomForestClassifier()
            case "xgboost":
                self.model = XGBClassifier(
                    objective="multi:softmax",
                    num_class=3,
                    eval_metric="mlogloss",
                    use_label_encoder=False,
                )
            case "lightgbm":
                if num_class is None:
                    raise ValueError("num_class is required for lightgbm")

                self.model = LGBMClassifier(objective="multiclass", num_class=num_class)

    def predict(self, x):
        return self.model.predict(x)

    def fit(self, x, y):
        return self.model.fit(x, y)

    def dump(self, path: str):
        with open(path, "wb") as f:
            pickle.dump(self.model, f)
