from typing import Union
from wasmtime import Engine, Func, Module, Store, Instance

engine = Engine()
wasm = open("./correction.wasm", "rb").read()
module = Module(engine, wasm)
store = Store(engine)
instance = Instance(store, module, ())

def add(a: int, b: int) -> Union[int, None]:
    addition = instance.exports(store)["add"]

    if not isinstance(addition, Func):
        return None

    answer = addition(store, a, b)
    return answer


if __name__ == "__main__":
    ans = add(7, 4)
    print(ans)
