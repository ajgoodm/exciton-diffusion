from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from numpy.typing import NDArray

from analysis.show.excitations import ExcitationConfig
from analysis.utils import read_array_f64_bigendian, read_json_file, wrap
from analysis.curve_fitting.least_squares import (
    convolved_exponential,
    fit_gaussian_mean_0,
    fit_convolved_exponential_decay,
    ConvolvedExponentialDecayParams,
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

    _, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(fig_edge_len, fig_edge_len))

    left_shift = 4 * config.pulse_fwhm_s
    min_x = -left_shift
    max_x = period_s - left_shift
    wrapped_time = wrap(time, period_s, left_shift)
    time_bins = np.linspace(min_x, max_x, n_time_bins)
    ax1 = _plot_wrapped(ax1, wrapped_time, time_bins, config.pulse_fwhm_s)
    ax1.set_xlim((min_x, max_x))
    _plot_diffusion(
        ax2,
        ax3,
        wrapped_time,
        x_m,
        config.spot_fwhm_m,
        time_bins,
        -2 * config.spot_fwhm_m,
        2 * config.spot_fwhm_m,
    )
    ax2.set_xlim((min_x, max_x))
    ax3.set_xlim((min_x, max_x))

    plt.tight_layout()
    plt.show()


def _plot_wrapped(
    axis: Axes,
    events: NDArray[np.float64],
    bins: NDArray[np.floating],
    pulse_fwhm_s: float,
) -> Axes:
    axis.set_xlabel("time (s)", fontsize=15)
    axis.set_ylabel("count", fontsize=15)
    cts, _, _ = axis.hist(events, bins)  # type: ignore[arg-type]
    bin_centers = (bins[1:] + bins[:-1]) / 2.0
    exponential_fit = fit_convolved_exponential_decay(
        bin_centers,
        cts / max(cts),
        pulse_fwhm_s,
        ConvolvedExponentialDecayParams(1.0e8),
    )
    axis.plot(
        bin_centers,
        convolved_exponential(bin_centers, exponential_fit.decay_rate_hz, pulse_fwhm_s)
        * max(cts),
        "-r",
    )
    axis.semilogy()
    axis.set_ylim((0.5 * min(cts), 1.5 * max(cts)))
    return axis


def _plot_diffusion(
    axis_2d_plot: Axes,
    axis_diffusivity_fit: Axes,
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

    fitted_stddevs: list[float] = []
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
        fitted_stddevs.append(fit_result.standard_deviation)

    fitted_fwhms = (
        np.array(fitted_stddevs) * 2.355
    )  # https://en.wikipedia.org/wiki/Full_width_at_half_maximum
    axis_2d_plot.imshow(
        histogram,
        extent=(float(min(time_bins)), float(max(time_bins)), min_x, max_x),  # type: ignore[type-var]
        aspect="auto",
    )
    axis_2d_plot.plot(time_bin_centers, fitted_fwhms, "w-")
    axis_2d_plot.plot(time_bin_centers, -fitted_fwhms, "w-")
    axis_2d_plot.set_ylim(min_x, max_x)
    axis_2d_plot.set_ylabel("x (m)", fontsize=15)

    non_zero_times: list[float] = []
    fitted_variance: list[float] = []
    for t, sd in zip(time_bin_centers, fitted_stddevs):
        if t >= 0:
            non_zero_times.append(t)
            fitted_variance.append(sd**2)

    axis_diffusivity_fit.plot(non_zero_times, fitted_variance, ".k")
    axis_diffusivity_fit.set_ylabel("fitted Gaussian\nvariance (m$^2$)", fontsize=15)
    axis_diffusivity_fit.set_xlabel("time (s)", fontsize=15)
