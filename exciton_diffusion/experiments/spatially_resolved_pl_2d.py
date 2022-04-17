"""Simulate a time-resolved photoluminescence lifetime experiment.
"""
import attr

from exciton_diffusion.experiments.base import Experiment
from exciton_diffusion.excitation_sources import ExcitationProfile2D
from exciton_diffusion.exciton_populations import (
    EmissionEvent2D,
    EmitterPopulation2D,
)

@attr.s(slots=True)
class SpatiallyResolvedPL2DExperiment(Experiment):
    #: simulation start time in seconds
    start_s: float = attr.ib(default=None)
    #: simulation end time in seconds
    end_s: float = attr.ib(default=None)
    #: simulation time step in seconds
    time_step_s: float = attr.ib(default=None)
    #: excitation source
    excitation_source: ExcitationProfile2D = attr.ib(default=None)
    #: emitter population
    emitter_population: EmitterPopulation2D = attr.ib(default=None)
    #: emission events
    emission_events: list[EmissionEvent2D] = attr.ib(default=None)

    def _configure(
        self,
        *,
        start_s: float,
        end_s: float,
        excitation_source: ExcitationProfile2D,
        emitter_population: EmitterPopulation2D,
        time_step_s: float,
    ):
        self.start_s = start_s
        self.end_s = end_s
        self.time_step_s = time_step_s
        self.excitation_source=excitation_source
        self.emitter_population=emitter_population
        self.emission_events = []

    def _run(self):
        # yield excitations in the generator up to experiment start
        self.excitation_source.yield_excitations_up_to_t(self.start_s - self.time_step_s)

        t_s = self.start_s
        while t_s <= self.end_s:
            self._step(t_s)
            t_s += self.time_step_s

    def _step(self, t_s: float):
        """Step the experiment from the previous time to t_s

        Arguments:
            t_s: end time for this step
        """
        new_excitations = self.excitation_source.yield_excitations_up_to_t(t_s)
        self.emitter_population.add_excitations_2d(new_excitations)
        emission_events = self.emitter_population.step(time_step_s=self.time_step_s)
        for event in emission_events:
            event.t_s = t_s
        self.emission_events.extend(emission_events)

    def _report(self):
        pass
