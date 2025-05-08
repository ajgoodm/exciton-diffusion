from dataclasses import dataclass
from typing import Callable

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


@dataclass(init=False)
class ConvolvedExponentialDecayParams:
    decay_rate_hz: float

    def __init__(self, decay_rate_hz: float):
        if decay_rate_hz <= 0:
            raise ValueError("Decay rate must be a positive integer")
        self.decay_rate_hz = decay_rate_hz

    @property
    def decay_lifetime_s(self) -> float:
        return 1.0 / self.decay_rate_hz


@dataclass
class ConvolvedExponentialDecayFitResult:
    decay_rate_hz: float
    decay_rate_hz_fit_variance: float


def _exponential_convolved_with_impulse_response(
    impulse_response_fwhm: float,
) -> Callable[[NDArray[np.floating], float], NDArray[np.floating]]:
    def _inner(
        domain: NDArray[np.floating],
        decay_rate_hz: float,
    ) -> NDArray[np.floating]:
        """Calculate an exponential decay over the domain with the piecewise function:
        x >= 0 -> exp(-decay_rate_hz * x)
        x < 0 -> 0

        and then convolve the result with a gaussian impulse response (area 1)
        with the prescribed full-width at half max over the domain. Return the
        result normalized to a maximum value of 1, and over the original domain.
        """
        domain_min = min(domain)  # type: ignore[type-var]
        domain_max = max(domain)  # type: ignore[type-var]
        if (
            domain_min > -2 * impulse_response_fwhm
            or domain_max < 2 * impulse_response_fwhm
        ):
            raise RuntimeError(
                "Cannot confidently deconvolve impulse response when domain does not straddle 0 and extend +/- 2 FWHM"
            )

        y = np.zeros(domain.shape, dtype=domain.dtype)
        for idx, val in enumerate(domain):
            if val >= 0:
                y[idx] = np.exp(-decay_rate_hz * val)

        # IRF: impulse response function - https://en.wikipedia.org/wiki/Impulse_response
        irf_standard_deviation = impulse_response_fwhm / 2.355
        irf = np.exp(-(domain**2) / (2 * irf_standard_deviation**2))
        irf = irf / sum(irf)

        result = np.convolve(y, irf)
        return result

    return _inner


def fit_convolved_exponetial_decay(
    x: NDArray[np.floating],
    y: NDArray[np.floating],
    impulse_response_fwhm_s: float,
    initial_guess: ConvolvedExponentialDecayParams | None,
) -> ConvolvedExponentialDecayFitResult:
    kwargs = dict()
    if initial_guess is not None:
        kwargs["p0"] = (initial_guess.decay_rate_hz,)

    _convolved_exponential = _exponential_convolved_with_impulse_response(
        impulse_response_fwhm_s
    )
    fitted_parameters, covariance_matrix = curve_fit(
        _convolved_exponential, x, y, **kwargs
    )

    return ConvolvedExponentialDecayFitResult(
        decay_rate_hz=fitted_parameters[0],
        decay_rate_hz_fit_variance=covariance_matrix[0][0],
    )
