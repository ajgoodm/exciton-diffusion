from pathlib import Path
from typing import cast
from collections.abc import Sequence

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from numpy.typing import NDArray

from analysis.show.excitations import ExcitationConfig
from analysis.utils import read_array_f64_bigendian, read_json_file, wrap


def plot(data_directory: Path, fig_edge_len: float = 7.0) -> None:
    config = read_json_file(data_directory / "config.json", ExcitationConfig)
    raw_array = read_array_f64_bigendian(data_directory / "emission_events")
    n_cols = 3
    if len(raw_array) % n_cols != 0:
        raise ValueError(
            "raw simulation output array had a length not divisible by the number of columns (3)"
        )

    n_rows = int(len(raw_array) / n_cols)
    time = raw_array.reshape((n_rows, n_cols))[:, 0]

    period_s = 1 / config.repetition_rate_hz

    _, (ax1) = plt.subplots(1, 1, figsize=(fig_edge_len, fig_edge_len))
    _plot_wrapped(ax1, wrap(time, period_s, config.pulse_fwhm_s), period_s)

    plt.tight_layout()
    plt.show()


def _plot_wrapped(
    axis: Axes,
    events: NDArray[np.float64],
    pulse_train_period: float,
) -> None:
    axis.set_xlabel("time (s)", fontsize=15)
    axis.set_ylabel("count", fontsize=15)
    bins = cast(
        Sequence[float],
        np.linspace(-0.05 * pulse_train_period, 0.9 * pulse_train_period, 256),
    )
    _, _, _ = axis.hist(events, bins)
    axis.semilogy()
