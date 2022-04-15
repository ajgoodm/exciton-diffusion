"""Utilities to generate a train of gaussian pulses
"""
import math

import attr
import numpy as np

@attr.s(frozen=True, slots=True)
class GaussianPulseTrainGenerator:
    #: The pulsed source repetition rate
    repetition_rate_hz: float = attr.ib()
    #: The pulse width in seconds 
    pulse_full_width_half_max_s: float = attr.ib()

    @property
    def repetition_period_s(self) -> float:
        """Convert the reptition rate to a reptition period
        """
        return 1 / self.repetition_rate_hz

    @property
    def pulse_standard_deviation_s(self) -> float:
        """Convert the full width, half max to a standard deviation
        """
        return self.pulse_full_width_half_max_s / 2.355

    def gaussian_pulse_train_generator(self, start_s: float, end_s: float, n_excitations: int) -> tuple[float]:
        """Generate a train of excitation times bunched into gaussian pulses
        with this source's characteristics (reptition rate and pulse width)

        Arguments:
            start_s: earliest possible excitation time
            end_s: latest possible excitation time
            n_excitations: number of excitations to return
        """
        # To ensure a realistic distribution and deal with edge effects,
        # create twice as many excitations as requested and return only
        # the requested number that are within the simulated time period
        total_excitations_generated = 2 * n_excitations

        duration_s = end_s - start_s
        n_pulses = math.ceil(duration_s / self.repetition_period_s)

        delays_from_pulse_peaks_s = np.random.normal(scale=self.pulse_standard_deviation_s, size=2 * total_excitations_generated)
        excitation_pulse_indices = np.random.randint(low=0, high=n_pulses, size=2 * total_excitations_generated)

        excitation_times = (excitation_pulse_indices * self.repetition_period_s) + delays_from_pulse_peaks_s
        excitation_times = excitation_times[np.where(excitation_times > start_s)]
        excitation_times = excitation_times[np.where(excitation_times < end_s)]
        excitation_times = excitation_times[:n_excitations]
        excitation_times = np.sort(excitation_times)

        return tuple(excitation_times)
