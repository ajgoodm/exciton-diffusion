from pathlib import Path
from typing import TypeVar, Type

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel


Deserializable = TypeVar("Deserializable", bound=BaseModel)


def read_json_file(path: Path, model_class: Type[Deserializable]) -> Deserializable:
    return model_class.model_validate_json(path.read_text())


def read_array_f64_bigendian(path: Path) -> NDArray[np.float64]:
    with open(path, "rb") as fh:
        array = np.frombuffer(fh.read(), dtype=np.dtype(">f8"))
    return array
