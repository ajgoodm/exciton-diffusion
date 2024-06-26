import math
import typing as T
from abc import abstractmethod, ABC

import attr
import numpy as np
import numpy.typing as npt

from exciton_diffusion.constants import _2PI
from exciton_diffusion.excitation_sources.excitation_source_2d import Excitation2D


@attr.define
class EmissionEvent2D:
    x_m: float
    y_m: float
    t_s: float = attr.ib(default=None)


@attr.define
class EmitterPopulation2D(ABC):
    x_coords_m: npt.NDArray[np.float_]
    y_coords_m: npt.NDArray[np.float_]
    routines: list[T.Callable[[float], T.Optional[list[EmissionEvent2D]]]] = attr.ib(
        factory=list
    )

    @abstractmethod
    def initialize(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        raise NotImplementedError

    @property
    def n_excitons(self) -> int:
        return self.x_coords_m.shape[0]

    def add_excitations_2d(self, excitations: list[Excitation2D]) -> None:
        x_coords_m = []
        y_coords_m = []

        for excitation in excitations:
            x_coords_m.append(excitation.x_m)
            y_coords_m.append(excitation.y_m)

        self.x_coords_m = np.concatenate([self.x_coords_m, np.array(x_coords_m)])
        self.y_coords_m = np.concatenate([self.y_coords_m, np.array(y_coords_m)])

    def step(self, time_step_s: float) -> list[EmissionEvent2D]:
        emission_events: list[EmissionEvent2D] = []
        for routine in self.routines:
            events = routine(time_step_s)
            if events is not None:
                emission_events.extend(events)

        return emission_events


@attr.define
class ExcitonPopulation2D(EmitterPopulation2D):
    radiative_lifetime_s: float = attr.ib(default=None)
    nonradiative_lifetime_s: T.Optional[float] = attr.ib(default=None)
    diffusivity_m2_per_s: T.Optional[float] = attr.ib(default=None)
    annihilation_radius_m: T.Optional[float] = attr.ib(default=None)

    def initialize(
        self,
        radiative_lifetime_s: float,
        nonradiative_lifetime_s: T.Optional[float] = None,
        diffusivity_m2_per_s: T.Optional[float] = None,
        annihilation_radius_m: T.Optional[float] = None,
    ) -> None:
        self.x_coords_m = np.array([], dtype=np.float64)
        self.y_coords_m = np.array([], dtype=np.float64)
        self.radiative_lifetime_s = radiative_lifetime_s
        self.nonradiative_lifetime_s = nonradiative_lifetime_s
        self.diffusivity_m2_per_s = diffusivity_m2_per_s
        self.routines.append(self.linear_decay)
        if diffusivity_m2_per_s is not None:
            self.routines.append(self.diffusion)
        if annihilation_radius_m is not None:
            self.routines.append(self.annihilation)

    @property
    def radiative_rate_hz(self) -> float:
        return 1 / self.radiative_lifetime_s

    @property
    def nonradiative_rate_hz(self) -> T.Optional[float]:
        if self.nonradiative_lifetime_s is not None:
            return 1 / self.nonradiative_lifetime_s
        return None

    def _diffusion_step_length_m(self, time_step_s: float) -> T.Optional[float]:
        if self.diffusivity_m2_per_s is not None:
            return float((self.diffusivity_m2_per_s * time_step_s) ** 0.5)
        return None

    def linear_decay(self, time_step_s: float) -> list[EmissionEvent2D]:
        """Simulates linear decay processes (radiative and optionally nonradiative)
        that occur over the course of the time step.

        Arguments:
            time_step_s: the discrete time period to simulate

        Returns:
            A list of (x, y) position tuples where radiative decay occurred
        """
        total_linear_decay_rate_hz = self.radiative_rate_hz
        if self.nonradiative_rate_hz is not None:
            total_linear_decay_rate_hz += self.nonradiative_rate_hz

        probability_of_decay = 1 - math.exp(-total_linear_decay_rate_hz * time_step_s)
        random_rolls = np.random.random(size=self.n_excitons)

        decayed = np.where(random_rolls <= probability_of_decay)
        decayed_x_m = self.x_coords_m[decayed]
        decayed_y_m = self.y_coords_m[decayed]
        n_decayed = decayed_x_m.shape[0]

        probability_decay_was_radiative = 1.0
        if self.nonradiative_rate_hz is not None:
            probability_decay_was_radiative = self.radiative_rate_hz / (
                self.radiative_rate_hz + self.nonradiative_rate_hz
            )
        radiative_decay_rolls = np.random.random(size=n_decayed)
        radiative_decayed_x_m = decayed_x_m[
            np.where(radiative_decay_rolls <= probability_decay_was_radiative)
        ]
        radiative_decayed_y_m = decayed_y_m[
            np.where(radiative_decay_rolls <= probability_decay_was_radiative)
        ]

        not_decayed = np.where(random_rolls > probability_of_decay)
        self.x_coords_m = self.x_coords_m[not_decayed]
        self.y_coords_m = self.y_coords_m[not_decayed]

        return [
            EmissionEvent2D(x_m=x, y_m=y)
            for x, y in zip(radiative_decayed_x_m, radiative_decayed_y_m)
        ]

    def diffusion(self, time_step_s: float) -> None:
        """Simulates random walk diffusion moving each exciton in the population
        one diffusion length over the course of the time step.
        """
        directions_radians = np.random.uniform(low=0.0, high=_2PI, size=self.n_excitons)

        dx_m = np.sin(directions_radians) * self._diffusion_step_length_m(time_step_s)
        dy_m = np.cos(directions_radians) * self._diffusion_step_length_m(time_step_s)

        self.x_coords_m += dx_m
        self.y_coords_m += dy_m

    def annihilation(self, time_step_s: float) -> None:
        return None
