import numpy as np

from analysis.curve_fitting.least_squares import (
    _exponential_convolved_with_impulse_response,
    _gaussian_mean_0,
    fit_convolved_exponetial_decay,
    fit_gaussian_mean_0,
    ConvolvedExponentialDecayParams,
    GaussianMean0Parameters,
)


class TestFitGaussianMean0:
    def test_happy_path(self):
        x = np.linspace(-10, 10, 128)

        exp_amplitude = 1.0
        exp_standard_deviation = 2.0
        y = _gaussian_mean_0(x, exp_amplitude, exp_standard_deviation)

        result = fit_gaussian_mean_0(
            x,
            y,
            GaussianMean0Parameters(
                amplitude=1.5,
                standard_deviation=3.0,
            ),
        )

        assert result.amplitude == exp_amplitude
        assert result.standard_deviation == exp_standard_deviation
        assert result.amplitude_fit_variance == 0.0  # fit input is calculated exactly
        assert result.standard_deviation_fit_variance == 0.0


class TestFitConvolvedExponentialDecay:
    def test_happy_path(self):
        x = np.linspace(-5, 25, 256)
        exponential_lifetime = 10.0
        exp_decay_rate = 1 / exponential_lifetime

        irf_fwhm = 1.0
        y = _exponential_convolved_with_impulse_response(irf_fwhm)(x, exp_decay_rate)
        result = fit_convolved_exponetial_decay(
            x,
            y,
            irf_fwhm,
            ConvolvedExponentialDecayParams(exp_decay_rate),
        )

        assert result.decay_rate_hz == exp_decay_rate
        assert (
            result.decay_rate_hz_fit_variance == 0.0
        )  # fit input is calculated exactly
