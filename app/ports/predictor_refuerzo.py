
"""Puerto de salida para la predicción de refuerzo académico."""

from typing import Protocol


class PredictorRefuerzo(Protocol):
    def predecir(self, datos: dict) -> dict:
        """Estima la necesidad de refuerzo a partir de datos de práctica."""
        ...
