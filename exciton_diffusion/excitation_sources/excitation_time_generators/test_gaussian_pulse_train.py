import pytest

from exciton_diffusion.excitation_sources.excitation_time_generators.gaussian_pulse_train import (
    GaussianPulseTrainGenerator,
)


class TestGaussianPulseTrainGenerator:
    def test_repitition_period_s(self):
        generator = GaussianPulseTrainGenerator(
            repetition_rate_hz = 0.1,
            pulse_full_width_half_max_s=1
        )

        assert generator.repetition_period_s == 10
        assert generator.pulse_standard_deviation_s == 1 / 2.355
    
    def test_gaussian_pulse_train_generator(self):
        generator = GaussianPulseTrainGenerator(
            repetition_rate_hz=1e6,
            pulse_full_width_half_max_s=1e-9,
        )

        start = -1e-5  # -10 microseconds
        end = 5e-5  # +50 microseconds
        n_excitations = int(1e6)

        excitations = generator.gaussian_pulse_train_generator(
            start_s=start, end_s=end, n_excitations=n_excitations
        )

        assert all(t >= start for t in excitations)
        assert all(t <= end for t in excitations)
        assert len(excitations) == n_excitations
        for idx in range(n_excitations - 1):
            assert excitations[idx + 1] >= excitations[idx]
