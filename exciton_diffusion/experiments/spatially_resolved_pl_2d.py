"""Simulate a time-resolved photoluminescence lifetime experiment.
"""
import attr

from exciton_diffusion.experiments.base import Experiment
from exciton_diffusion.excitation_sources import ExcitationProfile2D

@attr.s(slots=True)
class SpatiallyResolvedPL2DExperiment(Experiment):
    #: simulation start time in seconds
    start_s: float = attr.ib(default=None)
    #: simulation end time in seconds
    end_s: float = attr.ib(default=None)
    #: simulation time step in seconds
    time_step_s: float = attr.ib(default=None)
    #: laser wavelength in nanometers
    excitation_wavelength_nm: float = attr.ib(default=None)
    #: laser power in watts
    laser_power_w: float = attr.ib(default=None)
    #: excitation source
    excitation_source: ExcitationProfile2D = attr.ib(default=None)
    #: exciton population

    def _configure(
        self,
        *,
        start_s: float,
        end_s: float,
        time_step_s: float,
        excitation_wavelength_nm: float,
        laser_power_w: float,
    ):
        self.start_s = start_s
        self.end_s = end_s
        self.time_step_s = time_step_s
        self.excitation_wavelength_nm = excitation_wavelength_nm
        self.laser_power_w = laser_power_w

    def _run(self):
        pass

    def _report(self):
        pass
