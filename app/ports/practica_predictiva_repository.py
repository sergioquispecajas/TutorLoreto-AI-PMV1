
"""Puerto de salida para guardar prácticas predictivas."""

from typing import Protocol


class PracticaPredictivaRepository(Protocol):
    def registrar(self, datos: dict, resultado: dict) -> int:
        """Guarda una práctica y devuelve su identificador."""
        ...
