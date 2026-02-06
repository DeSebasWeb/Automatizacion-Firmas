from abc import ABC, abstractmethod
from typing import Optional


class AzureDIPort(ABC):
    @abstractmethod
    def analyze_e14_document(self, image_bytes: bytes) -> Optional[dict]:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass
