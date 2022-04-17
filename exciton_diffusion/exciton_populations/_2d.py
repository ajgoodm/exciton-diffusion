import math
import typing as T
from abc import abstractmethod, ABC

import attr
import numpy as np

from exciton_diffusion.excitation_sources.excitation_source_2d import Excitation2D


@attr.s(slots=True)
class EmissionEvent2D:
    x_m: float = attr.ib()
    y_m: float = attr.ib()
    t_s: float = attr.ib(default=None)


@attr.s(slots=True)
class EmitterPopulation2D(ABC):
    x_coords_m: np.array = attr.ib(default=None)
    y_coords_m: np.array = attr.ib(default=None)
    routines: list[T.Callable[[float], list[tuple[float, float]]]] = attr.ib(factory=list)

    @abstractmethod
    def initialize(self, *args, **kwargs):
        raise NotImplementedError

    @property
    def n_excitons(self) -> int:
        return self.x_coords_m.shape[0]

    def add_excitations_2d(self, excitations: list[Excitation2D]):
        x_coords_m = []
        y_coords_m = []

        for excitation in excitations:
            x_coords_m.append(excitation.x_m)
            y_coords_m.append(excitation.y_m)

        self.x_coords_m = np.concatenate([
            self.x_coords_m, np.array(x_coords_m)
        ])
        self.y_coords_m = np.concatenate([
            self.y_coords_m, np.array(y_coords_m)
        ])

    def step(self, time_step_s: float) -> list[EmissionEvent2D]:
        emission_events: list[EmissionEvent2D] = []
        for routine in self.routines:
            events = routine(time_step_s)
            if events is not None:
                emission_events.extend(events)
        
        return events


@attr.s(slots=True)
class ExcitonPopulation2D(EmitterPopulation2D):
    radiative_lifetime_s: float = attr.ib(default=None)
    nonradiative_lifetime_s: T.Optional[float] = attr.ib(default=None)

    def initialize(
        self,
        radiative_lifetime_s: float,
        nonradiative_lifetime_s: T.Optional[float]=None,
    ):
        self.x_coords_m = np.array([], dtype=np.float64)
        self.y_coords_m = np.array([], dtype=np.float64)
        self.radiative_lifetime_s = radiative_lifetime_s
        self.nonradiative_lifetime_s = nonradiative_lifetime_s
        self.routines.append(self.linear_decay)

    @property
    def radiative_rate_hz(self) -> float:
        return 1 / self.radiative_lifetime_s
    
    @property
    def nonradiative_rate_hz(self) -> T.Optional[float]:
        if self.nonradiative_lifetime_s is not None:
            return 1 / self.nonradiative_lifetime_s
        return None

    def linear_decay(self, time_step_s: float) -> list[tuple[float, float]]:
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

        probability_decay_was_radiative = 1
        if self.nonradiative_rate_hz is not None:
            probability_decay_was_radiative = self.radiative_rate_hz / (self.radiative_rate_hz + self.nonradiative_rate_hz)
        radiative_decay_rolls = np.random.random(size=n_decayed)
        radiative_decayed_x_m = decayed_x_m[np.where(radiative_decay_rolls <= probability_decay_was_radiative)]
        radiative_decayed_y_m = decayed_y_m[np.where(radiative_decay_rolls <= probability_decay_was_radiative)]

        not_decayed = np.where(random_rolls > probability_of_decay)
        self.x_coords_m = self.x_coords_m[not_decayed]
        self.y_coords_m = self.y_coords_m[not_decayed]
        
        return [
            EmissionEvent2D(x_m=x, y_m=y) for x, y
            in zip(radiative_decayed_x_m, radiative_decayed_y_m)
        ]
