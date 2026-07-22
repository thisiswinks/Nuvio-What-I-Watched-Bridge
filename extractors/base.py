from abc import ABC, abstractmethod
from typing import Any, Union, List, Dict


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self) -> Any:
        """Extract raw data from source (file, directory, or API cache)."""
        pass
