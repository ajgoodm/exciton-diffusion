import math
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


def convolve_periodic(
    data: NDArray[np.floating], irf: NDArray[np.floating]
) -> NDArray[np.floating]:
    if len(data) != len(irf):
        raise ValueError(
            "Custom fit routine assumes data have same length and pitch as IRF"
        )

    result = np.zeros(len(data))
    for idx, shift in enumerate(range(len(data))):
        result[idx] = sum(np.roll(irf, shift) * data)

    return result


def _convolved_exponential(
    impulse_response_domain: NDArray[np.floating],
    impulse_response: NDArray[np.floating],
) -> Callable[[NDArray[np.floating], float], NDArray[np.floating]]:
    """Create a callable that takes an input domain, a decay rate, and
    calculates an exponential decay over the domain with the piecewise function:
        x >= 0 -> exp(-decay_rate_hz * x)
        x < 0 -> 0

    and then convolves the result with the supplied impulse response function
    (IRF, https://en.wikipedia.org/wiki/Impulse_response).

    This is used in the context of fitting periodic data. The supplied domain is
    assumed to have the data's period. Convolution edge effects are avoided by
    assuming this periodicity
    """
    if len(impulse_response_domain) != len(impulse_response):
        raise ValueError(
            "IRF and the domain from which it's computed must have equal length"
        )

    if impulse_response_domain[0] != 0.0:
        raise ValueError(
            "IRF domain must contain and start at 0.0 so that convolved data is not shifted from input"
        )

    if not math.isclose(sum(impulse_response), 1.0, rel_tol=1e-6):
        raise ValueError(
            "IRF must sum to 1.0 so that convolved data have same area as input"
        )

    def _inner(
        domain: NDArray[np.floating],
        decay_rate_hz: float,
    ) -> NDArray[np.floating]:
        period = max(domain) - min(domain)  # type: ignore[type-var]

        y = np.zeros(domain.shape, dtype=domain.dtype)
        for idx, val in enumerate(domain):
            if val < 0:
                val = period + val
            y[idx] = np.exp(-decay_rate_hz * val)

        result = convolve_periodic(y, impulse_response)
        return result / max(result)  # type: ignore[no-any-return, type-var]

    return _inner


def convolved_exponential(
    domain: NDArray[np.floating],
    decay_rate_hz: float,
    impulse_response_fwhm_s: float,
) -> NDArray[np.floating]:
    return _convolved_exponential(
        _make_irf_domain(domain), _make_gaussian_irf(domain, impulse_response_fwhm_s)
    )(domain, decay_rate_hz)


def _make_irf_domain(data_domain: NDArray[np.floating]) -> NDArray[np.floating]:
    domain_diffs = data_domain[1:] - data_domain[:-1]
    dx = np.mean(domain_diffs)
    for diff in domain_diffs:
        if not math.isclose(diff, dx, rel_tol=1e-6):
            raise ValueError(
                "fit_convolved_exponential_decay only works on periodic domain"
            )

    result = np.zeros(len(data_domain))
    half = math.ceil(len(data_domain) / 2)
    for idx in range(half):
        result[idx] = idx * dx
        result[len(data_domain) - (idx + 1)] = -(idx + 1) * dx

    return result


def _make_gaussian_irf(
    domain: NDArray[np.floating], impulse_response_fwhm_s: float
) -> NDArray[np.floating]:
    irf_domain = _make_irf_domain(domain)
    irf_standard_deviation = impulse_response_fwhm_s / 2.355
    irf = np.exp(-(irf_domain**2) / (2 * irf_standard_deviation**2))
    return irf / sum(irf)  # type: ignore[no-any-return]


def fit_convolved_exponential_decay(
    x: NDArray[np.floating],
    y: NDArray[np.floating],
    impulse_response_fwhm_s: float,
    initial_guess: ConvolvedExponentialDecayParams | None,
) -> ConvolvedExponentialDecayFitResult:
    kwargs = dict()
    if initial_guess is not None:
        kwargs["p0"] = (initial_guess.decay_rate_hz,)

    irf_domain = _make_irf_domain(x)
    irf = _make_gaussian_irf(x, impulse_response_fwhm_s)

    convolved_exponential = _convolved_exponential(irf_domain, irf)
    fitted_parameters, covariance_matrix = curve_fit(
        convolved_exponential, x, y, **kwargs
    )

    return ConvolvedExponentialDecayFitResult(
        decay_rate_hz=fitted_parameters[0],
        decay_rate_hz_fit_variance=covariance_matrix[0][0],
    )
