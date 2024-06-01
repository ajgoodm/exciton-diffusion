import typing as T

import attr

from exciton_diffusion.excitation_sources.excitation_location_generators import (
    ExcitationLocationGenerator,
)
from exciton_diffusion.excitation_sources.excitation_time_generators import (
    ExcitationTimeGenerator,
)


__all__ = ["Excitation2D", "ExcitationProfile2D"]


@attr.frozen
class Excitation2D:
    """Representation of a single excitation event in the plane."""

    #: x coordinate in meters
    x_m: float
    #: y coordinate in meters
    y_m: float
    #: excitation time in seconds
    t_s: float


@attr.define
class ExcitationProfile2D:
    """Parameters used to generate a stream of excitation events in the plane."""

    #: earliest excitation time
    start_s: float

    #: latest excitation time
    end_s: float

    #: total number of excitations
    n_excitations: int

    #: excitation time series generator with method `generate(start_s, end_s, n_excitations) -> tuple[float]`
    excitation_time_generator: ExcitationTimeGenerator

    #: excitation location series generator with method `generate(n_excitations) -> tuple[[float, float]]`
    excitation_location_generator: ExcitationLocationGenerator

    #: generator of excitations populated by self.prepare method
    _excitations: T.Generator[Excitation2D, None, None] = attr.ib(default=None)

    #: if we've yielded an excitation from our generator that we did not
    #: yet return, stop iteration and store it here for later.
    _previous_excitation: T.Optional[Excitation2D] = attr.ib(default=None)

    def prepare(self) -> None:
        """Generate a series of excitations for this profile
        and store it on the instance.

        Args:
            n_excitations: total number of excitations to generate
        """
        excitation_times = self.excitation_time_generator.generate(
            start_s=self.start_s, end_s=self.end_s, n_excitations=self.n_excitations
        )
        excitation_locations = self.excitation_location_generator.generate(
            n_excitations=self.n_excitations
        )

        self._excitations = (
            Excitation2D(
                x_m=point[0],
                y_m=point[1],
                t_s=time,
            )
            for time, point in zip(excitation_times, excitation_locations)
        )

    def yield_excitations_up_to_t(self, t_s: float) -> list[Excitation2D]:
        """Yield all excitations from self._excitations that occur prior to t_s.
        Because self._excitations is a generator, we will only ever yield each
        excitation once.
        """
        excitations: list[Excitation2D] = []

        if self._previous_excitation is not None:
            if self._previous_excitation.t_s <= t_s:
                excitations.append(self._previous_excitation)
                self._previous_excitation = None
            else:
                return excitations

        while True:
            try:
                excitation = next(self._excitations)
                if excitation.t_s <= t_s:
                    excitations.append(excitation)
                else:
                    self._previous_excitation = excitation
                    break

            except StopIteration:
                break

        return excitations
