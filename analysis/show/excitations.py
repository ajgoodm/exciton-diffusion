from pathlib import Path

import matplotlib.pyplot as plt
from pydantic import BaseModel, ConfigDict

from analysis.utils import read_json_file


class ExcitationConfig(BaseModel):
    spot_fwhm_m: float
    repetition_rate_hz: float
    n_excitations: int
    n_pulses: int

    model_config = ConfigDict(frozen=True)


def plot(data_directory: Path) -> None:
    _config = read_json_file(data_directory / "config.json", ExcitationConfig)

    x = [1, 2, 3]
    plt.plot(x, x)
    plt.show()
