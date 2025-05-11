from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from numpy.typing import NDArray

from analysis.show.excitations import ExcitationConfig
from analysis.utils import read_array_f64_bigendian, read_json_file, wrap
from analysis.curve_fitting.least_squares import (
    fit_gaussian_mean_0,
    GaussianMean0Parameters,
)


def plot(
    data_directory: Path, fig_edge_len: float = 7.0, n_time_bins: int = 256
) -> None:
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

    left_shift = 4 * config.pulse_fwhm_s
    min_x = -left_shift
    max_x = period_s - left_shift
    wrapped_time = wrap(time, period_s, left_shift)
    time_bins = np.linspace(min_x, max_x, n_time_bins)
    ax1 = _plot_wrapped(ax1, wrapped_time, time_bins)
    ax1.set_xlim((min_x, max_x))
    _plot_diffusion(
        ax2,
        wrapped_time,
        x_m,
        config.spot_fwhm_m,
        time_bins,
        -2 * config.spot_fwhm_m,
        2 * config.spot_fwhm_m,
    )

    plt.tight_layout()
    plt.show()


def _plot_wrapped(
    axis: Axes, events: NDArray[np.float64], bins: NDArray[np.floating]
) -> Axes:
    axis.set_xlabel("time (s)", fontsize=15)
    axis.set_ylabel("count", fontsize=15)
    _, _, _ = axis.hist(events, bins)  # type: ignore[arg-type]
    axis.semilogy()
    return axis


def _plot_diffusion(
    axis: Axes,
    time_s: NDArray[np.float64],
    x_m: NDArray[np.float64],
    initial_spot_fwhm_m: float,
    time_bins: NDArray[np.floating],
    min_x: float,
    max_x: float,
    n_x_bins: int = 64,
) -> None:
    time_bin_centers = (time_bins[:-1] + time_bins[1:]) / 2.0

    x_bins = np.linspace(min_x, max_x, n_x_bins)
    x_bin_centers = (x_bins[:-1] + x_bins[1:]) / 2.0

    histogram = np.histogram2d(x_m, time_s, (x_bins, time_bins))[0]

    fitted_fwhms: list[float] = []
    for time_slice_idx in range(len(time_bins) - 1):
        row = histogram[:, time_slice_idx]
        max_ct = max(row)
        row = row / max(max_ct, 1)
        histogram[:, time_slice_idx] = row

        fit_result = fit_gaussian_mean_0(
            x_bin_centers,
            row,
            GaussianMean0Parameters(
                amplitude=1.0, standard_deviation=initial_spot_fwhm_m
            ),
        )
        fitted_fwhm = (
            fit_result.standard_deviation * 2.355
        )  # https://en.wikipedia.org/wiki/Full_width_at_half_maximum
        fitted_fwhms.append(fitted_fwhm)

    fitted_fwhms_arr = np.array(fitted_fwhms)
    axis.imshow(
        histogram,
        extent=(float(min(time_bins)), float(max(time_bins)), min_x, max_x),  # type: ignore[type-var]
        aspect="auto",
    )
    axis.plot(time_bin_centers, fitted_fwhms_arr, "w-")
    axis.plot(time_bin_centers, -fitted_fwhms_arr, "w-")
    axis.set_ylim(min_x, max_x)
