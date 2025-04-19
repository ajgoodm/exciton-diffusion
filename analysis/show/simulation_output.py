from __future__ import annotations

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
    x_m = raw_array.reshape((n_rows, n_cols))[:, 2]

    period_s = 1 / config.repetition_rate_hz

    _, (ax1, ax2) = plt.subplots(2, 1, figsize=(fig_edge_len, fig_edge_len))
    wrapped_time = wrap(time, period_s, config.pulse_fwhm_s)
    _plot_wrapped(ax1, wrapped_time, period_s)
    _plot_diffusion(ax2, wrapped_time, x_m, period_s, config.spot_fwhm_m, 100)

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
        np.linspace(-0.1 * pulse_train_period, 1.1 * pulse_train_period, 256),
    )
    _, _, _ = axis.hist(events, bins)
    axis.semilogy()


def _plot_diffusion(
    axis: Axes,
    time_s: NDArray[np.float64],
    x_m: NDArray[np.float64],
    pulse_train_period: float,
    spot_fwhm_m: float,
    cts_per_time_slice: int,
) -> None:
    x_at_time: list[tuple[float, float]] = sorted(zip(x_m, time_s), key=lambda t: t[1])

    space_bins = cast(
        Sequence[float],
        np.linspace(-2.0 * spot_fwhm_m, 2.0 * spot_fwhm_m, 64),
    )

    # a 2D array of cts where one axis is time,
    # the other a single spatial coordinate
    result: list[list[int]] = []
    time_bins: list[float] = [0.0]

    slice_accumulator: list[float] = []
    for (x_coord, time) in x_at_time:
        if len(slice_accumulator) < cts_per_time_slice:
            slice_accumulator.append(x_coord)
        else:  # time to write a slice, and start over
            spatial_hist, _ = np.histogram(slice_accumulator, space_bins)

            max_ct = max(spatial_hist)

            result.append(spatial_hist / max(max_ct, 1))
            time_bins.append(time)

            # start the next accumulator
            slice_accumulator = []

    axis.imshow(result)
