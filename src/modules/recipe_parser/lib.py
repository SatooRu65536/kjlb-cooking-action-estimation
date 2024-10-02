from yaml import safe_load
from typing import Any
from type import Recipe


def parse_recipe(path: str) -> Recipe:
    content = read_yaml(path)
    return to_recipe(content)


def to_recipe(content: Any) -> Recipe:
    return content


def read_yaml(path: str) -> Any:
    content: Any = None

    with open(path, "r") as f:
        content = safe_load(f)

    return content


if __name__ == "__main__":
    recipe = parse_recipe("../../../recipes/data/rolled_omelet.yaml")
    print(recipe)
