from pathlib import Path
from typing import TypeVar, Type

from pydantic import BaseModel


Deserializable = TypeVar("Deserializable", bound=BaseModel)


def read_json_file(path: Path, model_class: Type[Deserializable]) -> Deserializable:
    return model_class.model_validate_json(path.read_text())
