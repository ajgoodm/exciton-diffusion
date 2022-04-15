from abc import abstractmethod, ABC

import attr


@attr.s(slots=True)
class Experiment(ABC):
    _is_configured: bool = attr.ib(default=False)
    _is_complete: bool = attr.ib(default=False)

    def _complete(self):
        self._is_complete = True

    @property
    def is_configured(self) -> bool:
        return self._is_configured

    @property
    def is_complete(self) -> bool:
        return self._is_complete

    def configure(self, *args, **kwargs):
        """Configure an experiment
        """
        self._configure(*args, **kwargs)
        self._is_configured = True


    def run(self):
        """Run a configured experiment
        """
        if not self.is_configured:
            raise RuntimeError("Cannot run an experiment without configuring it first")
        self._run()
        self._complete()

    def report(self):
        """Report the results of a completed experiment
        """
        if not self.is_complete:
            raise RuntimeError("Cannot report an experiment that hasn't completed")
        self._report()

    @abstractmethod
    def _configure(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def _run(self):
        raise NotImplementedError
    
    @abstractmethod
    def _report(self):
        raise NotImplementedError
