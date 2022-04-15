import math
import typing as T
from abc import ABC

import attr
from attr.validators import instance_of

from exciton_diffusion.excitation_sources.excitation_location_generators import ExcitationLocationGenerator
from exciton_diffusion.excitation_sources.excitation_time_generators import ExcitationTimeGenerator


@attr.s(frozen=True, slots=True)
class Excitation2D:
    """Representation of a single excitation event in the plane.
    """

    #: x coordinate in meters
    x_m: float = attr.ib()
    #: y coordinate in meters
    y_m: float = attr.ib()
    #: excitation time in seconds
    t_s: float = attr.ib()


@attr.s(frozen=True, slots=True)
class ExcitationProfile2D:
    """Parameters used to generate a stream of excitation events in the plane.
    """

    #: earliest excitation time
    start_s: float = attr.ib()

    #: latest excitation time
    end_s: float = attr.ib()

    #: total number of excitations
    n_excitations: int = attr.ib()

    #: excitation time series generator with method `generate(start_s, end_s, n_excitations) -> tuple[float]`
    excitation_time_generator: ExcitationTimeGenerator = attr.ib(validator=instance_of(ExcitationTimeGenerator))

    #: excitation location series generator with method `generate(n_excitations) -> tuple[[float, float]]`
    excitation_location_generator: ExcitationLocationGenerator = attr.ib(validator=instance_of(ExcitationLocationGenerator))

    def get_excitations(self) -> tuple[Excitation2D]:
        """Generate a series of excitations for this profile

        Args:
            n_excitations: total number of excitations to generate

        Returns:
            A series of excitation excitation events in the plane
        """
        excitation_times = self.excitation_time_generator.generate(start_s=self.start_s, end_s=self.end_s, n_excitations=self.n_excitations)
        excitation_locations = self.excitation_location_generator.generate(n_excitations=self.n_excitations)

        return tuple(
            Excitation2D(
                x_m=point[0],
                y_m=point[1],
                t_s=time,
            ) for time, point in zip(excitation_times, excitation_locations) 
        )
