from pathlib import Path
from typing import cast
from collections.abc import Sequence

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict

from analysis.utils import read_array_f64_bigendian, read_json_file


class ExcitationConfig(BaseModel):
    spot_fwhm_m: float
    repetition_rate_hz: float
    pulse_fwhm_s: float
    n_excitations: int
    n_pulses: int

    model_config = ConfigDict(frozen=True)


def plot(data_directory: Path) -> None:
    config = read_json_file(data_directory / "config.json", ExcitationConfig)
    raw_array = read_array_f64_bigendian(data_directory / "excitations")
    if len(raw_array) != config.n_excitations * 3:  # time, x, y
        raise ValueError(
            f"excitation array has unexpected length ({len(raw_array)}) - expected {config.n_excitations * 3}"
        )

    time = raw_array.reshape((config.n_excitations, 3))[:, 0]
    _x = raw_array.reshape((config.n_excitations, 3))[:, 1]
    _y = raw_array.reshape((config.n_excitations, 3))[:, 2]

    period_s = 1 / config.repetition_rate_hz

    fig, (ax1, ax2, ax3) = plt.subplots(3)
    fig.suptitle("Excitation Events", fontsize=20)
    _plot_single_pulse(ax1, time, config.pulse_fwhm_s)
    _plot_pulse_train(ax2, time, period_s)
    _plot_single_pulse(
        ax3,
        wrap(time, period_s, config.pulse_fwhm_s),
        config.pulse_fwhm_s,
        "average pulse",
        False,
    )

    plt.tight_layout()
    plt.show()


def _plot_single_pulse(
    axis: Axes,
    events: NDArray[np.float64],
    fwhm_s: float,
    annotation: str = "single pulse",
    show_y_ticks: bool = True,
) -> None:
    axis.set_xlabel("time (s)", fontsize=15)
    axis.set_ylabel("count", fontsize=15)
    bins = cast(Sequence[float], np.linspace(-1.5 * fwhm_s, 1.5 * fwhm_s, 50))
    cts, _, _ = axis.hist(events, bins)
    fwhm_annotation = ((-fwhm_s / 2, fwhm_s / 2), (max(cts) / 2, max(cts) / 2))
    axis.plot(*fwhm_annotation, "r-", lw=2)
    axis.legend(["FWHM from config", annotation])
    if not show_y_ticks:
        axis.set_yticks([])


def _plot_pulse_train(axis: Axes, events: NDArray[np.float64], period_s: float) -> None:
    axis.set_xlabel("time (s)", fontsize=15)
    axis.set_ylabel("count", fontsize=15)
    axis.set_yticks([])

    bins = cast(Sequence[float], np.linspace(-0.5 * period_s, 5.5 * period_s, 512))
    cts, _, _ = axis.hist(events, bins)
    period_annotation = ((0, period_s), (1.1 * max(cts), 1.1 * max(cts)))
    axis.plot(*period_annotation, "r-", lw=2)
    axis.legend(["Pulse train repetition period", "actual"])


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
