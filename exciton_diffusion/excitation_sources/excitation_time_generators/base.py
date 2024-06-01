__all__ = ["ExcitationTimeGenerator"]

from abc import abstractmethod, ABC


class ExcitationTimeGenerator(ABC):
    @abstractmethod
    def generate(
        self, start_s: float, end_s: float, n_excitations: int
    ) -> tuple[float]:
        """Generate a train of excitation times with this source's characteristics

        Arguments:
            start_s: earliest possible excitation time
            end_s: latest possible excitation time
            n_excitations: number of excitations to return

        Returns:
            A tuple of excitation event times in seconds
        """
        raise NotImplementedError
