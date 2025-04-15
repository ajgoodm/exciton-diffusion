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


def wrap(
    events: NDArray[np.float64], period_s: float, pulse_fwhm_s: float
) -> NDArray[np.float64]:
    result = events.copy()

    start = period_s - 4 * pulse_fwhm_s
    for (event_idx, event) in enumerate(events):
        if event > period_s:
            difference = event - start
            offset = np.floor(difference / period_s) + 1
            result[event_idx] = event - offset * period_s

    return result
