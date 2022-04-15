import math
import typing as T
from abc import ABC

import attr


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

    #: A function that takes a start, end, and number of excitations and returns
    #: a sequence of excitation times
    excitation_time_generator: T.Callable[[float, float, int], tuple[float]]
    #: A function takes a number of excitations and returns a sequence of
    #: locations in the plane
    excitation_location_generator: T.Callable[[int], tuple[tuple[float, float]]]
    #: Time averaged excitation rate
    excitation_rate_hz: float = attr.ib()

    def get_excitations(self, start_s: float, end_s: float) -> tuple[Excitation2D]:
        """Generate a series of excitations for this profile

        Args:
            start_s: The earliest time an excitation can be generated
            end_s: The latest time an excitation can be generated
        
        Returns:
            A series of excitation excitation events in the plane
        """
        total_time_s = end_s - start_s
        if not total_time_s > 0:
            raise ValueError("Source must generate excitations for some time period")
        
        n_excitations: int = math.floor(total_time_s * self.excitation_rate_hz)
        excitation_times = self.excitation_time_generator(n_excitations, start_s, end_s)
        excitation_locations = self.excitation_location_generator(n_excitations)

        return tuple(
            Excitation2D(
                x_m=point[0],
                y_m=point[1],
                t_S=time,
            ) for time, point in zip(excitation_times, excitation_locations) 
        )
