"""Utility to generate uniformly distributed excitation times
"""
import attr
import numpy as np

from exciton_diffusion.excitation_sources.excitation_time_generators.base import ExcitationTimeGenerator


@attr.s(frozen=True, slots=True)
class ContinuousWaveGenerator(ExcitationTimeGenerator):
    def generate(self, start_s: float, end_s: float, n_excitations: int) -> tuple[float]:
        """Generate a series of excitation times that are uniformly distributed
        between start and end.

        Arguments:
            start_s: earliest possible excitation time
            end_s: latest possible excitation time
            n_excitations: number of excitations to return

        Returns:
            A tuple of excitation event times in seconds
        """
        excitation_times = np.random.uniform(
            low=start_s, high=end_s, size=(n_excitations)
        )

        return tuple(np.sort(excitation_times))
