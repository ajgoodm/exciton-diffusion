from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import curve_fit


@dataclass
class GaussianMean0Parameters:
    amplitude: float
    standard_deviation: float


@dataclass
class GaussianMean0FitResult:
    amplitude: float
    amplitude_fit_variance: float
    standard_deviation: float
    standard_deviation_fit_variance: float


def _gaussian_mean_0(
    domain: NDArray[np.floating],
    amplitude: float,
    standard_deviation: float,
) -> NDArray[np.floating]:
    return amplitude * np.exp(-(domain**2) / (2 * (standard_deviation**2)))  # type: ignore[no-any-return]


def fit_gaussian_mean_0(
    x: NDArray[np.floating],
    y: NDArray[np.floating],
    initial_guess: GaussianMean0Parameters | None,
) -> GaussianMean0FitResult:
    kwargs = dict()
    if initial_guess is not None:
        kwargs["p0"] = (
            initial_guess.amplitude,
            initial_guess.standard_deviation,
        )

    fitted_parameters, covariance_matrix = curve_fit(_gaussian_mean_0, x, y, **kwargs)

    return GaussianMean0FitResult(
        amplitude=fitted_parameters[0],
        amplitude_fit_variance=covariance_matrix[0][0],
        standard_deviation=fitted_parameters[1],
        standard_deviation_fit_variance=covariance_matrix[1][1],
    )
