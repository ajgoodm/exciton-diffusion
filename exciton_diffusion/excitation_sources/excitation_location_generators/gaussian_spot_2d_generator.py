"""Utility to generate a radially symmetric 2D Gaussian spot (in the plane)
"""
import attr

import numpy as np

from exciton_diffusion.excitation_sources.excitation_location_generators.base import ExcitationLocationGenerator


@attr.s(frozen=True, slots=True)
class GaussianSpot2DGenerator(ExcitationLocationGenerator):
    #: The spot sidth in meters
    full_width_half_max_m: float = attr.ib()

    @property
    def standard_deviation_m(self) -> float:
        """Convert the full width, half max to a standard deviation
        """
        return self.full_width_half_max_m / 2.355
    
    def generate(self, n_excitations: int) -> tuple[tuple[float, float]]:
        """Generate a series of excitation locations that form a
        Gaussian excitation profile with this source's characteristics (width)

        Arguments:
            start_s: earliest possible excitation time
            end_s: latest possible excitation time
            n_excitations: number of excitations to return

        Return:
            A tuple of excitation location coordinate pairs in meters
        """
        x_coords = np.random.normal(scale=self.standard_deviation_m, size=n_excitations)
        y_coords = np.random.normal(scale=self.standard_deviation_m, size=n_excitations)

        return tuple((x, y,) for x, y in zip(x_coords, y_coords))
