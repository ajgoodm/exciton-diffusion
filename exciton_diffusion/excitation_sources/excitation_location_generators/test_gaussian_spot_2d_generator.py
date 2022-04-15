from exciton_diffusion.excitation_sources.excitation_location_generators.gaussian_spot_2d_generator import (
    GaussianSpot2DGenerator
)


class TestGaussianSpot2DGenerator:
    def test_happy_path(self):
        generator = GaussianSpot2DGenerator(
            full_width_half_max_m=1,
        )

        n_points = 1000
        points = generator.gaussian_spot_2d_generator(n_excitations=n_points)
        assert len(points) == n_points
