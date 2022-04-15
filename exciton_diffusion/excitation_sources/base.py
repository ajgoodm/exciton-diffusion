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

    #: A mapping from the 2D plane to the positive reals
    #: representing the relative probability of an excitation occuring at a given point
    spatial_distribution: T.Callable[[float, float], float] = attr.ib()
    #: A mapping from time to the positive reals
    #: representing the relative probability of an excitation occuring a given moment
    temporal_distribution: T.Callable[[float], float] = attr.ib()
    #: Time averaged excitation rate
    excitation_rate_hz: float = attr.ib()

    def get_excitations(self, start: float, end: float) -> T.Tuple[Excitation2D]:
        pass
