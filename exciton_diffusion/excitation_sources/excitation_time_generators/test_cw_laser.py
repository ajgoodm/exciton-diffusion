from exciton_diffusion.excitation_sources.excitation_time_generators.cw_laser import (
    ContinuousWaveGenerator
)


class TestContinuousWaveGenerator:
    def test_continuous_wave_generator(self):
        generator = ContinuousWaveGenerator()

        start = -1 # -10 microseconds
        end = 1  # +50 microseconds
        n_excitations = 1000

        excitations = generator.generate(
            start_s=start, end_s=end, n_excitations=n_excitations
        )

        assert all(t >= start for t in excitations)
        assert all(t <= end for t in excitations)
        assert len(excitations) == n_excitations
        for idx in range(n_excitations - 1):
            assert excitations[idx + 1] >= excitations[idx]