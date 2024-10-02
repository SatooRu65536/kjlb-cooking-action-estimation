from typing import List, Optional, Dict
from pydantic import BaseModel, field_validator


class Time(BaseModel):
    h: int
    m: int
    s: int

    @field_validator("h", "m", "s")
    def check_positive(cls, v):
        if v < 0:
            raise ValueError("h/m/sは正の数にしてください")
        return v

    @field_validator("h", "m", "s")
    def check_integer(cls, v):
        if not isinstance(v, int):
            raise ValueError("h/m/sは整数にしてください")
        return v


class Ingredient(BaseModel):
    name: str
    quantity: float
    unit: str

    @field_validator("quantity")
    def check_positive(cls, v):
        if v <= 0:
            raise ValueError("数量は正の数でなければなりません。")
        return v


class Process(BaseModel):
    title: str
    time: Time
    required: List[str]


class OverwritedProcess(BaseModel):
    time: Optional[Time]
    required: List[str]


class Recipe(BaseModel):
    name: str
    url: Optional[str]
    ingredients: List[Ingredient]
    steps: Dict[str, OverwritedProcess]
    processes: Dict[str, Process]
