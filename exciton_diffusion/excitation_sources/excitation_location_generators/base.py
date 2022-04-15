from abc import abstractmethod, ABC


class ExcitationLocationGenerator(ABC):
    @abstractmethod
    def generate(self, n_excitations: int) -> tuple[tuple[float, tuple]]:
        """Generate a series of excitation locations that match this source's
        characteristics (spatial distribution)

        Arguments:
            n_excitations: number of excitations to return
        
        Returns:
            A tuple of (x, y) location tuples in meters
        """
        raise NotImplementedError
