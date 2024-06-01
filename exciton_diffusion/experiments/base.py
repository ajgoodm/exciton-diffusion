from abc import abstractmethod, ABC

import attr

from exciton_diffusion.excitation_sources import ExcitationProfile2D
from exciton_diffusion.exciton_populations import EmitterPopulation2D


@attr.define
class Experiment(ABC):
    _is_configured: bool = attr.ib(default=False)
    _is_complete: bool = attr.ib(default=False)

    def _complete(self) -> None:
        self._is_complete = True

    @property
    def is_configured(self) -> bool:
        return self._is_configured

    @property
    def is_complete(self) -> bool:
        return self._is_complete

    def configure(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
        """Configure an experiment"""
        self._configure(**kwargs)
        self._is_configured = True

    def run(self) -> None:
        """Run a configured experiment"""
        if not self.is_configured:
            raise RuntimeError("Cannot run an experiment without configuring it first")
        self._run()
        self._complete()

    def report(self) -> None:
        """Report the results of a completed experiment"""
        if not self.is_complete:
            raise RuntimeError("Cannot report an experiment that hasn't completed")
        self._report()

    @abstractmethod
    def _configure(
        self,
        *,
        start_s: float,
        end_s: float,
        excitation_source: ExcitationProfile2D,
        emitter_population: EmitterPopulation2D,
        time_step_s: float,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def _run(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def _report(self) -> None:
        raise NotImplementedError
