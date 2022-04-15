from exciton_diffusion.excitation_sources import excitation_time_generators
from exciton_diffusion.excitation_sources.excitation_time_generators import GaussianPulseTrainGenerator
from exciton_diffusion.excitation_sources.excitation_location_generators import GaussianSpot2DGenerator
from exciton_diffusion.excitation_sources.excitation_source_2d import ExcitationProfile2D


class TestExcitationProfile2D:
    def test_get_excitations(self):
        excitation_time_generator = GaussianPulseTrainGenerator(
            repetition_rate_hz=1e6, pulse_full_width_half_max_s=1e-9
        )
        excitation_location_generator = GaussianSpot2DGenerator(
            full_width_half_max_m=1e-6
        )

        start = -1e-5
        end = 5e-5
        n_excitations = 1_000_000

        excitation_profile = ExcitationProfile2D(
            start_s=start,
            end_s=end,
            n_excitations=n_excitations,
            excitation_time_generator=excitation_time_generator,
            excitation_location_generator=excitation_location_generator,
        )
        excitations = excitation_profile.get_excitations()

        assert all(e.t_s >= start for e in excitations)
        assert all(e.t_s <= end for e in excitations)
        assert len(excitations) == n_excitations
        for idx in range(n_excitations - 1):
            assert excitations[idx + 1].t_s >= excitations[idx].t_s
